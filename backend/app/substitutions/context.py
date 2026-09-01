import re
from typing import List, Optional

# Context Keyword Patterns
BAKING_KEYWORDS = re.compile(
    r"\b(bake|bakes|baked|baking|oven|preheat|cake|cakes|cookie|cookies|muffin|muffins|"
    r"bread|pastry|pie|dough|batter|flour|cupcake|sheet pan|roasting pan)\b",
    re.IGNORECASE,
)

FRYING_KEYWORDS = re.compile(
    r"\b(fry|fries|fried|frying|saute|sautes|sauted|sauté|sautéed|sautéing|skillet|pan|"
    r"sear|seared|searing|brown|browned|browning|wok|deep-fry|pan-fry)\b",
    re.IGNORECASE,
)

SAUCE_KEYWORDS = re.compile(
    r"\b(sauce|sauces|gravy|soup|soups|stew|stews|simmer|simmers|simmered|simmering|"
    r"reduction|reduce|broth|pot|stockpot|whisk)\b",
    re.IGNORECASE,
)

SALAD_KEYWORDS = re.compile(
    r"\b(salad|salads|dressing|vinaigrette|raw|toss|tossed|tossing|fresh|garnish|cold)\b",
    re.IGNORECASE,
)

BINDING_KEYWORDS = re.compile(
    r"\b(bind|binding|meatball|meatballs|patty|patties|meatloaf|loaf|shape|form into balls)\b",
    re.IGNORECASE,
)


def detect_culinary_context(
    title: str,
    directions: List[str],
) -> str:
    """
    Infers the predominant culinary application context from recipe title and directions.
    Returns: 'baking' | 'frying' | 'sauces' | 'salads' | 'binding' | 'general'
    """
    text_corpus = f"{title or ''} {' '.join(directions or [])}".lower()

    if not text_corpus.strip():
        return "general"

    # Score each context based on keyword occurrences
    scores = {
        "baking": len(BAKING_KEYWORDS.findall(text_corpus)),
        "frying": len(FRYING_KEYWORDS.findall(text_corpus)),
        "sauces": len(SAUCE_KEYWORDS.findall(text_corpus)),
        "salads": len(SALAD_KEYWORDS.findall(text_corpus)),
        "binding": len(BINDING_KEYWORDS.findall(text_corpus)),
    }

    best_context, best_count = max(scores.items(), key=lambda x: x[1])

    if best_count >= 1:
        return best_context

    return "general"
