from typing import List, Optional
from pydantic import BaseModel, Field


class SubstitutionEntry(BaseModel):
    """
    Knowledge base representation of a single substitution relationship.
    """
    original_ingredient: str
    substitute: str
    ratio: Optional[str] = Field(
        default=None,
        description="Standardized culinary substitution ratio (e.g. '1:1', '1:0.75', '1:0.5'), or None if unquantifiable.",
    )
    confidence: str = Field(
        ...,
        description="Confidence level: 'high' (standard equivalent), 'medium' (functional substitute), or 'low' (emergency fallback).",
    )
    dietary_compatibility: List[str] = Field(
        default_factory=list,
        description="Dietary categories this substitute satisfies: ['vegetarian', 'vegan', 'gluten_free'].",
    )
    use_cases: List[str] = Field(
        default_factory=lambda: ["general"],
        description="Culinary application contexts: e.g. ['baking', 'frying', 'sauces', 'salads', 'general'].",
    )
    reason: str = Field(
        ...,
        description="Culinary justification explaining why the substitute works and expected flavor/texture characteristics.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Practical culinary guidance or adjustment tips.",
    )
    source: str = Field(
        default="Culinary Reference Standards",
        description="Authoritative reference source for this substitution relationship.",
    )


class SubstitutionCandidate(BaseModel):
    """
    User-facing substitution suggestion presented for a missing recipe ingredient.
    """
    missing_ingredient: str
    substitute: str
    ratio: Optional[str] = None
    confidence: str = Field(..., description="'high' | 'medium' | 'low'")
    reason: str
    use_case: Optional[str] = None
    dietary_compatible: bool = True
    notes: Optional[str] = None
    source: Optional[str] = "Culinary Reference Standards"
