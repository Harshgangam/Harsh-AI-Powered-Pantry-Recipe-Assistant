import pytest
from data_pipeline.enrichment.dietary_classifier import classify_dietary_compatibility
from backend.app.recommendation.personalizer import is_dietary_compatible, evaluate_personalization
from backend.app.recommendation.scorer import calculate_dcs
from backend.app.recommendation.engine import RecommendationEngine
from backend.app.assistant.service import assistant_service
from backend.app.assistant.models import AssistantRequest


def test_dietary_classifier_non_vegetarian():
    """Verify non-vegetarian ingredients are correctly classified as non_vegetarian."""
    non_veg_samples = [
        ["chicken breast", "tomato", "garlic"],
        ["ground beef", "onion", "cheese"],
        ["salmon fillet", "lemon", "dill"],
        ["shrimp", "butter", "garlic"],
        ["pork chops", "applesauce"],
        ["lamb chops", "rosemary"],
    ]
    for ner in non_veg_samples:
        diet, conf, method = classify_dietary_compatibility(ner)
        assert diet == "non_vegetarian"
        assert conf == "high"


def test_dietary_classifier_vegetarian_and_vegan():
    """Verify vegetarian and vegan classifications remain unchanged."""
    veg_ner = ["paneer", "tomato", "onion", "butter"]
    diet_veg, conf_veg, _ = classify_dietary_compatibility(veg_ner)
    assert diet_veg == "vegetarian_compatible"

    vegan_ner = ["rice", "spinach", "tomato", "olive oil"]
    diet_vegan, conf_vegan, _ = classify_dietary_compatibility(vegan_ner)
    assert diet_vegan == "vegan_compatible"


def test_is_dietary_compatible_non_vegetarian_filter():
    """Verify is_dietary_compatible respects non_vegetarian preference."""
    assert is_dietary_compatible("non_vegetarian", "non_vegetarian") is True
    assert is_dietary_compatible("vegetarian_compatible", "non_vegetarian") is False
    assert is_dietary_compatible("vegan_compatible", "non_vegetarian") is False

    # Vegetarian user must NOT get non_vegetarian recipes
    assert is_dietary_compatible("non_vegetarian", "vegetarian") is False
    # Vegan user must NOT get non_vegetarian recipes
    assert is_dietary_compatible("non_vegetarian", "vegan") is False


def test_calculate_dcs_non_vegetarian():
    """Verify DCS score calculation for non_vegetarian preference."""
    assert calculate_dcs("non_vegetarian", "non_vegetarian") == 100.0
    assert calculate_dcs("non_vegetarian", "vegetarian_compatible") == 0.0
    assert calculate_dcs("non_vegetarian", "vegan_compatible") == 0.0


def test_recommendation_engine_non_vegetarian_search():
    """Verify recommendation engine returns real non-vegetarian recipes from RecipeNLG dataset."""
    engine = RecommendationEngine()
    pantry = ["chicken", "tomato", "onion", "garlic", "rice", "ginger"]

    res = engine.recommend(
        pantry_ingredients=pantry,
        limit=5,
        dietary_preference="non_vegetarian",
    )

    assert res.total_candidates_evaluated > 0
    assert len(res.recommendations) > 0

    top_rec = res.recommendations[0]
    assert top_rec.dietary_compatibility == "non_vegetarian"
    assert top_rec.recommendation_score > 0
    assert top_rec.ims > 0
    assert top_rec.pus > 0
    assert top_rec.why_this_recipe is not None


def test_rag_assistant_non_vegetarian_query():
    """Verify RAG assistant handles non-vegetarian culinary inquiries."""
    req = AssistantRequest(
        recipe_id=1,
        task="question",
        question="What is the easiest chicken recipe I can make with tomato and garlic?",
        pantry_ingredients=["chicken", "tomato", "garlic"],
        dietary_preference="non_vegetarian",
    )

    resp = assistant_service.get_guidance(req)
    assert resp.answer is not None
    assert len(resp.answer) > 0
    assert not resp.is_mock or len(resp.citations) > 0
