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


def calculate_eps(
    matched_ingredients: List[str],
    pantry_items_risk: Optional[Dict[str, str]] = None,
) -> float:
    """
    Calculates Expiry Priority Score (EPS, 0-100).
    Measures how effectively the recipe rescue high-risk expiring items.
    """
    if not matched_ingredients:
        return 0.0

    if not pantry_items_risk:
        return 50.0

    total_risk_points = 0.0
    count = 0

    for ing in matched_ingredients:
        ing_lower = ing.lower().strip()
        risk = pantry_items_risk.get(ing_lower, 'low')
        if risk == 'high':
            total_risk_points += 100.0
        elif risk == 'medium':
            total_risk_points += 60.0
        else:
            total_risk_points += 20.0
        count += 1

    if count == 0:
        return 0.0

    return round(total_risk_points / count, 2)


def calculate_qus(
    matched_ingredients: List[str],
    pantry_quantities: Optional[Dict[str, float]] = None,
) -> float:
    """
    Calculates Quantity Utilization Score (QUS, 0-100).
    """
    if not matched_ingredients:
        return 0.0
    if not pantry_quantities:
        return 75.0

    utilized = sum(1 for ing in matched_ingredients if pantry_quantities.get(ing.lower(), 1.0) > 0)
    return round((utilized / len(matched_ingredients)) * 100.0, 2)


def calculate_dcs(
    dietary_preference: Optional[str],
    recipe_compatibility: Optional[str],
) -> float:
    """
    Calculates Dietary Compatibility Score (DCS, 0-100).
    100.0 if fully compatible or no constraint, 0.0 if incompatible.
    """
    if not dietary_preference:
        return 100.0

    pref = dietary_preference.lower()
    compat = (recipe_compatibility or 'non_vegetarian').lower()

    if pref == 'vegetarian':
        if compat in ('vegetarian_compatible', 'vegan_compatible'):
            return 100.0
        return 0.0

    if pref == 'vegan':
        if compat == 'vegan_compatible':
            return 100.0
        return 0.0

    if pref in ('non_vegetarian', 'non-vegetarian', 'non_veg'):
        if compat == 'non_vegetarian':
            return 100.0
        return 0.0

    return 100.0


def calculate_tcs(
    max_cooking_time: Optional[int],
    estimated_time: Optional[int],
) -> float:
    """
    Calculates Cooking-Time Compatibility Score (TCS, 0-100).
    """
    if max_cooking_time is None or max_cooking_time <= 0:
        return 100.0
    if estimated_time is None or estimated_time <= 0:
        return 80.0

    if estimated_time <= max_cooking_time:
        headroom = max_cooking_time - estimated_time
        return min(100.0, 80.0 + (headroom / max_cooking_time) * 20.0)
    else:
        over = estimated_time - max_cooking_time
        penalty = min(80.0, over * 2.0)
        return max(0.0, round(80.0 - penalty, 2))


def calculate_mip(missing_count: int, total_recipe_ingredients: int) -> float:
    """
    Calculates Missing Ingredient Penalty (MIP, 0-100 scale penalty).
    """
    if total_recipe_ingredients == 0:
        return 0.0
    ratio = missing_count / total_recipe_ingredients
    return round(ratio * 50.0, 2)


def calculate_frps(
    ims: float,
    pus: float,
    eps: float = 50.0,
    qus: float = 75.0,
    dcs: float = 100.0,
    tcs: float = 100.0,
    mip: float = 0.0,
    rescue_mode: bool = False,
) -> Tuple[float, Dict[str, float]]:
    """
    Calculates Food Rescue Priority Score (FRPS) on a 0-100 scale.
    """
    if rescue_mode:
        w_ims = 0.25
        w_pus = 0.20
        w_eps = 0.20
        w_qus = 0.15
        w_dcs = 0.10
        w_tcs = 0.10
        w_mip = 0.10
    else:
        w_ims = 0.40
        w_pus = 0.20
        w_eps = 0.10
        w_qus = 0.10
        w_dcs = 0.10
        w_tcs = 0.10
        w_mip = 0.10

    raw_frps = (
        (ims * w_ims)
        + (pus * w_pus)
        + (eps * w_eps)
        + (qus * w_qus)
        + (dcs * w_dcs)
        + (tcs * w_tcs)
        - (mip * w_mip)
    )

    frps = min(100.0, max(0.0, raw_frps))

    breakdown = {
        "ims": round(ims, 1),
        "pus": round(pus, 1),
        "eps": round(eps, 1),
        "qus": round(qus, 1),
        "dcs": round(dcs, 1),
        "tcs": round(tcs, 1),
        "mip": round(mip, 1),
        "w_ims": w_ims,
        "w_pus": w_pus,
        "w_eps": w_eps,
        "w_qus": w_qus,
        "w_dcs": w_dcs,
        "w_tcs": w_tcs,
        "w_mip": w_mip,
    }

    return round(frps, 2), breakdown


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
    eps: float,
    rescue_mode: bool = False,
    dietary_preference: Optional[str] = None,
    max_cooking_time: Optional[int] = None,
) -> str:
    """
    Generates grounded Explainable AI (XAI) rationale for FRPS ranking.
    """
    matched_str = ", ".join(matched_ingredients[:4]) if matched_ingredients else "none"

    if eps >= 75.0:
        expiry_msg = "It actively rescues high-risk expiring ingredients from your pantry."
    elif eps >= 50.0:
        expiry_msg = "It uses moderately fresh ingredients from your pantry."
    else:
        expiry_msg = "providing standard pantry use."

    mode_prefix = "RESCUE MODE PRIORITY: " if rescue_mode else "This recipe was ranked highly because "

    reasons = [f"{mode_prefix}it uses {len(matched_ingredients)} of {total_recipe_ingredients} required ingredients ({matched_str}), {expiry_msg}"]

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
