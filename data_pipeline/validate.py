import argparse
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from data_pipeline.config import PARQUET_PATH, SQLITE_INDEX_PATH, STATS_PATH
from data_pipeline.indexer import SQLiteIngredientIndexer


def validate_pipeline_outputs(
    parquet_path: Path = PARQUET_PATH,
    sqlite_path: Path = SQLITE_INDEX_PATH,
    stats_path: Path = STATS_PATH,
) -> bool:
    """
    Validates the artifacts produced by the preprocessing pipeline.
    Checks Parquet integrity, SQLite schema and queries, and cross-consistency.
    """
    print("=" * 65)
    print("PIPELINE OUTPUT VALIDATION")
    print("=" * 65)

    all_passed = True

    # 1. Check file existence
    print("[Check 1] Output file existence...")
    for label, p in [("Parquet", parquet_path), ("SQLite", sqlite_path), ("Stats JSON", stats_path)]:
        if p.exists():
            size_mb = p.stat().st_size / (1024 * 1024)
            print(f"  [OK] {label} exists: {p} ({size_mb:.2f} MB)")
        else:
            print(f"  [FAIL] {label} MISSING: {p}", file=sys.stderr)
            all_passed = False

    if not all_passed:
        return False

    # 2. Check Stats JSON
    print("\n[Check 2] Reading stats JSON...")
    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)
    print(f"  [OK] Total raw rows read:    {stats['input']['total_raw_rows_read']:,}")
    print(f"  [OK] Valid recipes:          {stats['records']['valid_recipes']:,}")
    print(f"  [OK] Malformed recipes:      {stats['records']['malformed_recipes']:,}")
    print(f"  [OK] Duplicate IDs:          {stats['records']['duplicate_ids']:,}")
    print(f"  [OK] Unique ingredients:     {stats['index']['unique_ingredients']:,}")
    print(f"  [OK] Ingredient links:       {stats['index']['ingredient_recipe_links']:,}")

    # 3. Check Parquet readability and schema
    print("\n[Check 3] Validating Parquet file...")
    try:
        parquet_file = pq.ParquetFile(str(parquet_path))
        parquet_rows = parquet_file.metadata.num_rows
        parquet_cols = parquet_file.schema_arrow.names
        print(f"  [OK] Parquet rows:           {parquet_rows:,}")
        print(f"  [OK] Parquet columns ({len(parquet_cols)}): {parquet_cols}")

        expected_cols = ["recipe_id", "title", "ingredients", "directions", "link", "source", "ner", "ner_count"]
        if set(expected_cols) != set(parquet_cols):
            print(f"  [FAIL] Unexpected columns: {parquet_cols}", file=sys.stderr)
            all_passed = False
        else:
            print("  [OK] Column schema matches specification")

        # Read small sample
        sample_df = pd.read_parquet(parquet_path, engine="pyarrow").head(5)
        print(f"  [OK] Sample read successful ({len(sample_df)} rows):")
        for idx, row in sample_df.iterrows():
            print(f"    - [{row['recipe_id']}] \"{row['title']}\" (NER: {row['ner_count']} items, e.g. {row['ner'][:3]})")

    except Exception as e:
        print(f"  [FAIL] Parquet read error: {e}", file=sys.stderr)
        all_passed = False

    # 4. Check SQLite Index Integrity
    print("\n[Check 4] Validating SQLite ingredient index...")
    try:
        indexer = SQLiteIngredientIndexer(sqlite_path)
        sqlite_stats = indexer.get_stats()
        print(f"  [OK] SQLite recipes metadata count: {sqlite_stats['indexed_recipes']:,}")
        print(f"  [OK] SQLite unique ingredients:    {sqlite_stats['unique_ingredients']:,}")
        print(f"  [OK] SQLite recipe-ingredient links: {sqlite_stats['ingredient_recipe_links']:,}")

        # Consistency check: Parquet row count vs SQLite indexed recipes
        if parquet_rows != sqlite_stats["indexed_recipes"]:
            print(
                f"  [FAIL] Count mismatch! Parquet: {parquet_rows}, SQLite: {sqlite_stats['indexed_recipes']}",
                file=sys.stderr,
            )
            all_passed = False
        else:
            print("  [OK] Parquet row count matches SQLite indexed recipe count exactly!")

        # 5. Check Inverted Index Queries
        print("\n[Check 5] Testing inverted index queries...")
        # Query 1: Single ingredient
        test_ingredient = "garlic"
        garlic_recipes = indexer.find_recipes_by_ingredient(test_ingredient, limit=5)
        print(f"  [OK] Query single ingredient ('{test_ingredient}'): found {len(garlic_recipes)} sample recipe IDs: {garlic_recipes}")

        # Query 2: Multiple pantry ingredients candidate retrieval
        test_pantry = ["chicken breasts", "garlic", "sour cream", "butter"]
        pantry_matches = indexer.find_recipes_by_pantry(test_pantry, min_match=2, limit=5)
        print(f"  [OK] Query pantry ingredients ({test_pantry}):")
        for r_id, matched, total in pantry_matches:
            print(f"    - Recipe ID {r_id}: matches {matched}/{total} ingredients ({matched/total*100:.1f}%)")

        indexer.close()

    except Exception as e:
        print(f"  [FAIL] SQLite validation error: {e}", file=sys.stderr)
        all_passed = False

    # 6. ID Uniqueness Check in SQLite
    print("\n[Check 6] Verifying recipe ID uniqueness in SQLite...")
    try:
        conn = sqlite3.connect(str(sqlite_path))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(recipe_id), COUNT(DISTINCT recipe_id) FROM recipes_metadata;")
        total_ids, distinct_ids = cur.fetchone()
        if total_ids == distinct_ids:
            print(f"  [OK] All {distinct_ids:,} recipe IDs are strictly unique!")
        else:
            print(f"  [FAIL] Duplicate recipe IDs detected: {total_ids} total vs {distinct_ids} distinct!", file=sys.stderr)
            all_passed = False
        conn.close()
    except Exception as e:
        print(f"  [FAIL] Recipe ID uniqueness check failed: {e}", file=sys.stderr)
        all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print("ALL VALIDATION CHECKS PASSED SUCCESSFULLY [OK]")
    else:
        print("SOME VALIDATION CHECKS FAILED [FAIL]", file=sys.stderr)
    print("=" * 65)

    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate pipeline output artifacts.")
    parser.add_argument("--parquet", type=Path, default=PARQUET_PATH)
    parser.add_argument("--sqlite", type=Path, default=SQLITE_INDEX_PATH)
    parser.add_argument("--stats", type=Path, default=STATS_PATH)
    args = parser.parse_args()

    success = validate_pipeline_outputs(args.parquet, args.sqlite, args.stats)
    sys.exit(0 if success else 1)
