import re
from typing import List, Optional, Tuple

# Active cooking verbs
COOKING_VERBS = re.compile(
    r"\b(bake|bakes|baked|baking|cook|cooks|cooked|cooking|simmer|simmers|simmered|simmering|"
    r"boil|boils|boiled|boiling|fry|fries|fried|frying|roast|roasts|roasted|roasting|"
    r"saute|sautes|sauted|sauté|sautéed|broil|broils|broiled|broiling|microwave|microwaves|"
    r"microwaved|steam|steams|steamed|steaming|grill|grills|grilled|grilling|heat|heats|"
    r"heated|heating|brown|browns|browned|browning|sear|seared|searing)\b",
    re.IGNORECASE,
)

# Resting / cooling / chilling verbs to avoid confounding with active cooking time
PASSIVE_VERBS = re.compile(
    r"\b(chill|chilled|chilling|cool|cooled|cooling|refrigerate|refrigerated|"
    r"refrigerating|freeze|freezing|frozen|marinate|marinating|marinated|"
    r"stand|standing|rest|resting|rested)\b",
    re.IGNORECASE,
)

# Time duration patterns: e.g. "30 minutes", "1 to 2 hours", "45-50 min"
TIME_REGEX = re.compile(
    r"(\b\d+(?:\.\d+)?|\b\d+\s*-\s*\d+|\b\d+\s*to\s*\d+)\s*(hours?|hrs?|minutes?|mins?)\b",
    re.IGNORECASE,
)


def parse_duration_to_minutes(num_str: str, unit_str: str) -> Optional[int]:
    """Parse number or range string + unit string to total minutes."""
    try:
        num_str = num_str.lower().strip()
        unit_str = unit_str.lower().strip()

        if "-" in num_str:
            parts = num_str.split("-")
            val = float(parts[-1].strip())
        elif "to" in num_str:
            parts = num_str.split("to")
            val = float(parts[-1].strip())
        else:
            val = float(num_str)

        if "h" in unit_str:  # hour or hr
            return int(round(val * 60))
        elif "m" in unit_str:  # minute or min
            return int(round(val))
    except Exception:
        return None
    return None


def extract_cooking_time(
    directions: List[str],
) -> Tuple[Optional[int], Optional[str], str]:
    """
    Extract estimated active cooking time in minutes from recipe directions text.

    Aggregation Strategy:
    - Analyzes sentences across all directions.
    - Captures durations associated with active cooking verbs (bake, simmer, boil, roast, etc.).
    - Excludes passive resting/chilling/marinating periods.
    - Sums sequential active cooking steps (e.g. saute 5 min + bake 25 min = 30 min).
    - Caps unreasonable durations (> 24 hours / 1440 min) as unverified.

    Returns: (estimated_time_minutes, confidence, method)
    - If no reliable cooking time found: (None, None, "no_explicit_duration_found")
    """
    if directions is None or len(directions) == 0:
        return None, None, "no_explicit_duration_found"

    total_cooking_minutes = 0
    active_matches_count = 0
    detected_steps = []

    for step_idx, step_text in enumerate(directions):
        if not step_text:
            continue

        # Split step into sentences
        sentences = re.split(r"[.!?;]\s+", step_text)
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue

            # Check if sentence is purely passive/cooling
            has_passive = bool(PASSIVE_VERBS.search(sentence_clean))
            has_active = bool(COOKING_VERBS.search(sentence_clean))

            if has_passive and not has_active:
                # E.g. "Chill in refrigerator for 2 hours" -> skip
                continue

            matches = TIME_REGEX.findall(sentence_clean)
            if matches and (has_active or not has_passive):
                for num_part, unit_part in matches:
                    mins = parse_duration_to_minutes(num_part, unit_part)
                    if mins is not None and 0 < mins <= 720:  # Up to 12 hours
                        total_cooking_minutes += mins
                        active_matches_count += 1
                        detected_steps.append(f"{mins}m({num_part} {unit_part})")

    if total_cooking_minutes == 0 or active_matches_count == 0:
        return None, None, "no_explicit_duration_found"

    # Sanity guard: if total cooking time > 1440 min (24 hours), mark as untrusted
    if total_cooking_minutes > 1440:
        return None, None, "unrealistic_duration_exceeded"

    if active_matches_count == 1:
        confidence = "high"
        method = f"single_step_regex:{detected_steps[0]}"
    else:
        confidence = "medium"
        method = f"multi_step_sum:{'+'.join(detected_steps[:3])}"

    return total_cooking_minutes, confidence, method
