import argparse
import logging
import os
from pathlib import Path
import sqlite3
import time
from typing import Counter, Optional

import pyarrow.parquet as pq

from backend.app.config import settings
from data_pipeline.enrichment.cuisine_classifier import classify_cuisine
from data_pipeline.enrichment.dietary_classifier import classify_dietary_compatibility
from data_pipeline.enrichment.time_extractor import extract_cooking_time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def init_metadata_db(db_path: Path, reset: bool = False) -> sqlite3.Connection:
    """Initialize SQLite database for derived recipe metadata."""
    if reset and db_path.exists():
        logger.info(f"Removing existing metadata database at {db_path}...")
        db_path.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS recipe_metadata (
            recipe_id INTEGER PRIMARY KEY,
            cuisine TEXT,
            cuisine_confidence TEXT,
            cuisine_method TEXT,
            dietary_compatibility TEXT,
            dietary_confidence TEXT,
            dietary_method TEXT,
            estimated_time_minutes INTEGER,
            time_confidence TEXT,
            time_method TEXT
        );
        """
    )
    conn.commit()
    return conn


def create_metadata_indexes(conn: sqlite3.Connection):
    """Create indexes for efficient filtering during recommendation."""
    logger.info("Creating indexes on recipe_metadata...")
    t0 = time.time()
    conn.execute("CREATE INDEX IF NOT EXISTS idx_meta_cuisine ON recipe_metadata(cuisine);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_meta_dietary ON recipe_metadata(dietary_compatibility);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_meta_time ON recipe_metadata(estimated_time_minutes);")
    conn.commit()
    logger.info(f"Indexes created in {time.time() - t0:.2f}s")


def run_metadata_enrichment(
    parquet_path: Path = settings.PARQUET_PATH,
    db_path: Path = settings.METADATA_DB_PATH,
    batch_size: int = 50000,
    limit: Optional[int] = None,
    reset: bool = True,
):
    """
    Stream recipes from Parquet in memory-efficient chunks, derive metadata,
    and insert into SQLite metadata store.
    """
    logger.info("=" * 60)
    logger.info("Starting Recipe Metadata Enrichment Pipeline (Milestone 3)")
    logger.info(f"Input Parquet: {parquet_path}")
    logger.info(f"Output SQLite: {db_path}")
    logger.info(f"Batch Size: {batch_size:,} | Limit: {limit or 'ALL'}")
    logger.info("=" * 60)

    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    conn = init_metadata_db(db_path, reset=reset)
    pf = pq.ParquetFile(str(parquet_path))
    total_parquet_rows = pf.metadata.num_rows
    target_rows = min(total_parquet_rows, limit) if limit else total_parquet_rows

    total_processed = 0
    cuisine_counts: Counter[str] = Counter()
    dietary_counts: Counter[str] = Counter()
    time_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()

    start_time = time.time()

    insert_sql = """
        INSERT OR REPLACE INTO recipe_metadata (
            recipe_id, cuisine, cuisine_confidence, cuisine_method,
            dietary_compatibility, dietary_confidence, dietary_method,
            estimated_time_minutes, time_confidence, time_method
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    for batch in pf.iter_batches(
        batch_size=batch_size,
        columns=["recipe_id", "title", "directions", "ner"],
    ):
        batch_t0 = time.time()
        r_ids = batch.column("recipe_id").to_pylist()
        titles = batch.column("title").to_pylist()
        dirs = batch.column("directions").to_pylist()
        ners = batch.column("ner").to_pylist()
        
        batch_len = len(r_ids)
        if limit and total_processed + batch_len > limit:
            slice_len = limit - total_processed
            r_ids = r_ids[:slice_len]
            titles = titles[:slice_len]
            dirs = dirs[:slice_len]
            ners = ners[:slice_len]
            batch_len = slice_len

        records_to_insert = []
        for r_id, title, directions, ner in zip(r_ids, titles, dirs, ners):
            r_id = int(r_id)
            title = str(title) if title is not None else ""
            directions = list(directions) if directions is not None else []
            ner = list(ner) if ner is not None else []

            # 1. Derive Cuisine
            cuisine, c_conf, c_method = classify_cuisine(title, ner)
            cuisine_counts[cuisine or "unknown"] += 1
            if c_conf:
                confidence_counts[f"cuisine_{c_conf}"] += 1

            # 2. Derive Dietary Compatibility
            diet, d_conf, d_method = classify_dietary_compatibility(ner)
            dietary_counts[diet] += 1
            confidence_counts[f"dietary_{d_conf}"] += 1

            # 3. Derive Cooking Time
            cook_time, t_conf, t_method = extract_cooking_time(directions)
            if cook_time is not None:
                time_counts["with_time"] += 1
            else:
                time_counts["unknown_time"] += 1
            if t_conf:
                confidence_counts[f"time_{t_conf}"] += 1

            records_to_insert.append((
                r_id,
                cuisine,
                c_conf,
                c_method,
                diet,
                d_conf,
                d_method,
                cook_time,
                t_conf,
                t_method,
            ))

        with conn:
            conn.executemany(insert_sql, records_to_insert)

        total_processed += len(records_to_insert)
        batch_duration = time.time() - batch_t0
        progress_pct = (total_processed / target_rows) * 100.0
        elapsed = time.time() - start_time
        rate = total_processed / elapsed if elapsed > 0 else 0

        logger.info(
            f"Processed {total_processed:,}/{target_rows:,} ({progress_pct:.1f}%) "
            f"in {batch_duration:.2f}s | Speed: {rate:,.0f} rows/s"
        )

        if limit and total_processed >= limit:
            break

    # Build indexes after bulk insert for maximum speed
    create_metadata_indexes(conn)
    conn.close()

    total_duration = time.time() - start_time
    file_size_mb = db_path.stat().st_size / (1024 * 1024)

    logger.info("=" * 60)
    logger.info("METADATA ENRICHMENT COMPLETED")
    logger.info(f"Total Recipes Processed: {total_processed:,}")
    logger.info(f"Database File Size: {file_size_mb:.2f} MB")
    logger.info(f"Total Time: {total_duration:.2f}s ({total_processed / total_duration:,.0f} rows/s)")
    logger.info("-" * 60)
    logger.info("Cuisine Distribution:")
    for c, cnt in cuisine_counts.most_common():
        pct = (cnt / total_processed) * 100.0
        logger.info(f"  {c:<16}: {cnt:>10,} ({pct:5.2f}%)")
    logger.info("-" * 60)
    logger.info("Dietary Compatibility Distribution:")
    for d, cnt in dietary_counts.most_common():
        pct = (cnt / total_processed) * 100.0
        logger.info(f"  {d:<24}: {cnt:>10,} ({pct:5.2f}%)")
    logger.info("-" * 60)
    logger.info("Cooking Time Distribution:")
    for t, cnt in time_counts.most_common():
        pct = (cnt / total_processed) * 100.0
        logger.info(f"  {t:<16}: {cnt:>10,} ({pct:5.2f}%)")
    logger.info("-" * 60)
    logger.info("Confidence Metrics:")
    for conf, cnt in sorted(confidence_counts.items()):
        logger.info(f"  {conf:<20}: {cnt:>10,}")
    logger.info("=" * 60)

    return {
        "total_processed": total_processed,
        "database_size_mb": file_size_mb,
        "duration_seconds": total_duration,
        "cuisine_counts": dict(cuisine_counts),
        "dietary_counts": dict(dietary_counts),
        "time_counts": dict(time_counts),
        "confidence_counts": dict(confidence_counts),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate derived recipe metadata.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of recipes to process.")
    parser.add_argument("--batch-size", type=int, default=50000, help="Batch size for processing.")
    parser.add_argument("--no-reset", action="store_true", help="Do not overwrite existing DB.")
    args = parser.parse_args()

    run_metadata_enrichment(
        batch_size=args.batch_size,
        limit=args.limit,
        reset=not args.no_reset,
    )
