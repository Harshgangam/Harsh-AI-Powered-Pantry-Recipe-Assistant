import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from data_pipeline.config import (
    CHUNK_SIZE,
    LOGS_DIR,
    MALFORMED_LOG_PATH,
    PARQUET_PATH,
    PROCESSED_DATA_DIR,
    RAW_DATASET_PATH,
    SQLITE_INDEX_PATH,
    STATS_PATH,
)
from data_pipeline.indexer import SQLiteIngredientIndexer
from data_pipeline.normalizer import validate_and_clean_recipe

# Explicit PyArrow schema for consistent Parquet storage
PARQUET_SCHEMA = pa.schema([
    pa.field("recipe_id", pa.int64()),
    pa.field("title", pa.string()),
    pa.field("ingredients", pa.list_(pa.string())),
    pa.field("directions", pa.list_(pa.string())),
    pa.field("link", pa.string()),
    pa.field("source", pa.string()),
    pa.field("ner", pa.list_(pa.string())),
    pa.field("ner_count", pa.int32()),
])


def setup_logger(log_file: Path) -> logging.Logger:
    """Configures logging for malformed rows and pipeline events."""
    logger = logging.getLogger("recipe_pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_file.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(str(log_file), mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def format_size(bytes_size: int) -> str:
    """Formats bytes into human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def run_pipeline(
    raw_csv_path: Path = RAW_DATASET_PATH,
    parquet_out_path: Path = PARQUET_PATH,
    sqlite_out_path: Path = SQLITE_INDEX_PATH,
    stats_out_path: Path = STATS_PATH,
    malformed_log_path: Path = MALFORMED_LOG_PATH,
    chunk_size: int = CHUNK_SIZE,
    max_rows: Optional[int] = None,
) -> dict:
    """
    Runs the chunked data processing pipeline:
    1. Reads raw CSV in streaming chunks without loading entire file into RAM.
    2. Validates rows, parses NER and lists, normalizes entities.
    3. Writes valid records into Parquet incrementally.
    4. Populates SQLite inverted index incrementally.
    5. Measures and logs all file sizes, counts, and performance metrics.
    """
    start_time = time.time()
    raw_csv_path = Path(raw_csv_path)

    if not raw_csv_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at: {raw_csv_path}")

    # Prepare output directories
    parquet_out_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_out_path.parent.mkdir(parents=True, exist_ok=True)
    malformed_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Clean existing destination files to ensure fresh, clean runs
    if parquet_out_path.exists():
        parquet_out_path.unlink()
    if sqlite_out_path.exists():
        sqlite_out_path.unlink()
    wal_file = Path(str(sqlite_out_path) + "-wal")
    shm_file = Path(str(sqlite_out_path) + "-shm")
    if wal_file.exists():
        wal_file.unlink()
    if shm_file.exists():
        shm_file.unlink()

    logger = setup_logger(malformed_log_path)
    logger.info("Pipeline started. Source: %s", raw_csv_path)

    print("=" * 70)
    print("AI-POWERED PANTRY RECIPE ASSISTANT — DATA PIPELINE")
    print("=" * 70)
    print(f"Raw dataset:     {raw_csv_path}")
    print(f"Parquet output:  {parquet_out_path}")
    print(f"SQLite index:    {sqlite_out_path}")
    print(f"Chunk size:      {chunk_size:,} rows")
    if max_rows:
        print(f"Row limit:       {max_rows:,} rows")
    print("-" * 70)

    # Initialize SQLite Indexer
    indexer = SQLiteIngredientIndexer(sqlite_out_path)
    indexer.init_schema(drop_existing=True)

    # Initialize Parquet Writer
    parquet_writer = pq.ParquetWriter(
        str(parquet_out_path),
        PARQUET_SCHEMA,
        compression="snappy",
    )

    # Pipeline tracking metrics
    total_raw_rows = 0
    total_valid_rows = 0
    total_malformed_rows = 0
    malformed_reasons: Dict[str, int] = {}
    sources_distribution: Dict[str, int] = {}
    ner_lengths: List[int] = []
    seen_recipe_ids = set()
    duplicate_ids_count = 0

    chunk_idx = 0
    stop_processing = False

    try:
        # Stream CSV chunks with pandas
        csv_iterator = pd.read_csv(
            raw_csv_path,
            chunksize=chunk_size,
            low_memory=False,
            encoding="utf-8",
            dtype=str,  # read as string initially to prevent parse corruption
        )

        for chunk_df in csv_iterator:
            chunk_idx += 1
            chunk_valid_records: List[dict] = []
            chunk_start_time = time.time()

            # Iterate over rows in chunk using itertuples (fastest row iteration)
            for row in chunk_df.itertuples(index=False):
                total_raw_rows += 1

                if max_rows and total_raw_rows > max_rows:
                    stop_processing = True
                    break

                # Expect 7 columns: ['', 'title', 'ingredients', 'directions', 'link', 'source', 'NER']
                if len(row) < 7:
                    total_malformed_rows += 1
                    reason = f"Insufficient columns ({len(row)})"
                    malformed_reasons[reason] = malformed_reasons.get(reason, 0) + 1
                    logger.warning("Row %d malformed: %s", total_raw_rows, reason)
                    continue

                raw_id = row[0]
                title = row[1]
                ingredients = row[2]
                directions = row[3]
                link = row[4]
                source = row[5]
                ner = row[6]

                cleaned, err = validate_and_clean_recipe(
                    raw_id, title, ingredients, directions, link, source, ner
                )

                if err:
                    total_malformed_rows += 1
                    malformed_reasons[err] = malformed_reasons.get(err, 0) + 1
                    logger.warning("Row %d (ID %s) malformed: %s", total_raw_rows, raw_id, err)
                    continue

                # Check for duplicate recipe ID
                rec_id = cleaned["recipe_id"]
                if rec_id in seen_recipe_ids:
                    duplicate_ids_count += 1
                    logger.warning("Duplicate recipe ID %d skipped", rec_id)
                    continue
                seen_recipe_ids.add(rec_id)

                sources_distribution[cleaned["source"]] = (
                    sources_distribution.get(cleaned["source"], 0) + 1
                )
                chunk_valid_records.append(cleaned)
                total_valid_rows += 1

            # Process valid chunk batch
            if chunk_valid_records:
                # 1. Write chunk to Parquet
                pyarrow_table = pa.Table.from_pydict(
                    {
                        "recipe_id": [r["recipe_id"] for r in chunk_valid_records],
                        "title": [r["title"] for r in chunk_valid_records],
                        "ingredients": [r["ingredients"] for r in chunk_valid_records],
                        "directions": [r["directions"] for r in chunk_valid_records],
                        "link": [r["link"] for r in chunk_valid_records],
                        "source": [r["source"] for r in chunk_valid_records],
                        "ner": [r["ner"] for r in chunk_valid_records],
                        "ner_count": [r["ner_count"] for r in chunk_valid_records],
                    },
                    schema=PARQUET_SCHEMA,
                )
                parquet_writer.write_table(pyarrow_table)

                # 2. Incrementally index into SQLite
                indexer.index_chunk(chunk_valid_records)

            chunk_elapsed = time.time() - chunk_start_time
            rate = len(chunk_valid_records) / chunk_elapsed if chunk_elapsed > 0 else 0
            print(
                f"[Chunk {chunk_idx:3d}] Processed {total_raw_rows:9,d} rows "
                f"| Valid: {total_valid_rows:9,d} | Malformed: {total_malformed_rows:4,d} "
                f"| Rate: {rate:6.0f} rows/s"
            )

            if stop_processing:
                break

    finally:
        parquet_writer.close()

    print("-" * 70)
    print("Finalizing SQLite inverted index counts...")
    indexer.finalize_counts()
    sqlite_stats = indexer.get_stats()
    indexer.close()

    total_time = time.time() - start_time

    # Output file sizes
    raw_size_bytes = raw_csv_path.stat().st_size
    parquet_size_bytes = parquet_out_path.stat().st_size if parquet_out_path.exists() else 0
    sqlite_size_bytes = sqlite_out_path.stat().st_size if sqlite_out_path.exists() else 0

    stats = {
        "timestamp": datetime.now().isoformat(),
        "execution_time_seconds": round(total_time, 2),
        "chunk_size": chunk_size,
        "input": {
            "path": str(raw_csv_path),
            "size_bytes": raw_size_bytes,
            "size_formatted": format_size(raw_size_bytes),
            "total_raw_rows_read": total_raw_rows,
        },
        "output": {
            "parquet_path": str(parquet_out_path),
            "parquet_size_bytes": parquet_size_bytes,
            "parquet_size_formatted": format_size(parquet_size_bytes),
            "sqlite_path": str(sqlite_out_path),
            "sqlite_size_bytes": sqlite_size_bytes,
            "sqlite_size_formatted": format_size(sqlite_size_bytes),
            "malformed_log_path": str(malformed_log_path),
        },
        "records": {
            "valid_recipes": total_valid_rows,
            "malformed_recipes": total_malformed_rows,
            "duplicate_ids": duplicate_ids_count,
            "malformed_breakdown": malformed_reasons,
            "sources_distribution": sources_distribution,
        },
        "index": {
            "indexed_recipes": sqlite_stats["indexed_recipes"],
            "unique_ingredients": sqlite_stats["unique_ingredients"],
            "ingredient_recipe_links": sqlite_stats["ingredient_recipe_links"],
        },
    }

    # Save stats JSON
    stats_out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    logger.info("Pipeline completed successfully in %.2f seconds.", total_time)

    print("=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)
    print(f"Total rows read:       {total_raw_rows:,}")
    print(f"Valid recipes stored:  {total_valid_rows:,}")
    print(f"Malformed records:     {total_malformed_rows:,}")
    print(f"Unique ingredients:    {sqlite_stats['unique_ingredients']:,}")
    print(f"Ingredient links:      {sqlite_stats['ingredient_recipe_links']:,}")
    print(f"Parquet file size:     {format_size(parquet_size_bytes)}")
    print(f"SQLite index size:     {format_size(sqlite_size_bytes)}")
    print(f"Total time:            {total_time:.2f}s ({total_time/60:.2f} min)")
    print(f"Stats file saved to:   {stats_out_path}")
    print("=" * 70)

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RecipeNLG chunked preprocessing pipeline.")
    parser.add_argument("--csv", type=Path, default=RAW_DATASET_PATH, help="Path to raw CSV dataset")
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum rows to process (for testing)")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="Rows per chunk")
    args = parser.parse_args()

    run_pipeline(raw_csv_path=args.csv, chunk_size=args.chunk_size, max_rows=args.limit)
