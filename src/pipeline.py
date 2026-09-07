"""
src/pipeline.py

Main query pipeline for the AI-Powered Pantry & Recipe Assistant.

Flow:
  1. Retrieve relevant recipe/ingredient chunks from ChromaDB (via retriever.py)
  2. Build the LLM prompt with context + conversation history (via prompt_builder.py)
  3. Call the LLM (Groq) and return the structured answer (via llm_client.py)

Removed from original:
  - machine_filter       → replaced with ingredient_filter / source_filter
  - SEVERITY rating      → not relevant for a recipe/pantry assistant
  - Page number citation → replaced with recipe source/id citation
"""

from typing import Optional
from chromadb import Collection
from sentence_transformers import SentenceTransformer

from .retriever import retrieve
from .prompt_builder import build_prompt
from .llm_client import call_llm

NOT_FOUND_ANSWER = (
    "I could not find any matching recipes or ingredients in your pantry data. "
    "Try rephrasing your query or adding more ingredients."
)
ERROR_ANSWER = "Recipe assistant is temporarily unavailable. Please try again shortly."


def run_query(
    question: str,
    embedder: SentenceTransformer,
    collection: Collection,
    ingredient_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
    history: Optional[list[dict]] = None,
) -> dict:
    """
    Runs the full RAG pipeline for a pantry/recipe question.

    Parameters
    ----------
    question          : User's natural language query (e.g. "What can I cook with eggs and tomatoes?")
    embedder          : Loaded SentenceTransformer model.
    collection        : ChromaDB collection with indexed recipe/ingredient chunks.
    ingredient_filter : (Optional) Restrict search to a specific ingredient source
                        (e.g. "sqlite_ingredients").
    source_filter     : (Optional) Restrict search to a specific file source
                        (e.g. "recipes.json").
    history           : (Optional) Previous conversation turns for multi-turn support.

    Returns
    -------
    dict with keys:
        status  : "success" | "not_found" | "error"
        answer  : LLM-generated answer string
        sources : list of {"source": str, "id": str/int} from matched chunks
    """

    # Step 1: Retrieve relevant chunks
    chunks = retrieve(
        query=question,
        embedder=embedder,
        collection=collection,
        ingredient_filter=ingredient_filter,
        source_filter=source_filter,
        history=history,
    )

    if not chunks:
        return {
            "status": "not_found",
            "answer": NOT_FOUND_ANSWER,
            "sources": [],
        }

    # Step 2: Build the prompt with context and history
    messages = build_prompt(question, chunks, history=history)

    # Step 3: Call LLM
    try:
        answer = call_llm(messages)
    except RuntimeError:
        return {
            "status": "error",
            "answer": ERROR_ANSWER,
            "sources": [],
        }

    # Step 4: Extract source references from chunk metadata
    sources = [
        {
            "source": c["metadata"].get("source", "unknown"),
            "id": c["metadata"].get("id", ""),
        }
        for c in chunks
    ]

    return {
        "status": "success",
        "answer": answer,
        "sources": sources,
    }
