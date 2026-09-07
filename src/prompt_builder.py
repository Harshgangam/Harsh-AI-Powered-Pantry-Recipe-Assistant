"""
src/prompt_builder.py

Builds the LLM message list for the Pantry & Recipe Assistant.

Changes from original:
  - System prompt rewritten for a pantry/recipe use-case
  - Removed severity rating (not needed for recipe assistance)
  - Removed page-number citation → replaced with recipe source/ID reference
  - Context excerpts now labelled as "Recipe/Ingredient Excerpt"
"""

SYSTEM_PROMPT = """You are a smart and friendly AI-powered Pantry & Recipe Assistant.
Your job is to help users discover recipes they can cook using the ingredients they have at home.

Rules:
- ONLY use information from the recipe/ingredient context provided below. Do not invent recipes or ingredients.
- If the user asks what they can cook, suggest the most relevant recipes from the context.
- Mention the key ingredients required for each suggestion.
- If the context does not contain a suitable recipe, clearly say so and ask the user to provide more ingredients.
- Keep your response concise, friendly, and easy to read.
- Do NOT mention page numbers. You may reference the recipe name or source if available.
"""

HISTORY_TURN_LIMIT = 8   # Last 4 user/assistant pairs included in context


def build_prompt(
    question: str,
    chunks: list[dict],
    history: list[dict] | None = None,
) -> list[dict]:
    """
    Assembles the full message list for the LLM.

    Parameters
    ----------
    question : Current user query.
    chunks   : Retrieved context chunks [{"text": str, "metadata": dict, "score": float}].
    history  : Optional prior conversation turns.

    Returns
    -------
    list[dict] — OpenAI-style message list ready to pass to the LLM.
    """
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include recent conversation history for multi-turn support
    if history:
        messages.extend(history[-HISTORY_TURN_LIMIT:])

    # Build the context block from retrieved recipe/ingredient chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        chunk_id = meta.get("id", "")
        score = chunk.get("score", "")

        label = f"[Excerpt {i} — Source: {source}"
        if chunk_id != "":
            label += f", ID: {chunk_id}"
        if score != "":
            label += f", Relevance: {score:.2f}"
        label += "]"

        context_parts.append(f"{label}\n{chunk['text']}")

    context_block = "\n\n".join(context_parts)

    user_message = f"""Here are the relevant recipes and ingredients found in your pantry data:

{context_block}

User Question: {question}

Please suggest the best matching recipe(s) or answer the question based only on the above context:"""

    messages.append({"role": "user", "content": user_message})
    return messages
