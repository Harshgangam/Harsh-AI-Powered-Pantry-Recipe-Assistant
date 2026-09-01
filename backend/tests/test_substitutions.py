from typing import List, Optional
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.substitutions.context import detect_culinary_context
from backend.app.substitutions.models import SubstitutionCandidate, SubstitutionEntry
from backend.app.substitutions.service import SubstitutionService, substitution_service


# ==============================================================================
# Unit & Integration Tests for Milestone 4: Substitutions (Scenarios A - M)
# ==============================================================================

def test_scenario_a_no_missing_ingredients():
    """A. Recipe with no missing ingredients: substitutions must be empty."""
    subs = substitution_service.get_substitutions_for_recipe(
        missing_ingredients=[],
        recipe_title="Pasta Marinara",
        directions=["Boil pasta 10 minutes."],
    )
    assert subs == []


def test_scenario_b_one_known_missing_ingredient():
    """B. Recipe with one known missing ingredient: appropriate substitution returned."""
    subs = substitution_service.get_substitutions_for_recipe(
        missing_ingredients=["parmesan cheese"],
        recipe_title="Spaghetti with Parmesan",
        directions=["Grate cheese on top."],
    )
    assert len(subs) >= 1
    sub = subs[0]
    assert sub.missing_ingredient == "parmesan cheese"
    assert sub.substitute in ("pecorino romano", "nutritional yeast")
    assert sub.confidence in ("high", "medium")
    assert sub.reason is not None
    assert len(sub.reason) > 0


def test_scenario_c_multiple_missing_ingredients():
    """C. Recipe with multiple missing ingredients: each handled independently."""
    subs = substitution_service.get_substitutions_for_recipe(
        missing_ingredients=["butter", "garlic"],
        recipe_title="Garlic Butter Shrimp",
        directions=["Saute garlic in skillet with butter."],
    )
    missing_names = {s.missing_ingredient for s in subs}
    assert "butter" in missing_names
    assert "garlic" in missing_names
    assert len(subs) >= 2


def test_scenario_d_unknown_missing_ingredient():
    """D. Unknown missing ingredient: no fabricated substitution (returns empty list)."""
    subs = substitution_service.get_substitutions_for_recipe(
        missing_ingredients=["rare_mystic_root", "dragonfruit_powder"],
        recipe_title="Exotic Dish",
        directions=["Mix well."],
    )
    assert subs == []


def test_scenario_e_high_confidence_substitution():
    """E. High-confidence substitution: correct ratio, reason, confidence."""
    subs = substitution_service.get_substitutions_for_ingredient(
        missing_ingredient="butter",
        context="baking",
    )
    assert len(subs) > 0
    top_sub = subs[0]
    assert top_sub.confidence == "high"
    assert top_sub.ratio in ("1:1", "1:0.75")
    assert "fat" in top_sub.reason.lower() or "moisture" in top_sub.reason.lower()


def test_scenario_f_unknown_ratio():
    """F. Unknown ratio: ratio remains None when unquantified, never fabricated."""
    custom_entry = SubstitutionEntry(
        original_ingredient="mystery_spice",
        substitute="generic_herb",
        ratio=None,
        confidence="medium",
        dietary_compatibility=["vegetarian", "vegan"],
        use_cases=["general"],
        reason="Adds similar herbal earthiness.",
    )
    service = SubstitutionService(database=[custom_entry])
    subs = service.get_substitutions_for_ingredient("mystery_spice")
    assert len(subs) == 1
    assert subs[0].ratio is None


def test_scenario_g_vegan_preference():
    """G. Vegan preference: dairy/animal substitutes rejected, plant-based returned."""
    # For missing 'milk', dairy cream is rejected; soy or almond milk is returned
    subs = substitution_service.get_substitutions_for_ingredient(
        missing_ingredient="milk",
        dietary_preference="vegan",
    )
    assert len(subs) > 0
    for s in subs:
        assert s.dietary_compatible is True
        assert "dairy" not in s.substitute.lower()
        assert s.substitute in ("soy milk", "almond milk", "oat milk")

    # For missing 'butter' under vegan, margarine or olive oil is returned
    butter_subs = substitution_service.get_substitutions_for_ingredient(
        missing_ingredient="butter",
        dietary_preference="vegan",
    )
    assert len(butter_subs) > 0
    for s in butter_subs:
        assert s.substitute in ("margarine", "olive oil", "applesauce")


def test_scenario_h_vegetarian_preference():
    """H. Vegetarian preference: meat/fish broths rejected, vegetable broth returned."""
    subs = substitution_service.get_substitutions_for_ingredient(
        missing_ingredient="chicken broth",
        dietary_preference="vegetarian",
    )
    assert len(subs) > 0
    substitutes = [s.substitute for s in subs]
    assert "vegetable broth" in substitutes
    assert "beef broth" not in substitutes


def test_scenario_i_context_aware_use_case():
    """I. Context-aware use case: baking vs frying context appropriately prioritized."""
    # In Baking: butter -> margarine / applesauce prioritized
    baking_context = detect_culinary_context(
        title="Chocolate Chip Cookies",
        directions=["Preheat oven to 350. Bake on sheet pan for 12 minutes."],
    )
    assert baking_context == "baking"

    baking_subs = substitution_service.get_substitutions_for_ingredient(
        missing_ingredient="butter",
        context=baking_context,
    )
    assert len(baking_subs) > 0
    assert baking_subs[0].substitute in ("margarine", "applesauce")

    # In Frying: butter -> olive oil prioritized
    frying_context = detect_culinary_context(
        title="Sauteed Garlic Mushrooms",
        directions=["Heat skillet over medium heat. Saute in pan for 5 minutes."],
    )
    assert frying_context == "frying"

    frying_subs = substitution_service.get_substitutions_for_ingredient(
        missing_ingredient="butter",
        context=frying_context,
    )
    assert len(frying_subs) > 0
    assert frying_subs[0].substitute == "olive oil"


def test_scenario_j_no_dietary_preference():
    """J. No dietary preference: normal culinary substitutions returned."""
    subs = substitution_service.get_substitutions_for_ingredient("parmesan cheese")
    assert len(subs) > 0
    substitutes = [s.substitute for s in subs]
    assert "pecorino romano" in substitutes


def test_scenario_k_api_integration():
    """K. API integration: POST /api/recommendations returns complete substitution payload."""
    client = TestClient(app)
    # User has pasta, tomato, garlic; recipe may require parmesan or butter
    payload = {
        "pantry_ingredients": ["pasta", "tomato", "garlic"],
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data

    for item in data["recommendations"]:
        assert "missing_ingredients" in item
        assert "missing_count" in item
        assert "substitutions" in item
        assert item["missing_count"] == len(item["missing_ingredients"])
        if item["substitutions"]:
            first_sub = item["substitutions"][0]
            assert "missing_ingredient" in first_sub
            assert "substitute" in first_sub
            assert "confidence" in first_sub
            assert "reason" in first_sub


def test_scenario_m_deterministic_behavior():
    """M. Deterministic behavior: Repeated calls produce identical substitution outcomes."""
    missing = ["butter", "milk", "onion"]
    res1 = substitution_service.get_substitutions_for_recipe(
        missing_ingredients=missing,
        recipe_title="Cream of Onion Soup",
        directions=["Simmer soup in pot."],
        dietary_preference="vegetarian",
    )
    res2 = substitution_service.get_substitutions_for_recipe(
        missing_ingredients=missing,
        recipe_title="Cream of Onion Soup",
        directions=["Simmer soup in pot."],
        dietary_preference="vegetarian",
    )

    assert len(res1) == len(res2)
    for s1, s2 in zip(res1, res2):
        assert s1.missing_ingredient == s2.missing_ingredient
        assert s1.substitute == s2.substitute
        assert s1.ratio == s2.ratio
        assert s1.confidence == s2.confidence
        assert s1.reason == s2.reason
