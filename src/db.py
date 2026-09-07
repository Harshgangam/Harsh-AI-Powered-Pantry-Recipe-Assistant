"""
src/db.py

ChromaDB client setup for the AI-Powered Pantry & Recipe Assistant.

Usage:
    from src.db import get_chroma_collection
    collection = get_chroma_collection()

Environment variables (set in .env):
    CHROMA_DB_PATH      : Folder where ChromaDB stores data on disk.
                          Default: ./data/chroma_db
    CHROMA_COLLECTION   : Name of the collection inside ChromaDB.
                          Default: pantry_recipes
"""

import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb import Collection
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

# ── Config (override via .env) ──────────────────────────────────────────────
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "pantry_recipes")
# ────────────────────────────────────────────────────────────────────────────

_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Returns a singleton persistent ChromaDB client.
    Data is saved to disk at CHROMA_DB_PATH so it survives restarts.
    """
    global _client
    if _client is None:
        db_path = Path(CHROMA_DB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_chroma_collection() -> Collection:
    """
    Returns (or creates) the ChromaDB collection for pantry/recipe chunks.

    The collection uses cosine similarity — matching how sentence-transformers
    embeddings are normalised and compared.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},   # cosine similarity search
    )
    return collection


def reset_collection() -> Collection:
    """
    Deletes and recreates the collection from scratch.
    Use this when re-indexing all data (e.g. after updating your DB/JSON).
    """
    client = get_chroma_client()
    try:
        client.delete_collection(CHROMA_COLLECTION)
        print(f"Deleted existing collection: '{CHROMA_COLLECTION}'")
    except Exception:
        pass   # collection didn't exist yet, that's fine
    return get_chroma_collection()


if __name__ == "__main__":
    col = get_chroma_collection()
    print(f"Collection '{CHROMA_COLLECTION}' ready. Documents indexed: {col.count()}")
