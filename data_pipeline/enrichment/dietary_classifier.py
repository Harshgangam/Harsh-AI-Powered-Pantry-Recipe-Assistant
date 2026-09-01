from typing import List, Tuple

from data_pipeline.enrichment.taxonomy import (
    ANIMAL_DERIVED_EXCLUSIONS,
    NON_VEGETARIAN_EXCLUSIONS,
)


def classify_dietary_compatibility(
    ner_ingredients: List[str],
) -> Tuple[str, str, str]:
    """
    Inferred heuristic dietary compatibility based on ingredient exclusions.
    
    IMPORTANT:
    This is an inferred heuristic based on detected ingredients, NOT a ground-truth
    dietary certification.
    - Explicit detected meat/seafood exclusions have high confidence.
    - Absence-based compatibility (vegetarian_compatible, vegan_compatible) has
      lower confidence (medium/low) because unlisted ingredients or processing aids
      cannot be verified from text alone.

    Returns:
    - dietary_compatibility: 'non_vegetarian' | 'vegetarian_compatible' | 'vegan_compatible'
    - dietary_confidence: 'high' | 'medium' | 'low'
    - dietary_method: explanation string identifying detected exclusions or absence
    """
    if ner_ingredients is None or len(ner_ingredients) == 0:
        return "vegetarian_compatible", "low", "empty_ingredient_list"

    detected_meat = []
    detected_animal_derived = []

    for item in ner_ingredients:
        norm = item.lower().strip()
        if not norm:
            continue

        # Check meat/poultry/seafood exclusions
        if norm in NON_VEGETARIAN_EXCLUSIONS:
            detected_meat.append(norm)
            continue
        
        # Substring / multi-word check for common meats
        for exclusion in ("chicken", "beef", "pork", "bacon", "sausage", "turkey", "salmon", "tuna", "shrimp", "gelatin", "lard"):
            if exclusion in norm:
                detected_meat.append(norm)
                break
        else:
            # Check dairy/egg exclusions if no meat detected
            if norm in ANIMAL_DERIVED_EXCLUSIONS:
                detected_animal_derived.append(norm)
                continue
            for animal_item in ("cheese", "milk", "butter", "egg", "cream", "yogurt", "honey", "mayonnaise"):
                if animal_item in norm:
                    detected_animal_derived.append(norm)
                    break

    # 1. Non-vegetarian if meat/seafood detected (High Confidence)
    if detected_meat:
        return (
            "non_vegetarian",
            "high",
            f"detected_meat_or_seafood:{detected_meat[0]}",
        )

    # 2. Vegetarian-compatible if dairy/eggs detected (Medium Confidence)
    if detected_animal_derived:
        return (
            "vegetarian_compatible",
            "medium",
            f"detected_dairy_or_eggs:{detected_animal_derived[0]}",
        )

    # 3. Vegan-compatible if no animal ingredients detected (Low Confidence due to absence heuristic)
    return (
        "vegan_compatible",
        "low",
        "no_animal_ingredients_detected",
    )
