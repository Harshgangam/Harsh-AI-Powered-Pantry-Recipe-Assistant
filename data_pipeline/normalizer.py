import ast
import json
import math
from typing import Any, List, Optional, Tuple


def is_null_or_empty(val: Any) -> bool:
    """Checks if a value is None, NaN, empty string, or string representation of NaN."""
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    s = str(val).strip()
    return not s or s.lower() in ("nan", "none", "null")


def parse_list_field(raw_value: Any) -> Optional[List[str]]:
    """
    Parses a string representing a list (e.g. '["item1", "item2"]')
    Fast path: json.loads; fallback: ast.literal_eval.
    Returns None if raw_value is None or parsing fails.
    """
    if raw_value is None:
        return None
    if isinstance(raw_value, float) and math.isnan(raw_value):
        return None
    if isinstance(raw_value, list):
        return [str(x) for x in raw_value]
    
    val_str = str(raw_value).strip()
    if not val_str or val_str in ("[]", "nan", "none", "null"):
        return []
    
    # Fast path: JSON format
    try:
        parsed = json.loads(val_str)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass

    # Fallback: Python literal format (handles single quotes, unicode escapes, etc.)
    try:
        parsed = ast.literal_eval(val_str)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass

    return None


def normalize_ingredient(ingredient: str) -> str:
    """
    Normalizes a single ingredient string:
    - Lowercases text
    - Strips leading/trailing whitespace and punctuation
    - Collapses consecutive whitespace
    """
    if is_null_or_empty(ingredient):
        return ""
    
    cleaned = str(ingredient).lower().strip()
    # Normalize internal whitespace
    cleaned = " ".join(cleaned.split())
    # Strip common enclosing quotes or stray punctuation
    cleaned = cleaned.strip("\"'.,;:")
    return cleaned


def normalize_ner_list(raw_ner: Any) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Parses and normalizes the NER field.
    Returns (normalized_list, error_message).
    - Returns error if parsing fails or list is empty.
    - Deduplicates ingredients within the recipe while preserving order.
    """
    items = parse_list_field(raw_ner)
    if items is None:
        return None, "Failed to parse NER list"
    
    normalized_list = []
    seen = set()
    for item in items:
        norm = normalize_ingredient(item)
        if norm and norm not in seen:
            seen.add(norm)
            normalized_list.append(norm)
    
    if not normalized_list:
        return None, "Empty NER list after normalization"
    
    return normalized_list, None


def validate_and_clean_recipe(
    raw_id: Any,
    title: Any,
    ingredients: Any,
    directions: Any,
    link: Any,
    source: Any,
    ner: Any,
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Validates a raw recipe row and extracts cleaned fields.
    Returns (cleaned_dict, error_message).
    """
    # 1. Validate ID
    if is_null_or_empty(raw_id):
        return None, "Missing recipe ID"
    try:
        recipe_id = int(float(str(raw_id).strip()))
    except (ValueError, TypeError):
        return None, f"Invalid recipe ID: {raw_id}"

    # 2. Validate Title
    if is_null_or_empty(title):
        return None, "Empty title"
    clean_title = str(title).strip()

    # 3. Parse and validate Ingredients
    parsed_ingredients = parse_list_field(ingredients)
    if not parsed_ingredients:
        return None, "Empty or invalid ingredients field"

    # 4. Parse and validate Directions
    parsed_directions = parse_list_field(directions)
    if not parsed_directions:
        return None, "Empty or invalid directions field"

    # 5. Parse and normalize NER
    norm_ner, ner_err = normalize_ner_list(ner)
    if ner_err:
        return None, f"NER validation error: {ner_err}"

    clean_source = "Unknown" if is_null_or_empty(source) else str(source).strip()
    clean_link = "" if is_null_or_empty(link) else str(link).strip()

    return {
        "recipe_id": recipe_id,
        "title": clean_title,
        "ingredients": parsed_ingredients,
        "directions": parsed_directions,
        "link": clean_link,
        "source": clean_source,
        "ner": norm_ner,
        "ner_count": len(norm_ner),
    }, None
