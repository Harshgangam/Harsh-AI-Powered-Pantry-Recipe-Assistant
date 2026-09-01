"""
Evaluation Script for Milestone 6: AI-Assisted Grounded Recipe Guidance & Structured RAG Layer.
Evaluates groundedness, refusal of unverified substitutions, and response latency.
"""
import time
from typing import Dict, List

from backend.app.assistant.models import AssistantRequest, AssistantTask
from backend.app.assistant.service import assistant_service


EVALUATION_QUERIES = [
    {
        "id": 1,
        "name": "Explain recommendation for Italian pasta",
        "recipe_id": 1316605,
        "task": AssistantTask.EXPLAIN,
        "question": None,
        "pantry": ["pasta", "garlic", "olive oil"],
        "cuisine": "Italian",
        "expected_substrings": ["Ingredient Match Score", "Pantry Utilization Score", "Bowtie"],
        "must_not_contain": ["invented", "hallucination"],
    },
    {
        "id": 2,
        "name": "Simplify directions into numbered steps",
        "recipe_id": 1316605,
        "task": AssistantTask.SIMPLIFY,
        "question": None,
        "pantry": ["pasta", "garlic", "olive oil"],
        "cuisine": "Italian",
        "expected_substrings": ["1.", "2."],
        "must_not_contain": ["flambé", "sous-vide"],
    },
    {
        "id": 3,
        "name": "Pantry-aware cooking guidance",
        "recipe_id": 1316605,
        "task": AssistantTask.GUIDANCE,
        "question": None,
        "pantry": ["pasta", "garlic", "olive oil"],
        "cuisine": "Italian",
        "expected_substrings": ["pantry", "prep"],
        "must_not_contain": [],
    },
    {
        "id": 4,
        "name": "Verified substitution inquiry (basil -> dried basil)",
        "recipe_id": 1316605,
        "task": AssistantTask.QUESTION,
        "question": "Can I substitute fresh basil with something else?",
        "pantry": ["pasta", "garlic", "olive oil"],
        "cuisine": "Italian",
        "expected_substrings": ["dried basil"],
        "must_not_contain": ["apples", "chocolate"],
    },
    {
        "id": 5,
        "name": "Unverified substitution inquiry (mushrooms refusal)",
        "recipe_id": 1316605,
        "task": AssistantTask.QUESTION,
        "question": "Can I substitute the mushrooms with apples or bananas?",
        "pantry": ["pasta", "garlic", "olive oil"],
        "cuisine": "Italian",
        "expected_substrings": ["cannot confirm a reliable culinary substitute"],
        "must_not_contain": ["use apples instead", "delicious apple pasta"],
    },
    {
        "id": 6,
        "name": "Custom cooking step question (sausage before pasta)",
        "recipe_id": 1670510,
        "task": AssistantTask.QUESTION,
        "question": "How should I cook the sausage before adding the pasta?",
        "pantry": ["pasta", "olive oil", "garlic", "onion", "tomatoes"],
        "cuisine": "Italian",
        "expected_substrings": ["Step 1", "sausage", "skillet"],
        "must_not_contain": ["invented", "microwave"],
    },
]


def run_evaluation() -> Dict[str, any]:
    print("=" * 70)
    print("MILESTONE 6: ASSISTANT EVALUATION BENCHMARK")
    print("=" * 70)

    total = len(EVALUATION_QUERIES)
    passed_groundedness = 0
    passed_refusals = 0
    latencies: List[float] = []

    for item in EVALUATION_QUERIES:
        start_t = time.perf_counter()
        req = AssistantRequest(
            recipe_id=item["recipe_id"],
            task=item["task"],
            question=item["question"],
            pantry_ingredients=item["pantry"],
            cuisine=item["cuisine"],
        )
        resp = assistant_service.get_guidance(req)
        elapsed_ms = (time.perf_counter() - start_t) * 1000
        latencies.append(elapsed_ms)

        ans_lower = resp.answer.lower()

        # Check expected substrings
        all_expected = all(s.lower() in ans_lower for s in item["expected_substrings"])
        # Check no forbidden substrings
        no_forbidden = not any(f.lower() in ans_lower for f in item["must_not_contain"])

        is_passed = all_expected and no_forbidden
        if is_passed:
            passed_groundedness += 1

        if item["id"] == 5:
            # Unverified refusal check
            if "cannot confirm" in ans_lower:
                passed_refusals += 1

        status_tag = "PASS" if is_passed else "FAIL"
        print(f"[{status_tag}] Query #{item['id']} ({item['name']}): {elapsed_ms:.2f}ms")
        if not is_passed:
            print(f"       Expected: {item['expected_substrings']}")
            print(f"       Got: {resp.answer[:120]}...")

    avg_latency = sum(latencies) / len(latencies)
    groundedness_rate = (passed_groundedness / total) * 100.0
    refusal_rate = (passed_refusals / 1) * 100.0

    print("-" * 70)
    print(f"Groundedness Pass Rate:         {groundedness_rate:.1f}% ({passed_groundedness}/{total})")
    print(f"Unverified Refusal Rate:        {refusal_rate:.1f}% ({passed_refusals}/1)")
    print(f"Average Response Latency:       {avg_latency:.2f} ms")
    print("=" * 70)

    return {
        "total_queries": total,
        "passed_groundedness": passed_groundedness,
        "groundedness_rate": groundedness_rate,
        "refusal_rate": refusal_rate,
        "avg_latency_ms": avg_latency,
    }


if __name__ == "__main__":
    run_evaluation()
