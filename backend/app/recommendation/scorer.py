from typing import Dict, List, Optional, Set, Tuple

from backend.app.recommendation.normalizer import to_singular_form


def _dedup_recipe_ner(recipe_ner: List[str]) -> List[str]:
    """
    Deduplicate recipe NER ingredients by their canonical singular form.
    When two entries reduce to the same singular (e.g. 'tomatoes' and 'tomato'),
    only the first occurrence is kept, preserving the original token for display.
    """
    seen_singular: Set[str] = set()
    deduped: List[str] = []
    for ing in recipe_ner:
        singular = to_singular_form(ing.lower().strip())
        if singular not in seen_singular:
            seen_singular.add(singular)
            deduped.append(ing)
    return deduped


def calculate_ims(recipe_ner: List[str], pantry_variants: Set[str]) -> Tuple[float, List[str], List[str]]:
    """
    Calculates the Ingredient Match Score (IMS):
    IMS = (matched_recipe_ingredients / total_recipe_ingredients) * 100

    Recipe NER ingredients are deduplicated by singular form before scoring
    to avoid counting 'tomato' and 'tomatoes' as two separate ingredients.
    """
    if not recipe_ner:
        return 0.0, [], []

    deduped_ner = _dedup_recipe_ner(recipe_ner)

    matched = []
    missing = []

    for ing in deduped_ner:
        if ing in pantry_variants:
            matched.append(ing)
        else:
            missing.append(ing)

    total = len(deduped_ner)
    matched_count = len(matched)
    ims = (matched_count / total) * 100.0 if total > 0 else 0.0

    return round(ims, 2), matched, missing


def calculate_pus(
    recipe_ner: List[str],
    relevant_pantry: Set[str],
    pantry_variants_to_canonical: dict,
) -> Tuple[float, int, int]:
    """
    Calculates the Pantry Utilization Score (PUS):
    PUS = (relevant_pantry_ingredients_used / total_relevant_pantry_ingredients) * 100
    """
    total_relevant = len(relevant_pantry)
    if total_relevant == 0:
        return 0.0, 0, 0

    used_relevant_canonical = set()
    for ing in recipe_ner:
        canonical = pantry_variants_to_canonical.get(ing)
        if canonical and canonical in relevant_pantry:
            used_relevant_canonical.add(canonical)

    used_count = len(used_relevant_canonical)
    pus = (used_count / total_relevant) * 100.0

    return round(pus, 2), used_count, total_relevant





def calculate_final_score(
    ims: float,
    pus: float,
    ims_weight: float = 0.6,
    pus_weight: float = 0.4,
) -> float:
    """
    Calculates weighted recommendation score from IMS and PUS.
    """
    final_score = (ims * ims_weight) + (pus * pus_weight)
    return min(100.0, max(0.0, round(final_score, 2)))


def generate_explanation(
    matched_count: int,
    total_recipe_ingredients: int,
    relevant_used_count: int,
    total_relevant_count: int,
) -> str:
    """
    Generates human-readable baseline decision rationale.
    """
    pantry_use_str = (
        f"It consumes {relevant_used_count} of your {total_relevant_count} active pantry items."
        if total_relevant_count > 0
        else "No pantry items utilized."
    )
    return (
        f"This recipe matches {matched_count} of {total_recipe_ingredients} required ingredients. "
        f"{pantry_use_str}"
    )


def generate_frps_explanation(
    matched_ingredients: List[str],
    missing_ingredients: List[str],
    total_recipe_ingredients: int,
    relevant_used_count: int,
    total_relevant_count: int,
    dietary_preference: Optional[str] = None,
    max_cooking_time: Optional[int] = None,
) -> str:
    """
    Generates grounded Explainable AI (XAI) rationale for ranking.
    """
    matched_str = ", ".join(matched_ingredients[:4]) if matched_ingredients else "none"

    reasons = [f"This recipe was ranked highly because it uses {len(matched_ingredients)} of {total_recipe_ingredients} required ingredients ({matched_str})."]

    if total_relevant_count > 0:
        reasons.append(f"It consumes {relevant_used_count} of your {total_relevant_count} active pantry items.")

    if dietary_preference:
        reasons.append(f"It strictly complies with your {dietary_preference} dietary filter.")

    if max_cooking_time:
        reasons.append(f"It fits within your {max_cooking_time}-minute cooking window.")

    if not missing_ingredients:
        reasons.append("No additional grocery purchases required!")
    else:
        reasons.append(f"Requires only {len(missing_ingredients)} additional grocery item(s).")

    return " ".join(reasons)
