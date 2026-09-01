import json
import logging
import time
from pathlib import Path
import numpy as np
import pandas as pd

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
PARQUET_PATH = PROCESSED_DATA_DIR / "recipes.parquet"
FAISS_INDEX_PATH = PROCESSED_DATA_DIR / "recipe_faiss.index"
MAPPING_PATH = PROCESSED_DATA_DIR / "recipe_faiss_mapping.json"


def build_and_persist_faiss_index(limit: int = 5000, model_name: str = "all-MiniLM-L6-v2"):
    """
    Loads recipes from Parquet, constructs rich searchable text representations,
    generates dense vector embeddings via SentenceTransformer, and persists
    the FAISS index to disk alongside the recipe ID mapping.
    """
    start_time = time.time()
    logger.info(f"Starting FAISS index build from {PARQUET_PATH}...")

    if not PARQUET_PATH.exists():
        logger.error(f"Parquet file not found at {PARQUET_PATH}")
        return False

    df = pd.read_parquet(PARQUET_PATH)
    if limit and limit < len(df):
        df = df.iloc[:limit]

    logger.info(f"Loaded {len(df)} recipe records for vector index creation.")

    recipe_ids = []
    documents = []

    for idx, row in df.iterrows():
        r_id = int(row.get("recipe_id", idx))
        title = str(row.get("title", ""))
        ner = row.get("ner", [])
        ner_str = " ".join(ner) if isinstance(ner, (list, np.ndarray)) else str(ner)
        directions = row.get("directions", [])
        dir_str = " ".join(directions[:3]) if isinstance(directions, (list, np.ndarray)) else str(directions)[:150]

        doc_text = f"Title: {title}. Ingredients: {ner_str}. Directions: {dir_str}"
        recipe_ids.append(r_id)
        documents.append(doc_text)

    embedding_dim = 384

    if SENTENCE_TRANSFORMERS_AVAILABLE:
        logger.info(f"Encoding {len(documents)} documents using SentenceTransformer('{model_name}')...")
        model = SentenceTransformer(model_name)
        embeddings = model.encode(documents, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)
        embeddings = embeddings.astype(np.float32)
    else:
        logger.warning("SentenceTransformers not installed. Generating term hash embedding fallback.")
        embeddings = np.zeros((len(documents), embedding_dim), dtype=np.float32)
        for i, doc in enumerate(documents):
            for word in doc.lower().split():
                h_idx = abs(hash(word)) % embedding_dim
                embeddings[i, h_idx] += 1.0
            norm = np.linalg.norm(embeddings[i])
            if norm > 0:
                embeddings[i] /= norm

    if FAISS_AVAILABLE:
        logger.info(f"Building FAISS IndexFlatIP with dimension {embedding_dim}...")
        index = faiss.IndexFlatIP(embedding_dim)
        index.add(embeddings)
        faiss.write_index(index, str(FAISS_INDEX_PATH))
        logger.info(f"Persisted FAISS index to {FAISS_INDEX_PATH}")
    else:
        logger.warning("FAISS library not available. Saving raw numpy embedding matrix.")
        np.save(str(PROCESSED_DATA_DIR / "recipe_embeddings.npy"), embeddings)

    with open(MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(recipe_ids, f)

    logger.info(f"Persisted recipe ID mapping ({len(recipe_ids)} IDs) to {MAPPING_PATH}")
    elapsed = time.time() - start_time
    logger.info(f"FAISS index build complete in {elapsed:.2f} seconds!")
    return True


if __name__ == "__main__":
    build_and_persist_faiss_index()
