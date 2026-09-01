import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from backend.app.assistant.query_router import RoutedQuery

logger = logging.getLogger(__name__)


class ConversationState(BaseModel):
    session_id: str
    pantry_ingredients: List[str] = Field(default_factory=list)
    cuisine: Optional[str] = None
    dietary_preference: Optional[str] = None
    max_cooking_time_minutes: Optional[int] = None
    selected_recipe_id: Optional[int] = None
    previous_queries: List[str] = Field(default_factory=list)
    history: List[Dict[str, str]] = Field(default_factory=list)


class ConversationManager:
    """
    Stateful Conversation Manager tracking session context across turns
    to handle multi-turn follow-up requests.
    """

    def __init__(self):
        self._sessions: Dict[str, ConversationState] = {}

    def get_or_create_state(self, session_id: str = "default_session") -> ConversationState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState(session_id=session_id)
        return self._sessions[session_id]

    def update_state(self, session_id: str, query_text: str, routed: RoutedQuery) -> ConversationState:
        state = self.get_or_create_state(session_id)
        state.previous_queries.append(query_text)

        entities = routed.extracted_entities
        if "dietary_preference" in entities:
            state.dietary_preference = entities["dietary_preference"]
        if "max_cooking_time_minutes" in entities:
            state.max_cooking_time_minutes = entities["max_cooking_time_minutes"]
        if "cuisine" in entities:
            state.cuisine = entities["cuisine"]
        if "pantry_ingredients" in entities and entities["pantry_ingredients"]:
            # Merge pantry ingredients while preserving existing
            merged = set(state.pantry_ingredients + entities["pantry_ingredients"])
            state.pantry_ingredients = list(merged)

        return state

    def record_turn(self, session_id: str, user_text: str, assistant_response: str):
        state = self.get_or_create_state(session_id)
        state.history.append({"user": user_text, "assistant": assistant_response})


# Global singleton instance
conversation_manager = ConversationManager()
