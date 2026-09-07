"""
scripts/build_index.py

Reads all JSON files from ./data/processed/, embeds each chunk,
and stores them in ChromaDB.

Run from the project root:
    python -m scripts.build_index
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_chroma_collection

load_dotenv()

CACHE_DIR = Path("./data/processed")
BATCH_SIZE = 64


def normalize_chunk(raw: dict, source_stem: str) -> dict:
    """Map the ingester's schema to {id, text, metadata} expected by the retriever."""
    meta_in = raw.get("metadata", {}) or {}

    # For pantry/recipe project: use 'source' from metadata or fallback to filename
    source = meta_in.get("source") or source_stem

    chunk_id = meta_in.get("id", None)
    stable_id = f"{source}_chunk_{chunk_id}" if chunk_id is not None else f"{source_stem}_{hash(raw.get('text',''))}"

    metadata = {"source": source}

    # Carry through any remaining primitive metadata; ChromaDB rejects lists/dicts/None.
    for k, v in meta_in.items():
        if k in metadata or k in {"source"}:
            continue
        if isinstance(v, (str, int, float, bool)):
            metadata[k] = v

    return {
        "id": str(stable_id),
        "text": raw.get("text") or raw.get("content") or "",
        "metadata": metadata,
    }


def load_chunks(cache_dir: Path) -> list[dict]:
    chunks = []
    for json_file in sorted(cache_dir.glob("*.json")):
        print(f"  Reading {json_file.name}...")
        with json_file.open(encoding="utf-8") as f:
            data = json.load(f)
        for raw in data:
            chunks.append(normalize_chunk(raw, json_file.stem.replace("_chunks", "")))
    return chunks


def build_index():
    if not CACHE_DIR.exists():
        print(f"[ERROR] Cache directory '{CACHE_DIR}' does not exist.")
        print("  → First run: python -m src.ingestion.ingest_db_json")
        sys.exit(1)

    print(f"\n📂 Loading chunks from {CACHE_DIR}...")
    chunks = load_chunks(CACHE_DIR)

    if not chunks:
        print(f"[WARN] No chunks found in {CACHE_DIR}. Nothing to index.")
        sys.exit(0)

    print(f"✅ Loaded {len(chunks)} chunks total.\n")

    print("🤖 Loading SentenceTransformer embedder (all-MiniLM-L6-v2)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    print("🗄️  Connecting to ChromaDB...")
    collection = get_chroma_collection()

    # Skip chunks already in the collection (incremental indexing)
    existing_ids = set(collection.get(include=[])["ids"])
    new_chunks = [c for c in chunks if c["id"] not in existing_ids]

    if not new_chunks:
        print("✅ All chunks already indexed. Nothing to do.")
        print(f"   Collection size: {collection.count()} documents")
        return

    print(f"⚡ Embedding {len(new_chunks)} new chunks (batch_size={BATCH_SIZE})...")
    texts = [c["text"] for c in new_chunks]
    embeddings = embedder.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=True)

    ids       = [c["id"]       for c in new_chunks]
    metadatas = [c["metadata"] for c in new_chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )

    print(f"\n✅ Indexed {len(new_chunks)} new chunks.")
    print(f"   Total collection size: {collection.count()} documents")


if __name__ == "__main__":
    build_index()
