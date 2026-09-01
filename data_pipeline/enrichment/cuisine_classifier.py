import re
from typing import List, Optional, Set, Tuple

from data_pipeline.enrichment.taxonomy import (
    CUISINE_INGREDIENT_PROFILES,
    CUISINE_TITLE_KEYWORDS,
    SUPPORTED_CUISINES,
)


def classify_cuisine(
    title: str,
    ner_ingredients: List[str],
) -> Tuple[Optional[str], Optional[str], str]:
    """
    Conservative rule-based cuisine classification:
    - High confidence: Explicit title keyword match
    - Medium confidence: Co-occurrence of signature ingredient profile
    - Insufficient evidence: (None, None, "insufficient_evidence")

    Returns: (predicted_cuisine, confidence, method_or_evidence)
    """
    if not title:
        title = ""

    title_lower = title.lower()
    recipe_ner_set: Set[str] = {ing.lower().strip() for ing in ner_ingredients if ing}

    # Step 1: Title-based explicit keyword match (High Confidence)
    title_matches = []
    for cuisine, keywords in CUISINE_TITLE_KEYWORDS.items():
        for kw in keywords:
            # Word boundary matching to avoid false substrings (e.g. "curry" in "scurry")
            if re.search(r"\b" + re.escape(kw) + r"\b", title_lower):
                title_matches.append((cuisine, kw))
                break

    if title_matches:
        # If single clear cuisine in title, return high confidence
        primary_cuisine, kw = title_matches[0]
        return primary_cuisine, "high", f"title_keyword:{kw}"

    # Step 2: Co-occurring signature ingredients (Medium Confidence)
    ingredient_matches = []
    for cuisine, profiles in CUISINE_INGREDIENT_PROFILES.items():
        for profile in profiles:
            # Check if all ingredients in the signature profile are present
            # Match either exact or if any recipe NER item contains the signature term
            matched_profile_items = 0
            for sig_term in profile:
                if any(sig_term in r_ing for r_ing in recipe_ner_set):
                    matched_profile_items += 1
            
            if matched_profile_items == len(profile):
                ingredient_matches.append((cuisine, ",".join(sorted(profile))))
                break

    if len(ingredient_matches) == 1:
        cuisine, matched_terms = ingredient_matches[0]
        return cuisine, "medium", f"signature_profile:{matched_terms}"
    elif len(ingredient_matches) > 1:
        # If multiple cuisines match, return the first with note of mixed evidence
        cuisine, matched_terms = ingredient_matches[0]
        return cuisine, "medium", f"signature_profile_mixed:{matched_terms}"

    # Step 3: Insufficient evidence (conservative guard)
    return None, None, "insufficient_evidence"
