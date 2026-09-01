import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
FAISS_INDEX_PATH = PROCESSED_DATA_DIR / "recipe_faiss.index"
MAPPING_PATH = PROCESSED_DATA_DIR / "recipe_faiss_mapping.json"


class SemanticVectorRetriever:
    """
    Semantic recipe retrieval using SentenceTransformers and FAISS vector index.
    Loads persisted FAISS index from disk when present or creates in-memory embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.recipe_ids: List[int] = []
        self.embedding_dim = 384
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded SentenceTransformer model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer model {self.model_name}: {e}")
                self.model = None

        # Load persisted FAISS index and recipe mapping if present on disk
        if FAISS_AVAILABLE and FAISS_INDEX_PATH.exists() and MAPPING_PATH.exists():
            try:
                self.index = faiss.read_index(str(FAISS_INDEX_PATH))
                with open(MAPPING_PATH, "r", encoding="utf-8") as f:
                    self.recipe_ids = json.load(f)
                logger.info(f"Successfully loaded persisted FAISS index ({self.index.ntotal} vectors) and mapping ({len(self.recipe_ids)} IDs) from disk.")
            except Exception as e:
                logger.warning(f"Could not load persisted FAISS index: {e}")
                self.index = None

        if self.index is None and FAISS_AVAILABLE:
            try:
                self.index = faiss.IndexFlatIP(self.embedding_dim)
                logger.info("Initialized fresh FAISS IndexFlatIP")
            except Exception as e:
                logger.warning(f"Could not initialize FAISS index: {e}")
                self.index = None

        self._initialized = True

    def encode_text(self, text: str) -> np.ndarray:
        if not self._initialized:
            self.initialize()

        if self.model is not None:
            emb = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
            return emb.astype(np.float32)
        else:
            # Deterministic embedding fallback based on term hashing
            vec = np.zeros(self.embedding_dim, dtype=np.float32)
            words = text.lower().split()
            for word in words:
                idx = abs(hash(word)) % self.embedding_dim
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            return vec

    def index_recipes(self, recipes: List[Dict[str, Any]]):
        if not recipes:
            return

        if not self._initialized:
            self.initialize()

        texts = []
        self.recipe_ids = []

        for r in recipes:
            title = r.get("title", "")
            ner = " ".join(r.get("ner", []))
            cuisine = r.get("cuisine", "")
            doc = f"Title: {title}. Ingredients: {ner}. Cuisine: {cuisine}"
            texts.append(doc)
            self.recipe_ids.append(r.get("id", 0))

        embeddings = []
        for t in texts:
            embeddings.append(self.encode_text(t))

        emb_matrix = np.vstack(embeddings).astype(np.float32)

        if self.index is not None and FAISS_AVAILABLE:
            self.index.reset()
            self.index.add(emb_matrix)
        else:
            self.embeddings_matrix = emb_matrix

        logger.info(f"Indexed {len(self.recipe_ids)} recipes into semantic retriever memory.")

    def retrieve_similar(
        self,
        query: str,
        top_k: int = 50,
        candidates_pool: Optional[List[Dict[str, Any]]] = None,
    ) -> List[int]:
        """
        Retrieves top_k recipe IDs matching the query text semantically using FAISS similarity search.
        """
        if not self._initialized:
            self.initialize()

        if candidates_pool and not self.recipe_ids:
            self.index_recipes(candidates_pool)

        if not self.recipe_ids:
            return []

        query_vec = self.encode_text(query).reshape(1, -1)

        if self.index is not None and FAISS_AVAILABLE and self.index.ntotal > 0:
            k = min(top_k, self.index.ntotal, len(self.recipe_ids))
            distances, indices = self.index.search(query_vec, k)
            retrieved = []
            for idx in indices[0]:
                if 0 <= idx < len(self.recipe_ids):
                    retrieved.append(self.recipe_ids[idx])
            return retrieved
        elif hasattr(self, "embeddings_matrix"):
            sims = np.dot(self.embeddings_matrix, query_vec.T).squeeze()
            top_indices = np.argsort(-sims)[:top_k]
            return [self.recipe_ids[idx] for idx in top_indices]

        return self.recipe_ids[:top_k]


# Global singleton instance
semantic_retriever = SemanticVectorRetriever()
