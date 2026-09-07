"""
test_pipeline.py

Quick end-to-end test for the full RAG pipeline.
Run from the project root:
    python test_pipeline.py

Tests:
  1. ChromaDB connection
  2. SentenceTransformer loading
  3. Groq LLM connection
  4. Full pipeline query (if collection has data)
"""

import sys
import io
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*55)
print("  Pantry & Recipe Assistant — Pipeline Test")
print("="*55)

# ── Test 1: ChromaDB ────────────────────────────────────────
print("\n[1/4] Testing ChromaDB connection...")
try:
    from src.db import get_chroma_collection
    collection = get_chroma_collection()
    count = collection.count()
    print(f"  ✅ ChromaDB OK — Collection 'pantry_recipes' has {count} documents")
except Exception as e:
    print(f"  ❌ ChromaDB FAILED: {e}")
    sys.exit(1)

# ── Test 2: SentenceTransformer ────────────────────────────
print("\n[2/4] Loading SentenceTransformer embedder...")
try:
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    test_emb = embedder.encode("test query")
    print(f"  ✅ Embedder OK — Vector dimension: {len(test_emb)}")
except Exception as e:
    print(f"  ❌ Embedder FAILED: {e}")
    sys.exit(1)

# ── Test 3: Groq LLM ────────────────────────────────────────
print("\n[3/4] Testing Groq LLM connection...")
try:
    from src.llm_client import call_llm
    response = call_llm([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "Say 'Groq is working!' in one line."},
    ])
    print(f"  ✅ Groq OK — Response: {response[:80]}")
except Exception as e:
    print(f"  ❌ Groq FAILED: {e}")
    sys.exit(1)

# ── Test 4: Full Pipeline ───────────────────────────────────
print("\n[4/4] Running full pipeline query...")
if count == 0:
    print("  ⚠️  Skipped — No documents in ChromaDB yet.")
    print("     → Run: python -m scripts.build_index  (after ingesting data)")
else:
    try:
        from src.pipeline import run_query
        result = run_query(
            question="What can I cook with eggs and tomatoes?",
            embedder=embedder,
            collection=collection,
        )
        print(f"  ✅ Pipeline OK — Status: {result['status']}")
        print(f"     Answer preview: {result['answer'][:120]}...")
        print(f"     Sources found: {len(result['sources'])}")
    except Exception as e:
        print(f"  ❌ Pipeline FAILED: {e}")
        sys.exit(1)

print("\n" + "="*55)
print("  All tests passed! ✅ Pipeline is ready.")
print("="*55 + "\n")
