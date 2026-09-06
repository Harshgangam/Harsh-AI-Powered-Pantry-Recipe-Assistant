import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from data_pipeline.enrichment.taxonomy import SUPPORTED_CUISINES


class RoutedQuery(BaseModel):
    intent: str
    is_out_of_domain: bool = False
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    reasoning: str = ""


class QueryRouter:
    """
    Dynamic Natural-Language Query Router analyzing user text requests to infer intent
    and extract domain entities (ingredients, cuisine, dietary preference, time limit).
    """

    OUT_OF_DOMAIN_KEYWORDS = [
        "cricket", "football", "match", "weather", "politics", "president",
        "election", "stock", "crypto", "bitcoin", "movie", "song", "who won"
    ]

    INTENT_PATTERNS = {
        "PANTRY_QUERY": [
            r"what expires", r"expire", r"expiry", r"how much .* do i have",
            r"pantry status", r"what do i have in my pantry", r"check my pantry"
        ],
        "SUBSTITUTION": [
            r"replace", r"substitute", r"swap", r"instead of", r"without", r"alternative for",
            r"can i use .* instead", r"what if i don.t have"
        ],
        "SCALING": [
            r"for \d+ people", r"for \d+ persons", r"for \d+ servings",
            r"how much .* for \d+", r"scale (up|down|for|to)",
            r"double the recipe", r"half the recipe", r"triple the recipe",
            r"\d+ servings", r"serve \d+"
        ],
        "COOKING_KNOWLEDGE": [
            r"what is ", r"how to ", r"define", r"technique", r"meaning of",
            r"less spicy", r"how do i cook", r"saut", r"explain what",
            r"how long", r"what temperature", r"store", r"storage",
            r"who invented", r"history of", r"origin of", r"where did .* come from",
            r"who created", r"first person to", r"fun fact"
        ],
        "LEFTOVER_QUERY": [
            r"leftover", r"cooked too much", r"yesterday's", r"repurpose"
        ],
        "MEAL_PLANNING": [
            r"meal plan", r"three-day", r"3-day", r"plan my meals", r"weekly plan"
        ],
        "FOOD_RESCUE": [
            r"going bad", r"expiring", r"most of my", r"food waste", r"rescue", r"use up"
        ],
        "RECIPE_EXPLANATION": [
            r"why did you recommend", r"why this recipe", r"why is this good", r"explain score"
        ],
        "GENERAL_KNOWLEDGE": [
            r"who invented", r"history of", r"origin of", r"where did .* come from",
            r"who created", r"first person to", r"fun fact", r"did you know",
            r"what is the difference between", r"explain .* to me", r"tell me about",
            r"can dogs eat", r"is .* healthy", r"is .* safe to eat",
            r"best pan", r"best pot", r"which knife", r"kitchen tip",
            r"how many calories", r"nutrition", r"protein in",
        ],
        "RECIPE_SEARCH": [
            r"what can i cook", r"what can i make", r"recipe for", r"meal ideas",
            r"suggest something", r"quick meal", r"dinner", r"lunch", r"breakfast"
        ]
    }

    @classmethod
    def route_query(cls, query_text: str, active_pantry: Optional[List[str]] = None) -> RoutedQuery:
        q_lower = query_text.lower().strip()

        # 1. Out-of-domain detection
        if any(kw in q_lower for kw in cls.OUT_OF_DOMAIN_KEYWORDS):
            return RoutedQuery(
                intent="OUT_OF_DOMAIN",
                is_out_of_domain=True,
                extracted_entities={},
                confidence=1.0,
                reasoning="Query pertains to non-culinary topics (sports, news, or general trivia)."
            )

        # 2. Entity Extraction
        entities: Dict[str, Any] = {}

        # Dietary extraction
        if "vegetarian" in q_lower or "veg" in q_lower:
            entities["dietary_preference"] = "vegetarian"
        elif "vegan" in q_lower:
            entities["dietary_preference"] = "vegan"

        # Time extraction (e.g., "20 minutes", "under 30 mins", "quick")
        time_match = re.search(r"(\d+)\s*(mins?|minutes?)", q_lower)
        if time_match:
            entities["max_cooking_time_minutes"] = int(time_match.group(1))
        elif "quick" in q_lower or "fast" in q_lower:
            entities["max_cooking_time_minutes"] = 20

        # Cuisine extraction
        for c in SUPPORTED_CUISINES:
            if c.lower() in q_lower:
                entities["cuisine"] = c
                break

        # Ingredient extraction from query
        extracted_ings = []
        common_ings = ["rice", "spinach", "tomato", "tomatoes", "paneer", "chicken", "pasta", "garlic", "onion", "egg", "eggs", "cheese", "milk", "bread"]
        for ing in common_ings:
            if ing in q_lower:
                extracted_ings.append(ing)

        if extracted_ings:
            entities["pantry_ingredients"] = extracted_ings
        elif active_pantry:
            entities["pantry_ingredients"] = active_pantry

        # 3. Intent Classification
        matched_intent = "RECIPE_SEARCH"  # Default domain intent

        for intent, patterns in cls.INTENT_PATTERNS.items():
            if any(re.search(pat, q_lower) for pat in patterns):
                matched_intent = intent
                break

        return RoutedQuery(
            intent=matched_intent,
            is_out_of_domain=False,
            extracted_entities=entities,
            confidence=0.9,
            reasoning=f"Classified intent as {matched_intent} with entities {list(entities.keys())}."
        )
