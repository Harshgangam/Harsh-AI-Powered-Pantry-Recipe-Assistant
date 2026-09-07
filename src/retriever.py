"""
src/retriever.py

Retrieval logic for the AI-Powered Pantry & Recipe Assistant.

Uses ChromaDB vector search (cosine similarity) to find the most relevant
recipe/ingredient chunks for a given user query.

Filters available (optional):
  - ingredient_filter : only return chunks where metadata["source"] contains
                        the ingredient name (e.g. "sqlite_recipes").
  - source_filter     : filter by a specific source tag stored in metadata
                        (e.g. "ingredients.json").

No error-code or machine-ID logic is needed for this project.
"""

from typing import Optional
from chromadb import Collection
from sentence_transformers import SentenceTransformer

# ── Tuneable constants ──────────────────────────────────────────────────────
RELEVANCE_THRESHOLD = 0.35   # Minimum cosine similarity to include a chunk
TOP_K = 5                    # Default number of results to return
# ────────────────────────────────────────────────────────────────────────────


def retrieve(
    query: str,
    embedder: SentenceTransformer,
    collection: Collection,
    ingredient_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
    top_k: int = TOP_K,
    history: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Retrieves the most relevant recipe/pantry chunks from ChromaDB for a query.

    Parameters
    ----------
    query            : The user's current question or pantry query.
    embedder         : A loaded SentenceTransformer model.
    collection       : The ChromaDB collection holding indexed chunks.
    ingredient_filter: (Optional) Filter results to chunks from a specific
                       ingredient source table (e.g. "sqlite_ingredients").
    source_filter    : (Optional) Filter results to a specific JSON/DB source
                       filename (e.g. "recipes.json").
    top_k            : Number of top chunks to retrieve before thresholding.
    history          : (Optional) List of previous conversation turns
                       [{"role": "user"/"assistant", "content": "..."}].
                       If provided, the last user message is prepended to the
                       query so that follow-up questions carry prior context.

    Returns
    -------
    List of dicts: [{"text": str, "metadata": dict, "score": float}, ...]
    Only chunks with similarity >= RELEVANCE_THRESHOLD are returned.
    """

    # ── 1. Context-aware query construction ────────────────────────────────
    # Prepend the previous user turn so follow-ups like
    # "how do I cook it?" still retrieve the right recipe.
    retrieval_query = query
    if history:
        last_user = next(
            (t for t in reversed(history) if t.get("role") == "user"), None
        )
        if last_user and last_user.get("content"):
            retrieval_query = f"{last_user['content']} {query}"

    # ── 2. Embed the query ─────────────────────────────────────────────────
    embedding = embedder.encode(retrieval_query).tolist()

    # ── 3. Build optional metadata filter for ChromaDB ────────────────────
    # ChromaDB `where` clause supports only one key at a time with simple ops.
    # If both filters are provided, we prioritise source_filter.
    where = None
    if source_filter:
        where = {"source": source_filter}
    elif ingredient_filter:
        where = {"source": ingredient_filter}

    # ── 4. Vector search ───────────────────────────────────────────────────
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # ── 5. Filter by relevance threshold and format output ─────────────────
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity score in range [0, 1]
        similarity = 1 - (dist / 2)

        if similarity >= RELEVANCE_THRESHOLD:
            chunks.append({
                "text": doc,
                "metadata": meta,
                "score": round(similarity, 4),
            })

    return chunks
