import time
from typing import List
from backend.app.config import settings
from backend.app.recommendation.engine import RecommendationEngine
from backend.app.recommendation.normalizer import normalize_pantry_list


def run_benchmark():
    print("=" * 70)
    print("MILESTONE 2: RECOMMENDATION ENGINE PERFORMANCE BENCHMARK")
    print("=" * 70)
    print(f"SQLite Index: {settings.SQLITE_INDEX_PATH}")
    print(f"Parquet Data: {settings.PARQUET_PATH}")
    print("-" * 70)

    engine = RecommendationEngine(
        sqlite_path=settings.SQLITE_INDEX_PATH,
        parquet_path=settings.PARQUET_PATH,
        ims_weight=settings.IMS_WEIGHT,
        pus_weight=settings.PUS_WEIGHT,
        candidate_limit=settings.CANDIDATE_POOL_LIMIT,
    )

    pantry_scenarios = [
        ("3 Ingredients (Common)", ["garlic", "onion", "butter"]),
        ("5 Ingredients (Dinner)", ["chicken breasts", "garlic", "sour cream", "butter", "pasta"]),
        ("10 Ingredients (Full Pantry)", [
            "tomato", "garlic", "onion", "basil", "olive oil",
            "pasta", "cheese", "chicken", "black pepper", "salt"
        ]),
    ]

    results = []

    for label, pantry in pantry_scenarios:
        t_start = time.perf_counter()
        
        # 1. Normalization
        t0 = time.perf_counter()
        norm_pantry, variants = normalize_pantry_list(pantry)
        t_norm = time.perf_counter()

        # 2. Candidate retrieval
        candidates = engine.retriever.retrieve_candidate_ids(variants, limit=settings.CANDIDATE_POOL_LIMIT)
        t_candidates = time.perf_counter()

        # 3. Details and scoring
        response = engine.recommend(pantry, limit=10)
        t_end = time.perf_counter()

        total_time_ms = (t_end - t_start) * 1000.0
        candidate_time_ms = (t_candidates - t_norm) * 1000.0
        scoring_time_ms = total_time_ms - candidate_time_ms

        print(f"\nScenario: {label}")
        print(f"  Pantry: {pantry}")
        print(f"  Normalized Pantry ({len(response.normalized_pantry)} items): {response.normalized_pantry}")
        print(f"  Relevant Pantry ({len(response.relevant_pantry)} items):   {response.relevant_pantry}")
        print(f"  Candidates Evaluated: {response.total_candidates_evaluated}")
        print(f"  Recommendations Returned: {len(response.recommendations)}")
        print(f"  --- Latency Breakdown ---")
        print(f"  Total Request Time:     {total_time_ms:7.2f} ms ({total_time_ms/1000:.3f} s)")
        print(f"  Candidate Retrieval:    {candidate_time_ms:7.2f} ms")
        print(f"  Detail & Scoring:       {scoring_time_ms:7.2f} ms")

        if response.recommendations:
            top = response.recommendations[0]
            print(f"  Top Match:")
            print(f"    - Title: \"{top.title}\" (ID: {top.recipe_id})")
            print(f"    - IMS: {top.ims:.1f}% | PUS: {top.pus:.1f}% | Final Score: {top.recommendation_score:.1f}")
            print(f"    - Matched: {top.matched_ingredients}")
            print(f"    - Missing: {top.missing_ingredients}")
            print(f"    - Explanation: \"{top.explanation}\"")

        results.append({
            "scenario": label,
            "pantry_size": len(pantry),
            "candidates": response.total_candidates_evaluated,
            "total_ms": round(total_time_ms, 2),
            "candidate_ms": round(candidate_time_ms, 2),
            "scoring_ms": round(scoring_time_ms, 2),
        })

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Scenario':<30} | {'Pantry':<6} | {'Candidates':<10} | {'Total Time':<12}")
    print("-" * 70)
    for r in results:
        print(f"{r['scenario']:<30} | {r['pantry_size']:<6} | {r['candidates']:<10} | {r['total_ms']:7.2f} ms")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
