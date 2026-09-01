import tempfile
from pathlib import Path
import sqlite3
from typing import Any, Dict, List
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from backend.app.models.recommendation import PantryRequest, RecommendationResponse
from backend.app.recommendation.engine import RecommendationEngine
from backend.app.recommendation.personalizer import (
    calculate_cuisine_bonus,
    calculate_time_adjustment,
    evaluate_personalization,
    is_dietary_compatible,
)


@pytest.fixture
def synthetic_personalization_env():
    """
    Creates a temporary SQLite inverted index, Parquet file, and metadata SQLite
    with carefully controlled recipes for testing personalization scenarios A through M.
    """
    temp_dir = tempfile.TemporaryDirectory()
    dir_path = Path(temp_dir.name)

    sqlite_path = dir_path / "test_index.sqlite"
    parquet_path = dir_path / "test_recipes.parquet"
    metadata_path = dir_path / "test_metadata.sqlite"

    # 1. Initialize Inverted Index
    conn = sqlite3.connect(str(sqlite_path))
    conn.execute("""
        CREATE TABLE ingredients (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE recipes_metadata (
            recipe_id INTEGER PRIMARY KEY,
            ner_count INTEGER NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE recipe_ingredients (
            ingredient_id INTEGER NOT NULL,
            recipe_id INTEGER NOT NULL,
            PRIMARY KEY (ingredient_id, recipe_id)
        );
    """)

    # 2. Initialize Metadata SQLite
    meta_conn = sqlite3.connect(str(metadata_path))
    meta_conn.execute("""
        CREATE TABLE recipe_metadata (
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
    """)

    # Recipes for testing:
    # ID 1: "Spaghetti Marinara" - Italian, Vegan (pasta, tomato, garlic, basil, olive oil) - 20 mins
    # ID 2: "Chicken Parmesan" - Italian, Non-Vegetarian (chicken, pasta, tomato, cheese) - 45 mins
    # ID 3: "Paneer Butter Masala" - Indian, Vegetarian (paneer, tomato, butter, spices) - 30 mins
    # ID 4: "Chicken Curry" - Indian, Non-Vegetarian (chicken, tomato, onion, curry powder) - 35 mins
    # ID 5: "Simple Garlic Pasta" - Unknown cuisine, Vegan (pasta, garlic, olive oil) - 15 mins
    # ID 6: "Beef Stew" - American, Non-Vegetarian (beef, potato, carrot, onion) - 120 mins
    # ID 7: "Slow Cooker Tomato Soup" - Unknown cuisine, Vegetarian (tomato, cream, onion) - 240 mins
    # ID 8: "Quick Mystery Snack" - Unknown cuisine, Vegan, unknown time (tomato, basil) - NULL time

    ingredients_master = [
        "pasta", "tomato", "garlic", "basil", "olive oil", "chicken",
        "cheese", "paneer", "butter", "spices", "onion", "curry powder",
        "beef", "potato", "carrot", "cream"
    ]
    for idx, ing in enumerate(ingredients_master, start=1):
        conn.execute("INSERT INTO ingredients (id, name) VALUES (?, ?);", (idx, ing))

    ing_to_id = {name: idx for idx, name in enumerate(ingredients_master, start=1)}

    recipes_data = [
        {
            "recipe_id": 1,
            "title": "Spaghetti Marinara",
            "ingredients": ["pasta", "tomato", "garlic", "basil", "olive oil"],
            "directions": ["Boil pasta 10 minutes.", "Simmer sauce 10 minutes."],
            "ner": ["pasta", "tomato", "garlic", "basil", "olive oil"],
            "meta": ("Italian", "high", "title_keyword", "vegan_compatible", "low", "no_animal", 20, "high", "regex"),
        },
        {
            "recipe_id": 2,
            "title": "Chicken Parmesan",
            "ingredients": ["chicken", "pasta", "tomato", "cheese"],
            "directions": ["Fry chicken 15 minutes.", "Bake 30 minutes."],
            "ner": ["chicken", "pasta", "tomato", "cheese"],
            "meta": ("Italian", "high", "title_keyword", "non_vegetarian", "high", "detected_meat", 45, "medium", "multi_step"),
        },
        {
            "recipe_id": 3,
            "title": "Paneer Butter Masala",
            "ingredients": ["paneer", "tomato", "butter", "spices"],
            "directions": ["Cook gravy 20 minutes.", "Simmer 10 minutes."],
            "ner": ["paneer", "tomato", "butter", "spices"],
            "meta": ("Indian", "high", "title_keyword", "vegetarian_compatible", "medium", "detected_dairy", 30, "high", "regex"),
        },
        {
            "recipe_id": 4,
            "title": "Chicken Curry",
            "ingredients": ["chicken", "tomato", "onion", "curry powder"],
            "directions": ["Brown chicken 10 minutes.", "Simmer 25 minutes."],
            "ner": ["chicken", "tomato", "onion", "curry powder"],
            "meta": ("Indian", "high", "title_keyword", "non_vegetarian", "high", "detected_meat", 35, "medium", "multi_step"),
        },
        {
            "recipe_id": 5,
            "title": "Simple Garlic Pasta",
            "ingredients": ["pasta", "garlic", "olive oil"],
            "directions": ["Boil pasta 10 minutes.", "Saute garlic 5 minutes."],
            "ner": ["pasta", "garlic", "olive oil"],
            "meta": (None, None, "insufficient_evidence", "vegan_compatible", "low", "no_animal", 15, "medium", "multi_step"),
        },
        {
            "recipe_id": 6,
            "title": "Beef Stew",
            "ingredients": ["beef", "potato", "carrot", "onion"],
            "directions": ["Simmer for 2 hours."],
            "ner": ["beef", "potato", "carrot", "onion"],
            "meta": ("American", "medium", "signature_profile", "non_vegetarian", "high", "detected_meat", 120, "high", "regex"),
        },
        {
            "recipe_id": 7,
            "title": "Slow Cooker Tomato Soup",
            "ingredients": ["tomato", "cream", "onion"],
            "directions": ["Cook in slow cooker 4 hours."],
            "ner": ["tomato", "cream", "onion"],
            "meta": (None, None, "insufficient_evidence", "vegetarian_compatible", "medium", "detected_dairy", 240, "high", "regex"),
        },
        {
            "recipe_id": 8,
            "title": "Quick Mystery Snack",
            "ingredients": ["tomato", "basil"],
            "directions": ["Mix together and serve immediately."],
            "ner": ["tomato", "basil"],
            "meta": (None, None, "insufficient_evidence", "vegan_compatible", "low", "no_animal", None, None, "no_explicit_duration_found"),
        },
    ]

    parquet_rows = []
    for r in recipes_data:
        r_id = r["recipe_id"]
        ner = r["ner"]
        conn.execute("INSERT INTO recipes_metadata (recipe_id, ner_count) VALUES (?, ?);", (r_id, len(ner)))
        for item in ner:
            ing_id = ing_to_id[item]
            conn.execute("INSERT INTO recipe_ingredients (ingredient_id, recipe_id) VALUES (?, ?);", (ing_id, r_id))

        meta_conn.execute(
            "INSERT INTO recipe_metadata VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (r_id, *r["meta"])
        )

        parquet_rows.append({
            "recipe_id": r_id,
            "title": r["title"],
            "ingredients": r["ingredients"],
            "directions": r["directions"],
            "link": f"http://example.com/{r_id}",
            "source": "test",
            "ner": ner,
            "ner_count": len(ner),
        })

    conn.commit()
    conn.close()
    meta_conn.commit()
    meta_conn.close()

    table = pa.Table.from_pylist(parquet_rows)
    pq.write_table(table, str(parquet_path))

    engine = RecommendationEngine(
        sqlite_path=sqlite_path,
        parquet_path=parquet_path,
        metadata_path=metadata_path,
        ims_weight=0.6,
        pus_weight=0.4,
        candidate_limit=20,
    )

    yield engine

    temp_dir.cleanup()


# ==============================================================================
# Unit & Integration Tests: Scenarios A through M
# ==============================================================================

def test_scenario_a_no_preferences(synthetic_personalization_env):
    """A. No preferences: Existing Milestone 2 behavior remains unchanged."""
    engine = synthetic_personalization_env
    pantry = ["pasta", "tomato", "garlic", "basil", "olive oil"]

    resp = engine.recommend(pantry, limit=5)
    assert resp.total_candidates_evaluated > 0
    assert resp.applied_preferences == {}
    top = resp.recommendations[0]
    # Spaghetti Marinara (ID 1) has 100% match
    assert top.recipe_id == 1
    assert top.ims == 100.0
    assert top.pus == 100.0
    assert top.recommendation_score == 100.0
    assert top.preference_matches == {}
    assert "Personalization:" not in top.explanation


def test_scenario_b_italian_preference(synthetic_personalization_env):
    """B. Italian preference: Italian-compatible recipes receive cuisine bonus."""
    engine = synthetic_personalization_env
    # Provide pantry matching both Italian (ID 1) and Indian (ID 3)
    pantry = ["pasta", "tomato", "garlic", "basil", "olive oil", "paneer", "butter", "spices"]

    resp_italian = engine.recommend(pantry, limit=5, cuisine="Italian")
    assert resp_italian.applied_preferences["cuisine"] == "Italian"

    rec1 = next(r for r in resp_italian.recommendations if r.recipe_id == 1)
    assert rec1.cuisine == "Italian"
    assert rec1.preference_matches["cuisine"]["applied"] is True
    assert rec1.preference_matches["cuisine"]["bonus"] == 15.0
    assert "matches your Italian cuisine preference (+15.0 pts" in rec1.explanation


def test_scenario_c_indian_preference(synthetic_personalization_env):
    """C. Indian preference: Indian-compatible recipes receive cuisine bonus."""
    engine = synthetic_personalization_env
    pantry = ["paneer", "tomato", "butter", "spices", "pasta", "garlic"]

    resp = engine.recommend(pantry, limit=5, cuisine="Indian")
    assert resp.applied_preferences["cuisine"] == "Indian"

    rec3 = next(r for r in resp.recommendations if r.recipe_id == 3)
    assert rec3.cuisine == "Indian"
    assert rec3.preference_matches["cuisine"]["applied"] is True
    assert rec3.preference_matches["cuisine"]["bonus"] == 15.0
    assert "matches your Indian cuisine preference" in rec3.explanation


def test_scenario_d_vegetarian_preference(synthetic_personalization_env):
    """D. Vegetarian preference: Known meat-containing recipes are completely excluded."""
    engine = synthetic_personalization_env
    # Pantry that has chicken and pasta -> Chicken Parmesan (ID 2) and Chicken Curry (ID 4)
    pantry = ["chicken", "pasta", "tomato", "cheese", "garlic"]

    resp = engine.recommend(pantry, limit=10, dietary_preference="vegetarian")
    returned_ids = [r.recipe_id for r in resp.recommendations]

    # IDs 2 and 4 are non_vegetarian and must be filtered out!
    assert 2 not in returned_ids
    assert 4 not in returned_ids
    for r in resp.recommendations:
        assert r.dietary_compatibility != "non_vegetarian"


def test_scenario_e_vegan_preference(synthetic_personalization_env):
    """E. Vegan preference: Known animal-product recipes (meat & dairy) are excluded."""
    engine = synthetic_personalization_env
    # Pantry with pasta, tomato, butter, cheese, garlic
    pantry = ["pasta", "tomato", "butter", "cheese", "garlic", "olive oil"]

    resp = engine.recommend(pantry, limit=10, dietary_preference="vegan")
    returned_ids = [r.recipe_id for r in resp.recommendations]

    # Recipes with dairy: ID 2 (cheese), ID 3 (paneer, butter), ID 7 (cream) must be excluded!
    assert 2 not in returned_ids
    assert 3 not in returned_ids
    assert 7 not in returned_ids

    # Vegan recipes (ID 1, ID 5, ID 8) are retained
    for r in resp.recommendations:
        assert r.dietary_compatibility == "vegan_compatible"


def test_scenario_f_cooking_time_preference(synthetic_personalization_env):
    """
    F. Cooking time: Explicit formula:
    TimeBonus = 10 * ((max_time - estimated_time) / max_time) clamped to [0, 10].
    OveragePenalty = min(15.0, 0.2 * (estimated - max_time)).
    """
    engine = synthetic_personalization_env
    pantry = ["pasta", "garlic", "olive oil", "tomato"]

    # max_time = 30
    # Recipe 5: est 15 min -> 10 * ((30 - 15) / 30) = +5.0
    # Recipe 1: est 20 min -> 10 * ((30 - 20) / 30) = +3.33
    # Recipe 3: est 30 min -> 10 * ((30 - 30) / 30) = +0.0
    bonus_15, info_15 = calculate_time_adjustment(15, 30)
    assert bonus_15 == 5.0
    assert info_15["status"] == "within_limit"

    bonus_20, info_20 = calculate_time_adjustment(20, 30)
    assert bonus_20 == 3.33
    assert info_20["status"] == "within_limit"

    bonus_30, info_30 = calculate_time_adjustment(30, 30)
    assert bonus_30 == 0.0

    # Over limit: Recipe 6 est 120 min, max 30 -> 0.2 * (120 - 30) = 18.0 -> capped at 15.0
    pen_120, info_120 = calculate_time_adjustment(120, 30)
    assert pen_120 == -15.0
    assert info_120["status"] == "exceeded_limit"


def test_scenario_g_unknown_cooking_time(synthetic_personalization_env):
    """G. Unknown cooking time: Handled gracefully, receives neutral +0.0, no false claims."""
    engine = synthetic_personalization_env
    pantry = ["tomato", "basil"]

    resp = engine.recommend(pantry, limit=5, max_cooking_time_minutes=30)
    rec8 = next((r for r in resp.recommendations if r.recipe_id == 8), None)
    if rec8:
        assert rec8.estimated_time_minutes is None
        assert rec8.preference_matches["time"]["applied"] is False
        assert rec8.preference_matches["time"]["status"] == "unknown_cooking_time"
        assert "cooking time could not be reliably extracted" in rec8.explanation


def test_scenario_h_unknown_cuisine(synthetic_personalization_env):
    """H. Unknown cuisine: Does not falsely match requested cuisine, receives neutral +0.0."""
    engine = synthetic_personalization_env
    pantry = ["pasta", "garlic", "olive oil"]

    resp = engine.recommend(pantry, limit=5, cuisine="Italian")
    # Recipe 5 has unknown cuisine
    rec5 = next((r for r in resp.recommendations if r.recipe_id == 5), None)
    if rec5:
        assert rec5.cuisine is None
        assert rec5.preference_matches["cuisine"]["applied"] is False
        assert rec5.preference_matches["cuisine"]["status"] == "unknown_recipe_cuisine"
        assert "cuisine could not be confidently determined" in rec5.explanation


def test_scenario_i_multiple_preferences(synthetic_personalization_env):
    """I. Multiple preferences: Cuisine + Dietary + Time combined harmoniously."""
    engine = synthetic_personalization_env
    pantry = ["pasta", "tomato", "garlic", "basil", "olive oil", "chicken", "cheese"]

    resp = engine.recommend(
        pantry,
        limit=5,
        cuisine="Italian",
        dietary_preference="vegetarian",
        max_cooking_time_minutes=30,
    )

    # Chicken Parmesan (ID 2) is non-vegetarian and must be filtered out
    returned_ids = [r.recipe_id for r in resp.recommendations]
    assert 2 not in returned_ids

    # Spaghetti Marinara (ID 1) satisfies all three: Italian (+15), Vegetarian (compatible), 20 min (+3.33)
    top = resp.recommendations[0]
    assert top.recipe_id == 1
    assert top.preference_matches["cuisine"]["applied"] is True
    assert top.preference_matches["time"]["applied"] is True
    assert top.preference_matches["dietary"]["satisfied"] is True


def test_scenario_j_pantry_remains_foundational(synthetic_personalization_env):
    """J. Pantry match remains foundational: High preference cannot overpower poor pantry match."""
    engine = synthetic_personalization_env
    # User has only pasta and garlic
    pantry = ["pasta", "garlic"]

    # Recipe 5: has pasta, garlic, olive oil (IMS 66.7%, PUS 100%) -> base score ~80.0
    # Recipe 3: Paneer Butter Masala (0 pantry match, won't even be in candidates)
    resp = engine.recommend(pantry, limit=5, cuisine="Indian")
    # The top recommendation MUST be recipe 5 despite Indian cuisine preference
    top = resp.recommendations[0]
    assert top.recipe_id == 5
    assert top.ims > 0


def test_scenario_l_api_integration():
    """L. API integration: Test POST /api/recommendations with personalization fields."""
    client = TestClient(app)

    # Test with valid preferences
    payload = {
        "pantry_ingredients": ["tomato", "onion", "garlic", "pasta"],
        "cuisine": "Italian",
        "dietary_preference": "vegetarian",
        "max_cooking_time_minutes": 30,
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "applied_preferences" in data
    assert data["applied_preferences"]["cuisine"] == "Italian"
    assert data["applied_preferences"]["dietary_preference"] == "vegetarian"
    assert data["applied_preferences"]["max_cooking_time_minutes"] == 30

    if data["recommendations"]:
        first = data["recommendations"][0]
        assert "cuisine" in first
        assert "dietary_compatibility" in first
        assert "estimated_time_minutes" in first
        assert "preference_matches" in first
        assert "explanation_data" in first

    # Test invalid cuisine validation (HTTP 422)
    invalid_cuisine_payload = {
        "pantry_ingredients": ["tomato"],
        "cuisine": "MartianFood",
    }
    resp_invalid = client.post("/api/recommendations", json=invalid_cuisine_payload)
    assert resp_invalid.status_code == 422

    # Test invalid dietary validation (HTTP 422)
    invalid_diet_payload = {
        "pantry_ingredients": ["tomato"],
        "dietary_preference": "carnivore_only",
    }
    resp_invalid_diet = client.post("/api/recommendations", json=invalid_diet_payload)
    assert resp_invalid_diet.status_code == 422


def test_scenario_m_deterministic_repeated_requests(synthetic_personalization_env):
    """M. Deterministic repeated requests: Repeated calls with preferences produce identical outputs."""
    engine = synthetic_personalization_env
    pantry = ["pasta", "tomato", "garlic", "basil", "olive oil"]

    res1 = engine.recommend(pantry, limit=5, cuisine="Italian", max_cooking_time_minutes=30)
    res2 = engine.recommend(pantry, limit=5, cuisine="Italian", max_cooking_time_minutes=30)

    assert len(res1.recommendations) == len(res2.recommendations)
    for r1, r2 in zip(res1.recommendations, res2.recommendations):
        assert r1.recipe_id == r2.recipe_id
        assert r1.recommendation_score == r2.recommendation_score
        assert r1.explanation == r2.explanation
