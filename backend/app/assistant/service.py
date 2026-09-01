import logging
from typing import List, Optional, Dict, Any

from backend.app.assistant.context_assembler import context_assembler
from backend.app.assistant.conversation_manager import conversation_manager
from backend.app.assistant.llm_client import get_llm_client
from backend.app.assistant.models import (
    AssistantRequest,
    AssistantResponse,
    AssistantStatusResponse,
    GroundingCitation,
)
from backend.app.assistant.prompts import SYSTEM_GROUNDING_PROMPT, build_user_prompt
from backend.app.assistant.query_router import QueryRouter, RoutedQuery
from backend.app.assistant.rag_engine import rag_knowledge_base, recipe_verifier
from backend.app.config import settings
from backend.app.pantry.pantry_store import pantry_store
from backend.app.recommendation.engine import RecommendationEngine

logger = logging.getLogger(__name__)


class AssistantService:
    """
    Open-Ended Dynamic RAG Assistant Service combining:
    QueryRouter -> ConversationManager -> HybridRetriever (FAISS + SQLite) ->
    FRPS Ranking -> RAG Knowledge Base -> LLM -> Recipe Verifier.
    """

    def __init__(self):
        self.assembler = context_assembler
        self.router = QueryRouter()
        self.conversation_manager = conversation_manager
        self.knowledge_base = rag_knowledge_base
        self.verifier = recipe_verifier
        self.engine = RecommendationEngine()

    def get_guidance(self, request: AssistantRequest) -> AssistantResponse:
        """
        Main entry point processing natural language queries or structured assistant tasks.
        """
        query_text = request.question or request.task
        session_id = getattr(request, "session_id", "default_session") or "default_session"

        # 1. Dynamic Natural Language Query Routing
        active_pantry_items = pantry_store.get_all(status="available")
        pantry_names = [item.name for item in active_pantry_items]
        user_pantry = request.pantry_ingredients or pantry_names

        routed: RoutedQuery = self.router.route_query(query_text, active_pantry=user_pantry)

        # 2. Out-of-domain handling
        if routed.is_out_of_domain:
            return AssistantResponse(
                recipe_id=request.recipe_id or 0,
                recipe_title="Out-of-Domain Request",
                task=request.task,
                answer=(
                    "I am an AI Pantry Intelligence & Food Rescue Assistant specialized in recipes, "
                    "cooking, ingredients, substitutions, pantry management, food rescue, leftovers, "
                    "and meal planning. I cannot assist with non-culinary topics such as sports or news."
                ),
                citations=[],
                substitutions_used=[],
                unsupported_inquiries=[query_text],
                provider="verifier_guardrail",
                model="guardrail",
                is_mock=True,
            )

        # 3. Update Conversation State (Stateful context tracking)
        conv_state = self.conversation_manager.update_state(session_id, query_text, routed)
        effective_diet = request.dietary_preference or conv_state.dietary_preference
        effective_cuisine = request.cuisine or conv_state.cuisine
        effective_max_time = request.max_cooking_time_minutes or conv_state.max_cooking_time_minutes
        effective_pantry = user_pantry or conv_state.pantry_ingredients

        # 4. Intent-Driven Retrieval & Processing
        top_recipe_id = request.recipe_id

        if not top_recipe_id and routed.intent in ("RECIPE_SEARCH", "FOOD_RESCUE", "LEFTOVER_QUERY", "MEAL_PLANNING"):
            rec_response = self.engine.recommend(
                pantry_ingredients=effective_pantry,
                limit=5,
                cuisine=effective_cuisine,
                dietary_preference=effective_diet,
                max_cooking_time_minutes=effective_max_time,
                rescue_mode=(routed.intent == "FOOD_RESCUE"),
                query_text=query_text,
            )
            if rec_response.recommendations:
                top_recipe_id = rec_response.recommendations[0].recipe_id

        if not top_recipe_id:
            rec_response = self.engine.recommend(pantry_ingredients=effective_pantry, limit=1)
            if rec_response.recommendations:
                top_recipe_id = rec_response.recommendations[0].recipe_id
            else:
                top_recipe_id = 1

        # 5. Assemble Context (Recipe Details + Derived Metadata + IMS/PUS/FRPS)
        context = self.assembler.assemble_context(
            recipe_id=top_recipe_id,
            pantry_ingredients=effective_pantry,
            cuisine=effective_cuisine,
            dietary_preference=effective_diet,
            max_cooking_time_minutes=effective_max_time,
        )

        if not context:
            raise ValueError(f"Recipe with ID {top_recipe_id} could not be retrieved.")

        # 6. Retrieve RAG Knowledge Base Documents
        rag_docs = self.knowledge_base.retrieve_relevant_docs(query_text, top_k=3)
        rag_context_str = "\n".join([f"- [{doc.title}]: {doc.content}" for doc in rag_docs])

        # 7. Construct Dynamic Prompt
        base_context_str = self.assembler.format_context_for_prompt(context)
        combined_context_str = (
            f"{base_context_str}\n\n"
            f"=== VERIFIED RAG KNOWLEDGE BASE DOCS ===\n{rag_context_str}\n\n"
            f"=== QUERY INTENT & ENTITIES ===\nIntent: {routed.intent}\n"
            f"Entities: {routed.extracted_entities}\n"
        )

        user_prompt = build_user_prompt(
            context_str=combined_context_str,
            task=request.task,
            question=query_text,
        )

        # 8. Invoke LLM Client
        client = get_llm_client()
        raw_answer = client.generate(
            system_prompt=SYSTEM_GROUNDING_PROMPT,
            user_prompt=user_prompt,
            context=context,
            task=request.task,
            question=query_text,
        )

        # 9. Extract Citations & Grounding
        citations: List[GroundingCitation] = []
        substitutions_used: List[str] = []
        unsupported_inquiries: List[str] = []

        answer_lower = raw_answer.lower()
        for sub in context.substitutions:
            sub_name = sub["substitute"].lower()
            orig_name = sub["missing_ingredient"].lower()
            if sub_name in answer_lower or orig_name in answer_lower:
                substitutions_used.append(f"{sub['missing_ingredient']} -> {sub['substitute']}")
                citations.append(
                    GroundingCitation(
                        source_type="curated_substitution",
                        detail=f"Verified substitute for {sub['missing_ingredient']}: {sub['substitute']}",
                    )
                )

        # Always include pantry match citation for matched ingredients in context
        for item in context.matched_ingredients:
            citations.append(
                GroundingCitation(
                    source_type="pantry_match",
                    detail=f"Available pantry ingredient: {item}",
                )
            )

        # Always include derived metadata citation when cuisine metadata present
        if context.cuisine:
            citations.append(
                GroundingCitation(
                    source_type="derived_metadata",
                    detail=f"Cuisine classification: {context.cuisine}",
                )
            )

        for doc in rag_docs:
            citations.append(
                GroundingCitation(
                    source_type=doc.category,
                    detail=f"{doc.title}: {doc.content[:90]}...",
                )
            )

        # 10. Record turn in Conversation State
        self.conversation_manager.record_turn(session_id, query_text, raw_answer)

        return AssistantResponse(
            recipe_id=context.recipe_id,
            recipe_title=context.title,
            task=request.task,
            answer=raw_answer,
            citations=citations,
            substitutions_used=substitutions_used,
            unsupported_inquiries=unsupported_inquiries,
            provider=client.provider_name,
            model=client.model_name,
            is_mock=client.is_mock,
        )

    def get_status(self) -> AssistantStatusResponse:
        client = get_llm_client()
        has_key = bool(settings.LLM_API_KEY.strip())
        return AssistantStatusResponse(
            status="online",
            provider=client.provider_name,
            model=client.model_name,
            is_mock=client.is_mock,
            has_api_key=has_key,
        )


# Global assistant service instance
assistant_service = AssistantService()
