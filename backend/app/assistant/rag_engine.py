import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KnowledgeDocument(BaseModel):
    id: str
    category: str  # "substitution_rules", "storage_guidance", "leftover_transforms", "cooking_technique"
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    is_verified: bool
    refusal_reason: Optional[str] = None
    pantry_compliance_pct: float = 100.0
    dietary_compliant: bool = True
    time_compliant: bool = True
    claims_verified: List[str] = Field(default_factory=list)


class RAGKnowledgeBase:
    """
    Curated RAG Knowledge Base containing verified culinary, storage, substitution,
    technique, and leftover transformation intelligence.
    """

    def __init__(self):
        self.documents: List[KnowledgeDocument] = []
        self._seed_knowledge_base()

    def _seed_knowledge_base(self):
        docs = [
            KnowledgeDocument(
                id="kb_sub_1",
                category="substitution_rules",
                title="Paneer Substitutions",
                content="Paneer can be substituted with Extra-Firm Tofu (ratio 1:1) for vegan options, or Halloumi/Feta for frying.",
                metadata={"role": "protein", "dietary": ["vegan", "vegetarian"]}
            ),
            KnowledgeDocument(
                id="kb_sub_2",
                category="substitution_rules",
                title="Egg Substitutions in Baking",
                content="For baking, 1 egg can be substituted with 1 tbsp chia/flaxseed meal mixed with 3 tbsp water or 1/4 cup unsweetened applesauce.",
                metadata={"role": "binder", "dietary": ["vegan"]}
            ),
            KnowledgeDocument(
                id="kb_sub_3",
                category="substitution_rules",
                title="Onion Substitutions",
                content="If onions are unavailable, substitute with shallots, leeks, green onion / scallions, or 1/4 tsp asafoetida (hing) in Indian cooking.",
                metadata={"role": "aromatic", "ingredient": "onion"}
            ),
            KnowledgeDocument(
                id="kb_storage_1",
                category="storage_guidance",
                title="Spinach Freshness Preservation",
                content="Keep fresh spinach in an airtight container lined with a dry paper towel in the crisper drawer to absorb excess moisture and extend shelf life by 5-7 days.",
                metadata={"ingredient": "spinach", "shelf_extension": "5-7 days"}
            ),
            KnowledgeDocument(
                id="kb_storage_2",
                category="storage_guidance",
                title="Tomato Storage Best Practices",
                content="Store fresh tomatoes at room temperature stem-side down to maintain flavor and texture. Avoid refrigerating uncut tomatoes as cold temperatures degrade cell walls.",
                metadata={"ingredient": "tomatoes", "shelf_extension": "3-5 days"}
            ),
            KnowledgeDocument(
                id="kb_leftover_1",
                category="leftover_transforms",
                title="Leftover Rice Transformation",
                content="Leftover cooked rice stored overnight in the fridge is ideal for Fried Rice or Rice Bowls because the chilled starch grains dry out and do not become mushy.",
                metadata={"ingredient": "rice", "transform_dish": "Fried Rice"}
            ),
            KnowledgeDocument(
                id="kb_leftover_2",
                category="leftover_transforms",
                title="Leftover Curry Wrap / Kathi Roll",
                content="Combine leftover cooked curry with raw sliced red onions, coriander, and fresh lemon juice wrapped in flatbread for a high-value 10-minute rescued lunch.",
                metadata={"ingredient": "curry", "transform_dish": "Kathi Roll"}
            ),
            KnowledgeDocument(
                id="kb_tech_1",
                category="cooking_technique",
                title="Sautéing Technique",
                content="Sautéing is a cooking method that cooks food quickly in a small amount of oil or fat over high heat in a shallow pan, tossing ingredients frequently.",
                metadata={"technique": "sautéing"}
            ),
            KnowledgeDocument(
                id="kb_tech_2",
                category="cooking_technique",
                title="Spiciness Adjustment Technique",
                content="To reduce heat in a dish that is too spicy, add dairy (cream, yogurt, milk, cheese), nut butter, acidic juice (lemon/lime), or a touch of sugar/honey.",
                metadata={"technique": "adjust_spiciness"}
            ),
        ]
        self.documents = docs

    def retrieve_relevant_docs(self, query: str, top_k: int = 3) -> List[KnowledgeDocument]:
        query_words = set(query.lower().split())
        scored_docs = []

        for doc in self.documents:
            doc_text = f"{doc.title} {doc.content} {' '.join(doc.metadata.values() if isinstance(doc.metadata.values(), list) else [])}".lower()
            doc_words = set(doc_text.split())
            overlap = len(query_words.intersection(doc_words))
            scored_docs.append((overlap, doc))

        scored_docs.sort(key=lambda x: -x[0])
        return [doc for score, doc in scored_docs[:top_k] if score > 0] or self.documents[:top_k]


class RecipeVerifier:
    """
    Recipe Verification Layer checking generated responses against dietary restrictions,
    pantry availability bounds, and cooking time limits.
    """

    @staticmethod
    def verify_recipe_recommendation(
        recipe_title: str,
        recipe_ner: List[str],
        pantry_ingredients: List[str],
        dietary_preference: Optional[str] = None,
        max_cooking_time: Optional[int] = None,
        estimated_time: Optional[int] = None,
        recipe_compatibility: Optional[str] = None,
    ) -> VerificationResult:
        pantry_set = {p.lower().strip() for p in pantry_ingredients}
        recipe_set = {r.lower().strip() for r in recipe_ner}

        matched = sum(1 for ing in recipe_set if any(p in ing or ing in p for p in pantry_set))
        compliance_pct = (matched / len(recipe_set) * 100.0) if recipe_set else 100.0

        dietary_compliant = True
        refusal_reason = None

        if dietary_preference:
            pref = dietary_preference.lower()
            compat = (recipe_compatibility or "non_vegetarian").lower()
            if pref == "vegetarian" and compat not in ("vegetarian_compatible", "vegan_compatible"):
                dietary_compliant = False
                refusal_reason = f"Recipe '{recipe_title}' contains non-vegetarian ingredients violating vegetarian filter."
            elif pref == "vegan" and compat != "vegan_compatible":
                dietary_compliant = False
                refusal_reason = f"Recipe '{recipe_title}' is not fully vegan compatible."

        time_compliant = True
        if max_cooking_time and estimated_time:
            if estimated_time > max_cooking_time:
                time_compliant = False
                refusal_reason = f"Cooking time ({estimated_time}m) exceeds specified limit of {max_cooking_time}m."

        is_verified = dietary_compliant and time_compliant and (compliance_pct >= 30.0)

        claims = [
            f"Pantry Match: {matched}/{len(recipe_set)} ingredients ({round(compliance_pct, 1)}%)",
            f"Dietary Status: {'Verified Compliant' if dietary_compliant else 'Non-Compliant'}",
            f"Cooking Time Status: {'Within Limit' if time_compliant else 'Exceeds Limit'}",
        ]

        return VerificationResult(
            is_verified=is_verified,
            refusal_reason=refusal_reason,
            pantry_compliance_pct=round(compliance_pct, 1),
            dietary_compliant=dietary_compliant,
            time_compliant=time_compliant,
            claims_verified=claims,
        )


# Singleton instances
rag_knowledge_base = RAGKnowledgeBase()
recipe_verifier = RecipeVerifier()
