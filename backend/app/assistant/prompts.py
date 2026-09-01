from typing import Optional
from backend.app.assistant.models import AssistantTask

SYSTEM_GROUNDING_PROMPT = """You are the AI Recipe Assistant for the "AI-Powered Pantry Recipe Assistant" application.
Your mission is to provide clear, helpful, and 100% grounded culinary guidance strictly based on the provided RECIPE CONTEXT.

CRITICAL OPERATIONAL RULES:
1. EXCLUSIVE SOURCE MATERIAL: Answer ONLY using information explicitly present in the provided RECIPE CONTEXT, PANTRY MATCH, and CURATED KNOWLEDGE BASE SUBSTITUTIONS.
2. NO INVENTED INGREDIENTS: Never introduce ingredients that do not appear in the recipe, the user's pantry, or the curated substitutions.
3. NO INVENTED SUBSTITUTIONS:
   - If the user asks about substituting an ingredient and a substitution is listed in CURATED KNOWLEDGE BASE SUBSTITUTIONS, provide that verified substitute, ratio, and reason.
   - If the user asks about substituting an ingredient that is NOT in the curated substitutions, you MUST explicitly state:
     "I cannot confirm a reliable culinary substitute for [ingredient] based on our verified knowledge base. Substituting it may alter the structure or flavor of this recipe."
   - NEVER invent, guess, or assume a culinary substitute.
4. NO INVENTED TIMES OR TEMPERATURES: Use only cooking times and temperatures stated in the directions or metadata. If unspecified, explicitly state that the recipe directions do not specify them.
5. NO DIETARY FABRICATIONS: Never claim a recipe is vegetarian or vegan unless the DIETARY COMPATIBILITY in the context explicitly says so.
6. NO SCORING ALTERATIONS: Do not alter or question the Ingredient Match Score (IMS), Pantry Utilization Score (PUS), or Recommendation Score calculated by the deterministic engine.
7. CONCISE & PRACTICAL: Keep responses focused, encouraging, and structured using clean markdown bullet points where appropriate.
"""


def build_user_prompt(
    context_str: str,
    task: AssistantTask,
    question: Optional[str] = None,
) -> str:
    """
    Constructs the task-specific user prompt incorporating the assembled structured context.
    """
    lines = [context_str, "\n=== USER REQUEST ==="]

    if task == AssistantTask.EXPLAIN:
        lines.append("Task: Explain why this recipe was recommended for my pantry.")
        lines.append(
            "Instructions: Clearly explain in 2-3 sentences how my available pantry ingredients, "
            "the Ingredient Match Score (IMS), Pantry Utilization Score (PUS), and any active personalization "
            "(cuisine bonus, dietary compatibility, cooking time limit) contributed to this recommendation."
        )

    elif task == AssistantTask.SIMPLIFY:
        lines.append("Task: Simplify the cooking instructions for a beginner.")
        lines.append(
            "Instructions: Rewrite the cooking directions into numbered, clear, step-by-step instructions. "
            "Preserve all original culinary actions, temperatures, and timings faithfully, but remove confusing jargon."
        )

    elif task == AssistantTask.GUIDANCE:
        lines.append("Task: Provide pantry-aware preparation and cooking guidance.")
        lines.append(
            "Instructions: Tell me what on-hand pantry ingredients to prepare first, how to sequence the cooking process, "
            "and clearly indicate where missing ingredients or curated substitutions should be incorporated."
        )

    elif task == AssistantTask.QUESTION:
        user_q = question or "Can I make this recipe with my current ingredients?"
        lines.append(f"User Question: {user_q}")
        lines.append(
            "Instructions: Answer the question directly using ONLY the provided recipe context and curated substitutions.\n"
            "- For questions regarding cooking steps, ingredient preparation, cooking methods, or step sequence, directly cite the relevant step numbers and instructions from COOKING DIRECTIONS.\n"
            "- For questions regarding active cooking time, cite the verified estimated cooking time if present.\n"
            "- For questions regarding pantry availability or missing ingredients, reference the PANTRY MATCH and MISSING INGREDIENTS.\n"
            "- If the question asks about substituting an ingredient that is not in the curated substitutions, explicitly state that no verified substitute is available in the knowledge base.\n"
            "- If the question asks about information completely absent from the recipe context, state transparently that the recipe does not specify this information rather than guessing."
        )

    return "\n".join(lines)
