"""
scripts/ingest_and_index.py

Reads actual project data:
  1. backend/data/pantry_db.json        → pantry items
  2. backend/data/processed/foodkeeper.json → food storage info
  3. backend/data/processed/recipe_metadata.sqlite → recipe metadata
  4. backend/data/processed/recipes.parquet → full recipe text

Converts all to text chunks → saves to data/processed/ → indexes into ChromaDB.

Run from project root:
    python -X utf8 -m scripts.ingest_and_index
"""

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_chroma_collection

# ── Paths ───────────────────────────────────────────────────────────────────
BASE = Path(".")
PANTRY_JSON      = BASE / "backend/data/pantry_db.json"
FOODKEEPER_JSON  = BASE / "backend/data/processed/foodkeeper.json"
RECIPE_META_DB   = BASE / "backend/data/processed/recipe_metadata.sqlite"
RECIPES_PARQUET  = BASE / "backend/data/processed/recipes.parquet"
OUT_DIR          = BASE / "data/processed"

BATCH_SIZE = 64
MAX_RECIPES = 3000   # limit to avoid very long indexing on first run


# ── 1. Pantry items ─────────────────────────────────────────────────────────
def ingest_pantry(path: Path) -> list[dict]:
    chunks = []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    for key, item in data.items():
        name     = item.get("name", "")
        qty      = item.get("quantity", "")
        unit     = item.get("unit", "")
        expiry   = item.get("expiry_date", "")
        risk     = item.get("expiry_risk", "")
        location = item.get("storage_location", "")
        status   = item.get("status", "")

        text = (
            f"Pantry item: {name}. "
            f"Quantity: {qty} {unit}. "
            f"Storage: {location}. "
            f"Expiry: {expiry} (risk: {risk}). "
            f"Status: {status}."
        )
        chunks.append({
            "text": text,
            "metadata": {"source": "pantry_db", "id": key}
        })

    print(f"  [pantry_db.json] → {len(chunks)} chunks")
    return chunks


# ── 2. Foodkeeper storage info ───────────────────────────────────────────────
def ingest_foodkeeper(path: Path) -> list[dict]:
    chunks = []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        sheets = data.get("sheets", [])
        global_counter = 0   # unique across ALL sheets to avoid ID clashes
        for sheet in sheets:
            sheet_name = sheet.get("sheetName", "").replace(" ", "_")
            rows = sheet.get("data", [])
            if not rows:
                continue
            headers = [str(h) for h in rows[0]] if rows else []
            for row in rows[1:]:
                if not any(row):
                    continue
                global_counter += 1
                row_dict = dict(zip(headers, row))
                text = f"Food storage info ({sheet_name}): " + \
                       ". ".join(f"{k}: {v}" for k, v in row_dict.items() if v)
                chunks.append({
                    "text": text,
                    "metadata": {
                        "source": "foodkeeper",
                        "id": f"{sheet_name}_{global_counter}"
                    }
                })
    except Exception as e:
        print(f"  [foodkeeper.json] skipped — {e}")
        return []

    print(f"  [foodkeeper.json] → {len(chunks)} chunks")
    return chunks


# ── 3. Recipe metadata from SQLite ──────────────────────────────────────────
def ingest_recipe_metadata(path: Path) -> list[dict]:
    chunks = []
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM recipe_metadata LIMIT 5000").fetchall()
    conn.close()

    for row in rows:
        d = dict(row)
        rid = d.get("recipe_id", "")
        cuisine = d.get("cuisine") or "unknown"
        dietary = d.get("dietary_compatibility") or ""
        time_m  = d.get("estimated_time_minutes") or ""

        text = (
            f"Recipe ID {rid}: "
            f"Cuisine: {cuisine}. "
            f"Dietary: {dietary}. "
            f"Estimated time: {time_m} minutes."
        )
        chunks.append({
            "text": text,
            "metadata": {"source": "recipe_metadata_sqlite", "id": str(rid)}
        })

    print(f"  [recipe_metadata.sqlite] → {len(chunks)} chunks")
    return chunks


# ── 4. Full recipes from Parquet ────────────────────────────────────────────
def ingest_recipes_parquet(path: Path, limit: int = MAX_RECIPES) -> list[dict]:
    chunks = []
    df = pd.read_parquet(str(path))
    if limit and limit < len(df):
        df = df.iloc[:limit]

    for _, row in df.iterrows():
        rid        = int(row.get("recipe_id", 0))
        title      = str(row.get("title", ""))
        ner        = row.get("ner", [])
        directions = row.get("directions", [])

        ner_str = ", ".join(ner) if isinstance(ner, (list,)) else str(ner)
        dir_str = " ".join(list(directions)[:3]) if isinstance(directions, (list,)) else str(directions)[:200]

        text = (
            f"Recipe: {title}. "
            f"Ingredients: {ner_str}. "
            f"Instructions: {dir_str}"
        )
        chunks.append({
            "text": text,
            "metadata": {"source": "recipes_parquet", "id": str(rid)}
        })

    print(f"  [recipes.parquet] → {len(chunks)} chunks (limit={limit})")
    return chunks


# ── Save chunks to JSON ──────────────────────────────────────────────────────
def save_chunks(chunks: list[dict], out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"  Saved {len(chunks)} chunks → {out_path}")


# ── Index into ChromaDB ──────────────────────────────────────────────────────
CHROMA_MAX_BATCH = 5000   # ChromaDB max batch size limit

def index_chunks(all_chunks: list[dict], embedder: SentenceTransformer, collection):
    existing_ids = set(collection.get(include=[])["ids"])

    seen_ids = set()
    new_chunks = []
    for c in all_chunks:
        src = c["metadata"].get("source", "unknown")
        cid = c["metadata"].get("id", "")
        stable_id = f"{src}__{cid}"
        # Skip if already in ChromaDB OR already seen in this batch
        if stable_id not in existing_ids and stable_id not in seen_ids:
            seen_ids.add(stable_id)
            new_chunks.append({**c, "_stable_id": stable_id})

    if not new_chunks:
        print("  All chunks already indexed!")
        return

    print(f"  Embedding {len(new_chunks)} new chunks...")
    texts = [c["text"] for c in new_chunks]
    embeddings = embedder.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=True)

    # Add to ChromaDB in safe batches (max 5000 per call)
    total = len(new_chunks)
    for start in range(0, total, CHROMA_MAX_BATCH):
        end = min(start + CHROMA_MAX_BATCH, total)
        batch_chunks   = new_chunks[start:end]
        batch_embeddings = embeddings[start:end]
        collection.add(
            ids=[c["_stable_id"] for c in batch_chunks],
            embeddings=batch_embeddings.tolist(),
            documents=[c["text"] for c in batch_chunks],
            metadatas=[c["metadata"] for c in batch_chunks],
        )
        print(f"  Added batch {start}-{end} → Total in DB: {collection.count()}")

    print(f"  Done! Indexed {total} chunks. Total in DB: {collection.count()}")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  Ingesting & Indexing Project Data")
    print("="*55)

    all_chunks = []

    print("\nStep 1: Extracting chunks from data sources...")
    if PANTRY_JSON.exists():
        all_chunks += ingest_pantry(PANTRY_JSON)
    else:
        print(f"  [SKIP] {PANTRY_JSON} not found")

    if FOODKEEPER_JSON.exists():
        all_chunks += ingest_foodkeeper(FOODKEEPER_JSON)
    else:
        print(f"  [SKIP] {FOODKEEPER_JSON} not found")

    if RECIPE_META_DB.exists():
        all_chunks += ingest_recipe_metadata(RECIPE_META_DB)
    else:
        print(f"  [SKIP] {RECIPE_META_DB} not found")

    if RECIPES_PARQUET.exists():
        all_chunks += ingest_recipes_parquet(RECIPES_PARQUET)
    else:
        print(f"  [SKIP] {RECIPES_PARQUET} not found")

    print(f"\nTotal chunks extracted: {len(all_chunks)}")

    print("\nStep 2: Saving chunks to data/processed/all_chunks.json...")
    save_chunks(all_chunks, OUT_DIR / "all_chunks.json")

    print("\nStep 3: Loading embedder...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    print("\nStep 4: Indexing into ChromaDB...")
    collection = get_chroma_collection()
    index_chunks(all_chunks, embedder, collection)

    print("\n" + "="*55)
    print(f"  Done! ChromaDB now has {collection.count()} documents.")
    print("="*55 + "\n")


if __name__ == "__main__":
    main()
