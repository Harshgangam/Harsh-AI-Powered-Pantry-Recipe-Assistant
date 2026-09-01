import csv
import json
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from data_pipeline.indexer import SQLiteIngredientIndexer
from data_pipeline.normalizer import (
    normalize_ingredient,
    normalize_ner_list,
    parse_list_field,
    validate_and_clean_recipe,
)
from data_pipeline.preprocess import run_pipeline
from data_pipeline.validate import validate_pipeline_outputs


# ---------------------------------------------------------
# Unit Tests: Normalizer & Parser
# ---------------------------------------------------------

def test_parse_list_field():
    # JSON list with double quotes
    res = parse_list_field('["sugar", "milk", "butter"]')
    assert res == ["sugar", "milk", "butter"]

    # Python literal with single quotes
    res = parse_list_field("['flour', 'eggs', 'vanilla']")
    assert res == ["flour", "eggs", "vanilla"]

    # Empty representations
    assert parse_list_field("[]") == []
    assert parse_list_field("") == []
    assert parse_list_field(None) is None

    # Invalid syntax
    assert parse_list_field("not a list") is None
    assert parse_list_field("{'a': 1}") is None


def test_normalize_ingredient():
    assert normalize_ingredient("  Brown Sugar  ") == "brown sugar"
    assert normalize_ingredient("CHICKEN BREASTS") == "chicken breasts"
    assert normalize_ingredient('"fresh garlic,"') == "fresh garlic"
    assert normalize_ingredient("olive   oil") == "olive oil"
    assert normalize_ingredient("") == ""


def test_normalize_ner_list():
    # Normal and deduplication
    ner_raw = '["Garlic", "garlic", "ONION", "olive oil"]'
    cleaned, err = normalize_ner_list(ner_raw)
    assert err is None
    assert cleaned == ["garlic", "onion", "olive oil"]

    # Empty NER
    cleaned, err = normalize_ner_list("[]")
    assert cleaned is None
    assert "Empty" in err

    # Malformed NER
    cleaned, err = normalize_ner_list("invalid [ [ json")
    assert cleaned is None
    assert "Failed" in err


def test_validate_and_clean_recipe():
    # Valid recipe
    cleaned, err = validate_and_clean_recipe(
        raw_id="101",
        title="Spaghetti Aglio e Olio",
        ingredients='["spaghetti", "garlic", "olive oil", "red pepper flakes"]',
        directions='["Boil pasta", "Sauté garlic in olive oil", "Toss together"]',
        link="https://example.com/spaghetti",
        source="Gathered",
        ner='["spaghetti", "garlic", "olive oil", "red pepper flakes"]',
    )
    assert err is None
    assert cleaned["recipe_id"] == 101
    assert cleaned["title"] == "Spaghetti Aglio e Olio"
    assert cleaned["ner_count"] == 4
    assert "garlic" in cleaned["ner"]

    # Invalid ID
    _, err = validate_and_clean_recipe("bad_id", "Title", "['a']", "['b']", "", "Gathered", "['a']")
    assert "Invalid recipe ID" in err

    # Empty Title
    _, err = validate_and_clean_recipe("1", "   ", "['a']", "['b']", "", "Gathered", "['a']")
    assert "Empty title" in err

    # Empty Directions
    _, err = validate_and_clean_recipe("1", "Title", "['a']", "[]", "", "Gathered", "['a']")
    assert "directions" in err


# ---------------------------------------------------------
# Integration Tests: SQLite Inverted Index
# ---------------------------------------------------------

def test_sqlite_indexer_lifecycle(tmp_path):
    db_path = tmp_path / "test_index.sqlite"
    indexer = SQLiteIngredientIndexer(db_path)
    indexer.init_schema(drop_existing=True)

    records = [
        {"recipe_id": 1, "ner": ["garlic", "tomato", "basil"], "ner_count": 3},
        {"recipe_id": 2, "ner": ["chicken", "garlic", "butter"], "ner_count": 3},
        {"recipe_id": 3, "ner": ["tomato", "onion"], "ner_count": 2},
    ]

    indexer.index_chunk(records)
    indexer.finalize_counts()

    stats = indexer.get_stats()
    assert stats["indexed_recipes"] == 3
    assert stats["unique_ingredients"] == 6  # garlic, tomato, basil, chicken, butter, onion
    assert stats["ingredient_recipe_links"] == 8

    # Query single ingredient
    garlic_recipes = indexer.find_recipes_by_ingredient("garlic")
    assert set(garlic_recipes) == {1, 2}

    # Query multi-ingredient pantry candidate generation
    # Pantry has ["garlic", "tomato", "onion"]
    # Recipe 1 has garlic + tomato (2 matches out of 3)
    # Recipe 2 has garlic (1 match out of 3)
    # Recipe 3 has tomato + onion (2 matches out of 2) -> 100% match!
    pantry_matches = indexer.find_recipes_by_pantry(["garlic", "tomato", "onion"], min_match=1)
    matched_ids = [m[0] for m in pantry_matches]
    assert set(matched_ids) == {1, 2, 3}

    # Check top candidate: recipe 3 matches 2/2 (100%), recipe 1 matches 2/3 (66.7%)
    top_recipe = pantry_matches[0]
    assert top_recipe[1] == 2  # 2 matched ingredients

    indexer.close()


# ---------------------------------------------------------
# End-to-End Small Pipeline Test
# ---------------------------------------------------------

def test_end_to_end_pipeline(tmp_path):
    # 1. Create a synthetic test CSV with known rows (valid + malformed)
    csv_file = tmp_path / "test_recipes.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["", "title", "ingredients", "directions", "link", "source", "NER"])
        # Valid row 1
        writer.writerow([
            "0", "Garlic Butter Pasta",
            '["pasta", "garlic", "butter"]',
            '["Boil pasta.", "Toss with garlic and butter."]',
            "http://example.com/1", "Gathered",
            '["pasta", "garlic", "butter"]'
        ])
        # Valid row 2
        writer.writerow([
            "1", "Tomato Basil Salad",
            '["tomato", "basil", "olive oil"]',
            '["Chop tomatoes.", "Add basil and olive oil."]',
            "http://example.com/2", "Recipes1M",
            '["tomato", "basil", "olive oil"]'
        ])
        # Malformed row: empty title
        writer.writerow([
            "2", "",
            '["eggs", "milk"]',
            '["Whisk and fry."]',
            "http://example.com/3", "Gathered",
            '["eggs", "milk"]'
        ])
        # Malformed row: empty NER
        writer.writerow([
            "3", "Ghost Recipe",
            '["mystery spice"]',
            '["Cast spell."]',
            "http://example.com/4", "Gathered",
            '[]'
        ])

    parquet_out = tmp_path / "recipes.parquet"
    sqlite_out = tmp_path / "ingredient_index.sqlite"
    stats_out = tmp_path / "stats.json"
    malformed_log = tmp_path / "malformed.log"

    # 2. Run the chunked pipeline
    stats = run_pipeline(
        raw_csv_path=csv_file,
        parquet_out_path=parquet_out,
        sqlite_out_path=sqlite_out,
        stats_out_path=stats_out,
        malformed_log_path=malformed_log,
        chunk_size=2,  # test chunking mechanism
    )

    # 3. Assert counts
    assert stats["input"]["total_raw_rows_read"] == 4
    assert stats["records"]["valid_recipes"] == 2
    assert stats["records"]["malformed_recipes"] == 2

    # 4. Run validation suite
    validation_success = validate_pipeline_outputs(parquet_out, sqlite_out, stats_out)
    assert validation_success is True

    # 5. Check Parquet content
    df = pd.read_parquet(parquet_out)
    assert len(df) == 2
    assert list(df["recipe_id"]) == [0, 1]
    assert list(df["title"]) == ["Garlic Butter Pasta", "Tomato Basil Salad"]

    # 6. Check SQLite contents
    conn = sqlite3.connect(str(sqlite_out))
    cur = conn.cursor()
    cur.execute("SELECT name FROM ingredients ORDER BY name;")
    ings = [row[0] for row in cur.fetchall()]
    assert ings == ["basil", "butter", "garlic", "olive oil", "pasta", "tomato"]
    conn.close()
