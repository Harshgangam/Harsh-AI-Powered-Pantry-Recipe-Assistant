import re
from typing import List, Set, Tuple

# Words ending in 's' that are singular and must not have trailing 's' removed
PROTECTED_SINGULARS: Set[str] = {
    "asparagus",
    "molasses",
    "hummus",
    "couscous",
    "citrus",
    "watercress",
    "lemongrass",
    "swiss cheese",
    "feta cheese",
    "parmesan cheese",
    "ricotta cheese",
    "goat cheese",
    "blue cheese",
    "cream cheese",
    "cheddar cheese",
    "provolone cheese",
    "mozzarella cheese",
    "monterey jack cheese",
    "cottage cheese",
    "gouda cheese",
    "brie cheese",
    "havarti cheese",
    "fontina cheese",
    "asiago cheese",
    "gruyere cheese",
    "manchego cheese",
    "colby cheese",
    "colby jack cheese",
    "curry leaves",
    "bay leaves",
    "brussels sprouts",
    "oats",
    "rolled oats",
    "quick oats",
    "groats",
    "chia seeds",
    "sesame seeds",
    "flax seeds",
    "poppy seeds",
    "sunflower seeds",
    "pumpkin seeds",
    "mustard seeds",
    "caraway seeds",
    "fennel seeds",
    "coriander seeds",
    "cumin seeds",
    "dill seeds",
    "anise seeds",
    "celery seeds",
}


def normalize_pantry_ingredient(ingredient: str) -> str:
    """
    Conservative normalization of a single pantry ingredient:
    - Lowercase
    - Strip whitespace
    - Collapse multiple whitespace to single space
    - Strip harmless surrounding punctuation (quotes, commas, colons, etc.)
    """
    if not ingredient:
        return ""
    
    cleaned = ingredient.lower().strip()
    # Normalize internal whitespace
    cleaned = " ".join(cleaned.split())
    # Strip harmless surrounding punctuation
    cleaned = cleaned.strip("\"'.,;:#?!*~`()[]{}")
    return cleaned


def to_singular_form(term: str) -> str:
    """
    Safely converts a regular plural food noun to its singular form.
    Only operates on the final word if term is multi-word (e.g. 'fresh tomatoes' -> 'fresh tomato').
    Guards protected singulars (e.g. 'asparagus', 'couscous').
    """
    norm = normalize_pantry_ingredient(term)
    if not norm or norm in PROTECTED_SINGULARS:
        return norm

    words = norm.split(" ")
    last_word = words[-1]

    # If the last word is protected, do not de-pluralize
    if last_word in PROTECTED_SINGULARS:
        return norm

    singular_last = last_word

    # Rule 1: -ies -> -y (e.g. cherries -> cherry, strawberries -> strawberry)
    # Exclude very short words like 'pies' -> 'pie', 'ties' -> 'tie'
    if last_word.endswith("ies") and len(last_word) > 4:
        singular_last = last_word[:-3] + "y"
    # Rule 2: -es after s, x, z, ch, sh, o (e.g. tomatoes -> tomato, potatoes -> potato)
    elif last_word.endswith("es"):
        if re.search(r"(s|x|z|ch|sh|o)es$", last_word):
            # Guard against 'grapes' -> 'grap' by checking 'pe', 'te'
            if last_word in ("tomatoes", "potatoes"):
                singular_last = last_word[:-2]
            elif re.search(r"(ch|sh|ss|x|z)es$", last_word):
                singular_last = last_word[:-2]
            else:
                singular_last = last_word[:-1]
        else:
            singular_last = last_word[:-1]
    # Rule 3: Regular -s (e.g. onions -> onion, eggs -> egg, carrots -> carrot)
    elif last_word.endswith("s") and not last_word.endswith("ss") and len(last_word) > 2:
        singular_last = last_word[:-1]

    if singular_last != last_word:
        words[-1] = singular_last
        return " ".join(words)

    return norm


def to_plural_form(term: str) -> str:
    """
    Safely derives the standard plural form of a food noun for index lookup.
    """
    norm = normalize_pantry_ingredient(term)
    if not norm or norm in PROTECTED_SINGULARS:
        return norm

    words = norm.split(" ")
    last_word = words[-1]

    if last_word in PROTECTED_SINGULARS:
        return norm

    if last_word.endswith("y") and not re.search(r"[aeiou]y$", last_word) and len(last_word) > 2:
        plural_last = last_word[:-1] + "ies"
    elif last_word in ("tomato", "potato"):
        plural_last = last_word + "es"
    elif re.search(r"(s|x|z|ch|sh)$", last_word):
        plural_last = last_word + "es"
    elif not last_word.endswith("s"):
        plural_last = last_word + "s"
    else:
        plural_last = last_word

    words[-1] = plural_last
    return " ".join(words)


def get_lookup_variants(term: str) -> Set[str]:
    """
    Given a normalized user pantry term, returns a small set of safe
    spelling variants (exact normalized, singular form, plural form)
    to check against the index.
    Does NOT collapse semantic distinctions (e.g. 'chicken breasts' != 'chicken').
    """
    norm = normalize_pantry_ingredient(term)
    if not norm:
        return set()

    variants = {norm}
    singular = to_singular_form(norm)
    plural = to_plural_form(norm)

    variants.add(singular)
    variants.add(plural)
    return variants


def normalize_pantry_list(ingredients: List[str]) -> Tuple[List[str], Set[str]]:
    """
    Normalizes a list of pantry ingredients provided by the user.
    Returns:
    - deduplicated list of normalized pantry ingredients (preserving order)
    - comprehensive set of safe lookup variants for all items
    """
    normalized_list = []
    seen = set()
    all_lookup_variants = set()

    for item in ingredients:
        norm = normalize_pantry_ingredient(item)
        if norm and norm not in seen:
            seen.add(norm)
            # Use canonical singular if safe, or exact normalized form
            canonical = to_singular_form(norm) if to_singular_form(norm) else norm
            normalized_list.append(canonical)
            all_lookup_variants.update(get_lookup_variants(norm))

    return normalized_list, all_lookup_variants
