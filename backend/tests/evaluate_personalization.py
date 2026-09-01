from dataclasses import dataclass
import time
from typing import Any, Dict, List, Optional

from backend.app.config import settings
from backend.app.models.recommendation import RecommendationResponse
from backend.app.recommendation.engine import RecommendationEngine


@dataclass
class QueryBenchmark:
    name: str
    pantry: List[str]
    cuisine: Optional[str] = None
    dietary_preference: Optional[str] = None
    max_cooking_time_minutes: Optional[int] = None
    limit: int = 10


TEST_QUERIES = [
    QueryBenchmark(
        name="Italian Pasta Dinner",
        pantry=["pasta", "tomato", "garlic", "basil", "olive oil"],
        cuisine="Italian",
        max_cooking_time_minutes=30,
        limit=5,
    ),
    QueryBenchmark(
        name="Indian Spiced Rice & Curry",
        pantry=["rice", "chicken", "onion", "garlic", "ginger", "curry powder"],
        cuisine="Indian",
        max_cooking_time_minutes=45,
        limit=5,
    ),
    QueryBenchmark(
        name="Vegetarian Mexican Night",
        pantry=["tortillas", "black beans", "salsa", "cheddar cheese", "chicken breasts", "jalapeno"],
        cuisine="Mexican",
        dietary_preference="vegetarian",
        max_cooking_time_minutes=40,
        limit=5,
    ),
    QueryBenchmark(
        name="Quick Vegan Stir-Fry",
        pantry=["soy sauce", "sesame oil", "garlic", "ginger", "broccoli", "rice", "butter", "egg"],
        dietary_preference="vegan",
        max_cooking_time_minutes=25,
        limit=5,
    ),
    QueryBenchmark(
        name="American Comfort Dinner",
        pantry=["beef", "potato", "onion", "carrot", "butter", "ground beef"],
        cuisine="American",
        max_cooking_time_minutes=60,
        limit=5,
    ),
]


def run_evaluation():
    print("=" * 80)
    print("PERSONALIZATION LAYER EVALUATION: BASELINE VS PERSONALIZED")
    print(f"Parquet Path:  {settings.PARQUET_PATH}")
    print(f"Index SQLite:  {settings.SQLITE_INDEX_PATH}")
    print(f"Meta SQLite:   {settings.METADATA_DB_PATH}")
    print("=" * 80)

    engine = RecommendationEngine()

    total_baseline_time = 0.0
    total_personalized_time = 0.0

    all_results = []

    for q_idx, q in enumerate(TEST_QUERIES, start=1):
        print(f"\n--- [Query {q_idx}/{len(TEST_QUERIES)}] {q.name} ---")
        print(f"Pantry: {q.pantry}")
        prefs_desc = []
        if q.cuisine:
            prefs_desc.append(f"Cuisine='{q.cuisine}'")
        if q.dietary_preference:
            prefs_desc.append(f"Dietary='{q.dietary_preference}'")
        if q.max_cooking_time_minutes:
            prefs_desc.append(f"MaxTime={q.max_cooking_time_minutes}m")
        print(f"Preferences: {', '.join(prefs_desc) if prefs_desc else 'None'}")

        # 1. Baseline Run (Pantry only: IMS + PUS)
        t0 = time.perf_counter()
        base_resp: RecommendationResponse = engine.recommend(
            pantry_ingredients=q.pantry,
            limit=q.limit,
        )
        t_base = time.perf_counter() - t0
        total_baseline_time += t_base

        # 2. Personalized Run (Pantry + Preferences)
        t1 = time.perf_counter()
        pers_resp: RecommendationResponse = engine.recommend(
            pantry_ingredients=q.pantry,
            limit=q.limit,
            cuisine=q.cuisine,
            dietary_preference=q.dietary_preference,
            max_cooking_time_minutes=q.max_cooking_time_minutes,
        )
        t_pers = time.perf_counter() - t1
        total_personalized_time += t_pers

        # 3. Analyze Comparison Metrics
        base_ids = [r.recipe_id for r in base_resp.recommendations]
        pers_ids = [r.recipe_id for r in pers_resp.recommendations]

        # Top-K overlap
        common_ids = set(base_ids).intersection(set(pers_ids))
        overlap_pct = (len(common_ids) / len(base_ids) * 100.0) if base_ids else 0.0

        # Preference satisfaction in Personalized recommendations
        cuisine_matches = 0
        dietary_satisfactions = 0
        time_satisfactions = 0
        unknown_cuisine_count = 0
        unknown_time_count = 0

        for r in pers_resp.recommendations:
            if q.cuisine:
                if r.cuisine and r.cuisine.lower() == q.cuisine.lower():
                    cuisine_matches += 1
                elif r.cuisine is None:
                    unknown_cuisine_count += 1

            if q.dietary_preference:
                if q.dietary_preference == "vegetarian" and r.dietary_compatibility in ("vegetarian_compatible", "vegan_compatible"):
                    dietary_satisfactions += 1
                elif q.dietary_preference == "vegan" and r.dietary_compatibility == "vegan_compatible":
                    dietary_satisfactions += 1

            if q.max_cooking_time_minutes:
                if r.estimated_time_minutes is not None and r.estimated_time_minutes <= q.max_cooking_time_minutes:
                    time_satisfactions += 1
                elif r.estimated_time_minutes is None:
                    unknown_time_count += 1

        n_pers = len(pers_resp.recommendations)
        cuisine_match_rate = (cuisine_matches / n_pers * 100.0) if (n_pers and q.cuisine) else None
        diet_satisfaction_rate = (dietary_satisfactions / n_pers * 100.0) if (n_pers and q.dietary_preference) else None
        time_satisfaction_rate = (time_satisfactions / n_pers * 100.0) if (n_pers and q.max_cooking_time_minutes) else None

        print(f"Latency: Baseline = {t_base:.3f}s | Personalized = {t_pers:.3f}s")
        print(f"Candidates Evaluated: {pers_resp.total_candidates_evaluated}")
        print(f"Top-{q.limit} Recipe Overlap with Baseline: {overlap_pct:.1f}% ({len(common_ids)}/{len(base_ids)})")

        if cuisine_match_rate is not None:
            print(f"Cuisine Match Rate: {cuisine_match_rate:.1f}% ({cuisine_matches}/{n_pers}) | Unknown Cuisine: {unknown_cuisine_count}")
        if diet_satisfaction_rate is not None:
            print(f"Dietary Constraint Satisfaction: {diet_satisfaction_rate:.1f}% ({dietary_satisfactions}/{n_pers}) [Strict Exclusion]")
        if time_satisfaction_rate is not None:
            print(f"Cooking Time Satisfaction (<= {q.max_cooking_time_minutes}m): {time_satisfaction_rate:.1f}% ({time_satisfactions}/{n_pers}) | Unknown Time: {unknown_time_count}")

        print("\nTop 3 Personalized Results:")
        for rank, r in enumerate(pers_resp.recommendations[:3], start=1):
            print(
                f"  #{rank} [{r.recipe_id}] {r.title:<35} | "
                f"Score={r.recommendation_score:5.1f} (Base={r.explanation_data.base_score:5.1f}, IMS={r.ims:4.1f}%, PUS={r.pus:4.1f}%) | "
                f"Cuisine={r.cuisine or 'Unknown':<10} | Diet={r.dietary_compatibility or 'Unknown':<20} | "
                f"Time={str(r.estimated_time_minutes)+'m' if r.estimated_time_minutes else 'Unknown':<7}"
            )

        all_results.append({
            "query": q.name,
            "t_base": t_base,
            "t_pers": t_pers,
            "overlap_pct": overlap_pct,
            "cuisine_match_rate": cuisine_match_rate,
            "diet_satisfaction_rate": diet_satisfaction_rate,
            "time_satisfaction_rate": time_satisfaction_rate,
            "unknown_cuisine": unknown_cuisine_count,
            "unknown_time": unknown_time_count,
        })

    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY ACROSS ALL QUERIES")
    print("=" * 80)
    print(f"Average Baseline Latency:     {total_baseline_time / len(TEST_QUERIES):.3f}s")
    print(f"Average Personalized Latency: {total_personalized_time / len(TEST_QUERIES):.3f}s")
    avg_overlap = sum(r["overlap_pct"] for r in all_results) / len(all_results)
    print(f"Average Top-K Rank Overlap:   {avg_overlap:.1f}% (demonstrating meaningful preference-guided reranking)")
    print("=" * 80)


if __name__ == "__main__":
    run_evaluation()
