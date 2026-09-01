import argparse
import csv
import sys
from pathlib import Path
from data_pipeline.config import RAW_DATASET_PATH
from data_pipeline.normalizer import validate_and_clean_recipe


def inspect_dataset(csv_path: Path, sample_limit: int = 50000):
    """
    Safely inspects the raw dataset without loading it entirely into memory.
    Reads row-by-row with csv.reader, reporting schema, samples, and statistics.
    """
    if not csv_path.exists():
        print(f"Error: Dataset file not found at: {csv_path}", file=sys.stderr)
        return False

    file_size_gb = csv_path.stat().st_size / (1024 ** 3)
    print("=" * 60)
    print("RECIPENLG DATASET INSPECTION")
    print("=" * 60)
    print(f"File Path: {csv_path}")
    print(f"File Size: {file_size_gb:.2f} GB ({csv_path.stat().st_size:,} bytes)")
    print()

    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print("Error: Empty file", file=sys.stderr)
            return False

        print(f"Header ({len(header)} columns): {header}")
        print("-" * 60)

        total_sampled = 0
        valid_count = 0
        malformed_count = 0
        malformed_reasons = {}
        sources = {}
        ner_lengths = []

        print(f"Sampling first {sample_limit:,} rows...")
        for i, row in enumerate(reader):
            if i >= sample_limit:
                break
            total_sampled += 1

            if len(row) != 7:
                malformed_count += 1
                reason = f"Column count mismatch ({len(row)} cols)"
                malformed_reasons[reason] = malformed_reasons.get(reason, 0) + 1
                continue

            raw_id, title, ingredients, directions, link, source, ner = row
            sources[source] = sources.get(source, 0) + 1

            cleaned, err = validate_and_clean_recipe(
                raw_id, title, ingredients, directions, link, source, ner
            )

            if err:
                malformed_count += 1
                malformed_reasons[err] = malformed_reasons.get(err, 0) + 1
            else:
                valid_count += 1
                ner_lengths.append(cleaned["ner_count"])

            if i < 3:
                print(f"\n[Sample Row {i}]")
                print(f"  ID: {raw_id}")
                print(f"  Title: {title}")
                print(f"  Source: {source}")
                print(f"  Ingredients (raw snippet): {ingredients[:100]}...")
                print(f"  Directions (raw snippet): {directions[:100]}...")
                print(f"  NER (raw): {ner}")
                if cleaned:
                    print(f"  Cleaned NER ({cleaned['ner_count']} items): {cleaned['ner']}")

    print("\n" + "=" * 60)
    print("SAMPLE ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Rows Sampled: {total_sampled:,}")
    print(f"Valid Rows: {valid_count:,} ({valid_count/total_sampled*100:.2f}%)")
    print(f"Malformed Rows: {malformed_count:,} ({malformed_count/total_sampled*100:.2f}%)")
    print(f"Sources Distribution: {sources}")
    if ner_lengths:
        print(f"Avg NER items/recipe: {sum(ner_lengths)/len(ner_lengths):.2f}")
        print(f"Min NER items: {min(ner_lengths)}")
        print(f"Max NER items: {max(ner_lengths)}")
    if malformed_reasons:
        print("\nMalformed Reasons:")
        for r, count in malformed_reasons.items():
            print(f"  - {r}: {count}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect RecipeNLG CSV dataset safely.")
    parser.add_argument("--path", type=Path, default=RAW_DATASET_PATH, help="Path to raw CSV dataset")
    parser.add_argument("--sample", type=int, default=50000, help="Number of rows to sample")
    args = parser.parse_args()
    inspect_dataset(args.path, args.sample)
