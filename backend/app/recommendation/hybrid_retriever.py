import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from backend.app.config import settings
from backend.app.recommendation.retriever import RecipeRetriever
from backend.app.recommendation.vector_retriever import semantic_retriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid Retrieval Layer combining FAISS vector similarity search (SentenceTransformers)
    with SQLite structured inverted index filtering.
    """

    def __init__(
        self,
        sqlite_path: Path = settings.SQLITE_INDEX_PATH,
        parquet_path: Path = settings.PARQUET_PATH,
        metadata_path: Optional[Path] = settings.METADATA_DB_PATH,
    ):
        self.sqlite_retriever = RecipeRetriever(sqlite_path, parquet_path, metadata_path)
        self.vector_retriever = semantic_retriever

    def retrieve_candidates(
        self,
        pantry_variants: Set[str],
        query_text: Optional[str] = None,
        limit: int = settings.CANDIDATE_POOL_LIMIT,
    ) -> Tuple[List[int], Dict[int, Dict[str, Any]], Dict[int, Dict[str, Any]]]:
        """
        Executes hybrid retrieval:
        1. Queries SQLite inverted index for exact pantry ingredient matches.
        2. Queries FAISS vector index using query_text semantic embedding.
        3. Fuses both candidate pools seamlessly.
        4. Fetches Parquet details & SQLite metadata.
        """
        structured_tuples = self.sqlite_retriever.retrieve_candidate_ids(
            pantry_variants=pantry_variants,
            limit=limit,
        )
        structured_ids = [t[0] for t in structured_tuples]

        semantic_ids = []
        if query_text and query_text.strip():
            try:
                semantic_ids = self.vector_retriever.retrieve_similar(
                    query=query_text,
                    top_k=limit,
                )
            except Exception as e:
                logger.warning(f"Semantic vector retrieval error: {e}")

        # Combine structured (SQLite) and semantic (FAISS) candidates
        seen = set()
        candidate_ids = []

        for st_id in structured_ids:
            if st_id not in seen:
                seen.add(st_id)
                candidate_ids.append(st_id)

        for s_id in semantic_ids:
            if s_id not in seen:
                seen.add(s_id)
                candidate_ids.append(s_id)

        if not candidate_ids:
            return [], {}, {}

        candidate_ids = candidate_ids[:limit]

        # Batch fetch details and metadata
        details_map = self.sqlite_retriever.fetch_recipe_details(candidate_ids)
        metadata_map = self.sqlite_retriever.fetch_recipe_metadata(candidate_ids)

        return candidate_ids, details_map, metadata_map


# Global hybrid retriever instance
hybrid_retriever = HybridRetriever()
