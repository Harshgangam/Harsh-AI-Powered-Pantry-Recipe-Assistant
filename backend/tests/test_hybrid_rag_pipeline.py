import pytest
from backend.app.assistant.query_router import QueryRouter
from backend.app.assistant.conversation_manager import conversation_manager
from backend.app.assistant.rag_engine import rag_knowledge_base, recipe_verifier
from backend.app.assistant.service import assistant_service
from backend.app.assistant.models import AssistantRequest
from backend.app.recommendation.hybrid_retriever import hybrid_retriever
from backend.app.recommendation.engine import RecommendationEngine


def test_query_router_intent_classification():
    """Verify QueryRouter accurately classifies natural language query intents."""
    router = QueryRouter()

    q1 = router.route_query("What can I cook with rice and tomato?")
    assert q1.intent in ("RECIPE_SEARCH", "PANTRY_QUERY")
    assert not q1.is_out_of_domain

    q2 = router.route_query("I have spinach expiring tomorrow. What should I cook first?")
    assert q2.intent in ("FOOD_RESCUE", "PANTRY_QUERY")

    q3 = router.route_query("What can replace paneer?")
    assert q3.intent == "SUBSTITUTION"

    q4 = router.route_query("Explain what sauteing means.")
    assert q4.intent in ("COOKING_KNOWLEDGE", "RECIPE_EXPLANATION")

    q5 = router.route_query("I cooked too much rice yesterday. What can I do with it?")
    assert q5.intent in ("LEFTOVER_QUERY", "RECIPE_SEARCH")

    q6 = router.route_query("Give me a three-day meal plan using my pantry.")
    assert q6.intent == "MEAL_PLANNING"

    q7 = router.route_query("Who won yesterday's cricket match?")
    assert q7.intent == "OUT_OF_DOMAIN"
    assert q7.is_out_of_domain


def test_out_of_domain_guardrail_refusal():
    """Verify out-of-domain queries return polite domain refusal."""
    req = AssistantRequest(recipe_id=1, task="question", question="Who won yesterday's cricket match?")
    resp = assistant_service.get_guidance(req)
    assert "cannot assist with non-culinary topics" in resp.answer
    assert resp.provider == "verifier_guardrail"


def test_hybrid_retriever_execution():
    """Verify HybridRetriever executes FAISS vector search and SQLite lookup."""
    pantry = {"tomato", "rice", "garlic"}
    candidate_ids, details_map, metadata_map = hybrid_retriever.retrieve_candidates(
        pantry_variants=pantry,
        query_text="quick spicy rice bowl",
        limit=10,
    )
    assert len(candidate_ids) > 0
    assert len(details_map) > 0


def test_conversation_manager_state_persistence():
    """Verify multi-turn state persistence (e.g. updating diet or time limit)."""
    session = "test_session_1"

    # Turn 1: Pantry input
    q1 = QueryRouter.route_query("I have rice and spinach", active_pantry=["rice", "spinach"])
    state1 = conversation_manager.update_state(session, "I have rice and spinach", q1)
    assert "rice" in state1.pantry_ingredients

    # Turn 2: Follow-up constraint
    q2 = QueryRouter.route_query("Make it vegetarian")
    state2 = conversation_manager.update_state(session, "Make it vegetarian", q2)
    assert state2.dietary_preference == "vegetarian"
    assert "rice" in state2.pantry_ingredients  # Preserved from previous turn!

    # Turn 3: Follow-up time constraint
    q3 = QueryRouter.route_query("I only have 20 minutes")
    state3 = conversation_manager.update_state(session, "I only have 20 minutes", q3)
    assert state3.max_cooking_time_minutes == 20
    assert state3.dietary_preference == "vegetarian"  # Preserved!


def test_paraphrased_query_understanding():
    """Verify paraphrased queries map to recipe search intent."""
    router = QueryRouter()
    queries = [
        "What can I cook with rice?",
        "What can I make using the rice I have?",
        "I have rice. Any meal ideas?",
        "Suggest something from my rice",
        "I need a recipe that uses my rice"
    ]
    for q in queries:
        routed = router.route_query(q)
        assert not routed.is_out_of_domain
        assert "rice" in routed.extracted_entities.get("pantry_ingredients", [])


def test_rag_knowledge_retrieval():
    """Verify RAG knowledge retrieval fetches relevant documents for substitutions and techniques."""
    docs_sub = rag_knowledge_base.retrieve_relevant_docs("What can replace paneer?", top_k=2)
    assert any("Paneer" in d.title for d in docs_sub)

    docs_tech = rag_knowledge_base.retrieve_relevant_docs("sautéing technique", top_k=2)
    assert any("Sautéing" in d.title for d in docs_tech)
