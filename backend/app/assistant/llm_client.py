import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from backend.app.assistant.models import AssistantTask, StructuredRecipeContext
from backend.app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMClient:
    """Abstract interface for LLM client providers."""

    provider_name: str = "base"
    model_name: str = "base-model"
    is_mock: bool = False

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: StructuredRecipeContext,
        task: AssistantTask,
        question: Optional[str] = None,
    ) -> str:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """
    Deterministic, rule-grounded fallback LLM client.
    Generates realistic, faithful culinary answers strictly from StructuredRecipeContext.
    Guarantees 100% offline testability, zero API cost, and high reliability.
    """

    provider_name: str = "mock"
    model_name: str = "deterministic-rule-grounded"
    is_mock: bool = True

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: StructuredRecipeContext,
        task: AssistantTask,
        question: Optional[str] = None,
    ) -> str:
        if task == AssistantTask.EXPLAIN:
            return self._explain(context)
        elif task == AssistantTask.SIMPLIFY:
            return self._simplify(context)
        elif task == AssistantTask.GUIDANCE:
            return self._guidance(context)
        else:
            return self._answer_question(context, question or "")

    def _explain(self, context: StructuredRecipeContext) -> str:
        matched_str = ", ".join(context.matched_ingredients) if context.matched_ingredients else "none"
        missing_count = len(context.missing_ingredients)

        cuisine_clause = ""
        if context.cuisine and context.cuisine.lower() == (context.cuisine_preference_applied or "").lower():
            cuisine_clause = f" It matches your preference for {context.cuisine} cuisine."
        elif context.cuisine:
            cuisine_clause = f" It is identified as {context.cuisine} cuisine."

        diet_clause = ""
        if context.dietary_compatibility:
            diet_clause = f" Dietary compatibility is classified as {context.dietary_compatibility.replace('_', ' ')}."

        time_clause = ""
        if context.estimated_time_minutes:
            time_clause = f" It takes an estimated {context.estimated_time_minutes} minutes to cook."

        missing_clause = ""
        if missing_count > 0:
            if context.substitutions:
                missing_clause = f" You only need {missing_count} additional item(s), with verified substitutions available for on-hand alternatives."
            else:
                missing_clause = f" You need {missing_count} additional ingredient(s) from your grocery store."
        else:
            missing_clause = " You have 100% of the required ingredients ready in your pantry!"

        return (
            f"**{context.title}** was recommended because you have **{len(context.matched_ingredients)} of {len(context.ner)}** "
            f"recipe ingredients on hand ({matched_str}), achieving an **Ingredient Match Score (IMS) of {context.ims:.1f}%** "
            f"and a **Pantry Utilization Score (PUS) of {context.pus:.1f}%** (Final Score: {context.recommendation_score:.1f})."
            f"{cuisine_clause}{diet_clause}{time_clause}{missing_clause}"
        )

    def _simplify(self, context: StructuredRecipeContext) -> str:
        lines = [f"Here is the simplified, step-by-step cooking guide for **{context.title}**:"]
        for idx, step in enumerate(context.directions, 1):
            clean_step = step.strip()
            # Clean step of redundant prefix numbers if present
            clean_step = re.sub(r"^\d+[\.\)]\s*", "", clean_step)
            lines.append(f"{idx}. {clean_step}")

        if context.estimated_time_minutes:
            lines.append(f"\n*Estimated active cooking time: ~{context.estimated_time_minutes} minutes.*")
        return "\n".join(lines)

    def _guidance(self, context: StructuredRecipeContext) -> str:
        matched_str = ", ".join(context.matched_ingredients) if context.matched_ingredients else "staple pantry items"
        lines = [
            f"### Pantry-Aware Preparation & Cooking Sequence for *{context.title}*",
            f"1. **Prep on-hand pantry ingredients first**: Set out your **{matched_str}** so they are measured and ready before cooking.",
        ]

        if context.directions:
            first_step = context.directions[0].strip()
            lines.append(f"2. **Initial cooking action**: Follow Step 1 — {first_step}")

        if context.substitutions:
            lines.append("3. **Incorporate verified substitutions**:")
            for sub in context.substitutions:
                ratio_txt = f" using a {sub['ratio']} ratio" if sub.get("ratio") else ""
                lines.append(
                    f"   - Replace missing *{sub['missing_ingredient']}* with **{sub['substitute']}**{ratio_txt} ({sub['reason']})."
                )
        elif context.missing_ingredients:
            missing_str = ", ".join(context.missing_ingredients)
            lines.append(f"3. **Missing components**: Gather {missing_str} before starting.")

        lines.append("4. **Finishing**: Complete according to the remaining recipe steps and serve hot.")
        return "\n".join(lines)

    def _answer_question(self, context: StructuredRecipeContext, question: str) -> str:
        q_lower = question.lower().strip()
        words = [re.sub(r"[^\w]", "", w) for w in q_lower.split() if w]

        # 1. SUBSTITUTION INQUIRIES
        sub_triggers = [
            "substitute", "substitutes", "substitution", "substitutions",
            "replace", "replacing", "replacement", "swap", "swapping",
            "instead of", "alternative", "without", "omit", "leave out"
        ]
        if any(t in q_lower for t in sub_triggers):
            # A. Check verified substitutions from curated knowledge base
            for sub in context.substitutions:
                missing_ing = sub["missing_ingredient"].lower()
                sub_ing = sub["substitute"].lower()
                if missing_ing in q_lower or sub_ing in q_lower:
                    ratio_info = f" with a ratio of **{sub['ratio']}**" if sub.get("ratio") else ""
                    return (
                        f"Yes, according to our curated knowledge base, you can substitute **{sub['missing_ingredient']}** "
                        f"with **{sub['substitute']}**{ratio_info} (Confidence: {sub['confidence']}). "
                        f"Reason: {sub['reason']}"
                    )

            # B. Negative constraint: check if an ingredient from NER or raw ingredients is mentioned
            for ing in context.ner:
                if ing.lower() in q_lower:
                    return (
                        f"I cannot confirm a reliable culinary substitute for **{ing}** based on our verified knowledge base. "
                        f"Substituting or omitting it may alter the intended flavor, texture, or chemistry of **{context.title}**."
                    )

            # Check raw ingredients for match (e.g. mushrooms, sausage, etc.)
            for raw in context.ingredients:
                for w in re.findall(r"[a-zA-Z]+", raw.lower()):
                    if len(w) > 3 and w in q_lower and w not in ["package", "packages", "tbsp", "teaspoon", "tablespoon", "clove", "cloves", "large", "small", "fresh"]:
                        return (
                            f"I cannot confirm a reliable culinary substitute for **{w}** based on our verified knowledge base. "
                            f"Substituting or omitting it may alter the intended flavor, texture, or chemistry of **{context.title}**."
                        )

            # C. Generic unverified ingredient check (e.g. "Can I substitute apples for mushrooms?")
            stop_words = {"can", "substitute", "replace", "swap", "instead", "without", "recipe", "make", "this", "with", "for", "using", "use", "dish"}
            candidates = [w for w in words if len(w) > 3 and w not in stop_words]
            item_name = candidates[0] if candidates else "this ingredient"
            return (
                f"I cannot confirm a reliable culinary substitute for **{item_name}** based on our verified knowledge base. "
                f"Substituting it may alter the structure or flavor of this recipe."
            )

        # 2. TIME / DURATION INQUIRIES
        time_triggers = ["how long", "time", "duration", "minutes", "prep time", "cook time", "cooking time"]
        if any(t in q_lower for t in time_triggers):
            if context.estimated_time_minutes:
                return (
                    f"The estimated active cooking time for **{context.title}** is **{context.estimated_time_minutes} minutes** "
                    f"(Confidence: {context.time_confidence or 'high'})."
                )
            return f"The recipe directions and metadata for **{context.title}** do not specify an exact active cooking duration."

        # 3. PANTRY & INGREDIENT AVAILABILITY INQUIRIES
        missing_triggers = ["missing", "need to buy", "what do i need", "what am i missing", "lacking", "don't have", "do not have", "need to get"]
        if any(t in q_lower for t in missing_triggers):
            if context.missing_ingredients:
                missing_str = ", ".join(context.missing_ingredients)
                sub_note = ""
                if context.substitutions:
                    verified_subs = [f"{s['missing_ingredient']} (substitute with {s['substitute']})" for s in context.substitutions]
                    sub_note = f" Verified substitutions available in our knowledge base: {', '.join(verified_subs)}."
                return f"For **{context.title}**, you are currently missing {len(context.missing_ingredients)} ingredient(s): **{missing_str}**.{sub_note}"
            return f"You have all required ingredients in your pantry for **{context.title}** (100% Ingredient Match Score)!"

        pantry_triggers = ["pantry", "on hand", "already have", "do i have", "available ingredients", "in my pantry", "have on hand"]
        if any(t in q_lower for t in pantry_triggers):
            for ing in context.ner:
                if ing.lower() in q_lower:
                    if ing in context.matched_ingredients:
                        return f"Yes, **{ing}** is available in your pantry and matches the requirements for **{context.title}**."
                    elif ing in context.missing_ingredients:
                        return f"No, **{ing}** is currently missing from your pantry for **{context.title}**."
            matched_str = ", ".join(context.matched_ingredients) if context.matched_ingredients else "none"
            return (
                f"From your pantry, you have **{len(context.matched_ingredients)} of {len(context.ner)}** ingredients "
                f"on hand for **{context.title}** ({context.ims:.1f}% Match Score): **{matched_str}**."
            )

        # 4. CUISINE & DIETARY INQUIRIES
        if any(t in q_lower for t in ["cuisine", "origin", "style"]):
            return f"**{context.title}** is classified as **{context.cuisine or 'Unclassified'}** cuisine (Confidence: {context.cuisine_confidence or 'None'})."

        if any(t in q_lower for t in ["vegan", "vegetarian", "meat", "dairy", "diet", "dietary"]):
            diet = (context.dietary_compatibility or "standard").replace("_", " ")
            return f"Based on ingredient taxonomy, **{context.title}** is classified as **{diet}** (Confidence: {context.dietary_confidence or 'None'})."

        # 5. STEP / DIRECTION / METHOD / PREPARATION SEQUENCE QUESTIONS
        first_step_triggers = ["first step", "step 1", "start", "begin", "initially"]
        if any(t in q_lower for t in first_step_triggers) and context.directions:
            return f"The initial step for **{context.title}** is:\n- **Step 1**: {context.directions[0]}"

        stop_words = {
            "how", "should", "i", "the", "a", "an", "is", "are", "do", "does", "what", "when", "where",
            "why", "to", "in", "on", "for", "with", "of", "and", "can", "please", "would", "could",
            "about", "this", "that", "there", "these", "those", "you", "your", "we", "our", "me", "my",
            "tell", "explain", "describe", "much", "many"
        }
        q_content_words = [w for w in words if w not in stop_words and len(w) > 2]

        # Extract entities mentioned in query from NER, raw ingredients, or directions
        entities = set(context.ner)
        raw_ingredient_words: Dict[str, List[str]] = {}
        for ing in context.ingredients:
            for w in re.findall(r"[a-zA-Z]+", ing.lower()):
                if len(w) > 3 and w not in stop_words:
                    entities.add(w)
                    raw_ingredient_words.setdefault(w, []).append(ing)

        # Also add direction nouns (e.g. "vegetables", "skillet", "drippings")
        for step in context.directions:
            for w in re.findall(r"[a-zA-Z]+", step.lower()):
                if len(w) > 4 and w not in stop_words:
                    entities.add(w)

        matched_entities = [e for e in entities if e in q_lower]

        has_before = "before" in q_lower
        has_after = "after" in q_lower

        anchor_entity = None
        subject_entity = None
        if has_before:
            parts = q_lower.split("before", 1)
            for e in matched_entities:
                if e in parts[1]:
                    anchor_entity = e
                elif e in parts[0]:
                    subject_entity = e
        elif has_after:
            parts = q_lower.split("after", 1)
            for e in matched_entities:
                if e in parts[1]:
                    anchor_entity = e
                elif e in parts[0]:
                    subject_entity = e

        if not subject_entity and matched_entities:
            subject_entity = matched_entities[0]
            if len(matched_entities) > 1 and not anchor_entity:
                anchor_entity = matched_entities[1]

        # Expand related terms for subject entity (e.g. "sausage" -> "links")
        related_subject_terms = {subject_entity} if subject_entity else set()
        if subject_entity and subject_entity in raw_ingredient_words:
            for raw in raw_ingredient_words[subject_entity]:
                for w in re.findall(r"[a-zA-Z]+", raw.lower()):
                    if len(w) > 3 and w not in stop_words:
                        related_subject_terms.add(w)

        # Find steps mentioning anchor entity
        anchor_steps = []
        if anchor_entity:
            for idx, step in enumerate(context.directions, 1):
                if anchor_entity in step.lower():
                    anchor_steps.append(idx)

        # Score direction steps
        scored_steps = []
        target_anchor = None
        if has_before and anchor_steps:
            adding_steps = [s for s in anchor_steps if any(w in context.directions[s-1].lower() for w in ["add", "toss", "mix", "pour", "combine"])]
            target_anchor = adding_steps[0] if adding_steps else anchor_steps[-1]
        elif has_after and anchor_steps:
            target_anchor = min(anchor_steps)

        for idx, step in enumerate(context.directions, 1):
            step_l = step.lower()
            score = 0

            # Subject matching
            for term in related_subject_terms:
                if term in step_l:
                    score += 12

            # Match content words (verbs, nouns)
            for qw in q_content_words:
                if qw in step_l:
                    score += 4

            # Sequence adjustments
            if has_before and target_anchor:
                if idx < target_anchor and score > 0:
                    score += 10
                elif idx == target_anchor:
                    score += 1
                elif idx > target_anchor:
                    score -= 10
            elif has_after and target_anchor:
                if idx > target_anchor and score > 0:
                    score += 10
                elif idx <= target_anchor:
                    score -= 10

            if score > 0:
                scored_steps.append((idx, score, step))

        scored_steps.sort(key=lambda x: (x[1], -x[0]), reverse=True)

        if scored_steps and scored_steps[0][1] >= 8:
            if has_before and target_anchor:
                before_steps = [s for s in scored_steps if s[0] < target_anchor and s[1] >= 8][:4]
                before_steps.sort(key=lambda x: x[0])
                step_lines = [f"- **Step {s[0]}**: {s[2]}" for s in before_steps]
                intro = f"According to the recipe directions for **{context.title}**, here is how to cook and prepare the **{subject_entity or 'ingredient'}** before adding the **{anchor_entity or 'pasta'}**:"
                outro = f"\nFinally, in **Step {target_anchor}**: {context.directions[target_anchor-1]}"
                return intro + "\n" + "\n".join(step_lines) + outro
            else:
                top_steps = [s for s in scored_steps if s[1] >= 8][:4]
                top_steps.sort(key=lambda x: x[0])
                step_lines = [f"- **Step {s[0]}**: {s[2]}" for s in top_steps]
                if subject_entity:
                    intro = f"According to the recipe directions for **{context.title}**, here is how **{subject_entity}** is used and prepared:"
                else:
                    intro = f"Based on the recipe directions for **{context.title}**, the following steps are relevant to your question:"
                return intro + "\n" + "\n".join(step_lines)

        # 6. UNANSWERABLE / UNVERIFIED QUESTIONS (No Hallucination)
        subject_desc = f"'{question.strip('?.')}'"
        return (
            f"The recipe directions and metadata for **{context.title}** do not contain information regarding {subject_desc}. "
            f"To avoid guessing or providing ungrounded advice, please consult standard culinary guidance or follow the provided directions."
        )


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini API via lightweight HTTP calls."""

    provider_name: str = "gemini"
    is_mock: bool = False

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", temperature: float = 0.2, max_tokens: int = 600):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.fallback = MockLLMClient()

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: StructuredRecipeContext,
        task: AssistantTask,
        question: Optional[str] = None,
    ) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                logger.warning(
                    f"Gemini API returned status {response.status_code}: {response.text}. Falling back to MockLLMClient."
                )
        except Exception as e:
            logger.warning(f"Error calling Gemini API ({e}). Falling back to MockLLMClient.")

        return self.fallback.generate(system_prompt, user_prompt, context, task, question)


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI-compatible chat completion APIs (OpenAI, Groq, Ollama, etc.)."""

    provider_name: str = "openai"
    is_mock: bool = False

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1", temperature: float = 0.2, max_tokens: int = 600):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.fallback = MockLLMClient()

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: StructuredRecipeContext,
        task: AssistantTask,
        question: Optional[str] = None,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "").strip()
                logger.warning(
                    f"OpenAI API returned status {response.status_code}: {response.text}. Falling back to MockLLMClient."
                )
        except Exception as e:
            logger.warning(f"Error calling OpenAI API ({e}). Falling back to MockLLMClient.")

        return self.fallback.generate(system_prompt, user_prompt, context, task, question)


def get_llm_client() -> BaseLLMClient:
    """Factory function instantiating the appropriate LLM client based on configuration."""
    provider = settings.LLM_PROVIDER.lower()
    api_key = settings.LLM_API_KEY.strip()

    if not api_key:
        logger.info("No LLM_API_KEY provided; using deterministic MockLLMClient.")
        return MockLLMClient()

    if provider == "gemini":
        return GeminiClient(
            api_key=api_key,
            model_name=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
    elif provider == "openai":
        return OpenAIClient(
            api_key=api_key,
            model_name=settings.LLM_MODEL,
            base_url=settings.OPENAI_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
    else:
        logger.info(f"Unrecognized provider '{provider}'; falling back to MockLLMClient.")
        return MockLLMClient()
