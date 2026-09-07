import json
import logging
import time
from pathlib import Path
import numpy as np
from src.ingestion.ingest_db_json import get_all_chunks

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
PROCESSED_DATA_DIR = BASE_DIR / "backend" / "data" / "processed"
FAISS_INDEX_PATH = PROCESSED_DATA_DIR / "recipe_faiss.index"
MAPPING_PATH = PROCESSED_DATA_DIR / "recipe_faiss_mapping.json"

def build_faiss_from_chunks(db_configs=None, json_files=None, model_name="all-MiniLM-L6-v2"):
    """
    Reads data using the new ingestion script, generates embeddings,
    and builds the .index (FAISS) file.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    
    logger.info("Extracting data chunks from DB/JSON...")
    chunks = get_all_chunks(db_configs=db_configs, json_files=json_files)
    
    if not chunks:
        logger.warning("No chunks found. Exiting.")
        return False
        
    logger.info(f"Loaded {len(chunks)} chunks for vector index creation.")

    documents = []
    chunk_ids = []

    for i, chunk in enumerate(chunks):
        # We use the text directly, or you can format it further if needed
        documents.append(chunk["text"])
        # Use ID from metadata if available, else use index
        cid = chunk.get("metadata", {}).get("id", i)
        chunk_ids.append(cid)

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
        json.dump(chunk_ids, f)

    logger.info(f"Persisted ID mapping to {MAPPING_PATH}")
    elapsed = time.time() - start_time
    logger.info(f"FAISS index build complete in {elapsed:.2f} seconds!")
    return True

if __name__ == "__main__":
    # Update with your actual database and JSON paths
    sample_db = [{"db_path": "path/to/your/database.db", "table_name": "recipes"}]
    sample_json = ["path/to/your/data.json"]
    build_faiss_from_chunks(db_configs=sample_db, json_files=sample_json)
