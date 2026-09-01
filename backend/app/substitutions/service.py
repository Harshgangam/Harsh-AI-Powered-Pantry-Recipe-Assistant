from typing import Dict, List, Optional

from backend.app.substitutions.context import detect_culinary_context
from backend.app.substitutions.knowledge_base import SUBSTITUTION_DATABASE
from backend.app.substitutions.models import SubstitutionCandidate, SubstitutionEntry


class SubstitutionService:
    """
    Intelligent substitution engine providing context-aware, dietary-filtered
    ingredient alternatives for missing recipe ingredients.
    """

    def __init__(self, database: Optional[List[SubstitutionEntry]] = None):
        self.database = database or SUBSTITUTION_DATABASE
        self._index: Dict[str, List[SubstitutionEntry]] = {}
        for entry in self.database:
            key = entry.original_ingredient.lower().strip()
            if key not in self._index:
                self._index[key] = []
            self._index[key].append(entry)

    def lookup_raw_entries(self, ingredient_name: str) -> List[SubstitutionEntry]:
        """Lookup substitution entries in this service instance's index."""
        if not ingredient_name:
            return []

        norm = ingredient_name.lower().strip()

        # 1. Exact match in index
        if norm in self._index:
            return self._index[norm]

        # 2. Singular check (e.g. 'eggs' -> 'egg')
        if norm.endswith("s") and norm[:-1] in self._index:
            return self._index[norm[:-1]]

        # 3. Substring check for compound terms (e.g. 'unsalted butter' -> 'butter')
        for key, entries in self._index.items():
            if key in norm or norm in key:
                return entries

        return []

    def get_substitutions_for_ingredient(
        self,
        missing_ingredient: str,
        context: str = "general",
        dietary_preference: Optional[str] = None,
        max_candidates: int = 2,
    ) -> List[SubstitutionCandidate]:
        """
        Finds appropriate substitution candidates for a single missing ingredient.
        """
        raw_entries = self.lookup_raw_entries(missing_ingredient)
        if not raw_entries:
            return []

        # 1. Filter by dietary preference
        compatible_entries = []
        user_diet = (dietary_preference or "").lower()

        for entry in raw_entries:
            if user_diet == "vegan":
                if "vegan" in entry.dietary_compatibility:
                    compatible_entries.append(entry)
            elif user_diet == "vegetarian":
                if "vegetarian" in entry.dietary_compatibility or "vegan" in entry.dietary_compatibility:
                    compatible_entries.append(entry)
            else:
                compatible_entries.append(entry)

        if not compatible_entries:
            return []

        # 2. Sort/Prioritize by context match, then confidence
        conf_weights = {"high": 3, "medium": 2, "low": 1}

        def score_entry(e: SubstitutionEntry):
            context_match = 1 if (context in e.use_cases or "general" in e.use_cases) else 0
            exact_context_match = 2 if context in e.use_cases else 0
            conf_score = conf_weights.get(e.confidence, 1)
            return (exact_context_match, context_match, conf_score)

        sorted_entries = sorted(compatible_entries, key=score_entry, reverse=True)

        results: List[SubstitutionCandidate] = []
        seen_substitutes = set()

        for entry in sorted_entries[:max_candidates]:
            if entry.substitute in seen_substitutes:
                continue
            seen_substitutes.add(entry.substitute)

            results.append(
                SubstitutionCandidate(
                    missing_ingredient=missing_ingredient,
                    substitute=entry.substitute,
                    ratio=entry.ratio,
                    confidence=entry.confidence,
                    reason=entry.reason,
                    use_case=context if context != "general" else (entry.use_cases[0] if entry.use_cases else "general"),
                    dietary_compatible=True,
                    notes=entry.notes,
                    source=entry.source,
                )
            )

        return results

    def get_substitutions_for_recipe(
        self,
        missing_ingredients: List[str],
        recipe_title: str = "",
        directions: Optional[List[str]] = None,
        dietary_preference: Optional[str] = None,
        max_substitutes_per_item: int = 1,
    ) -> List[SubstitutionCandidate]:
        """
        Extracts substitution candidates for all missing ingredients in a recommended recipe.
        """
        if not missing_ingredients:
            return []

        context = detect_culinary_context(recipe_title, directions or [])

        all_candidates: List[SubstitutionCandidate] = []
        for missing_item in missing_ingredients:
            item_subs = self.get_substitutions_for_ingredient(
                missing_ingredient=missing_item,
                context=context,
                dietary_preference=dietary_preference,
                max_candidates=max_substitutes_per_item,
            )
            all_candidates.extend(item_subs)

        return all_candidates

    def generate_substitution_explanation(
        self,
        substitutions: List[SubstitutionCandidate],
    ) -> Optional[str]:
        """
        Generates a human-readable explanation clause detailing suggested alternatives.
        """
        if not substitutions:
            return None

        clauses = []
        for sub in substitutions:
            ratio_str = f" ({sub.ratio})" if sub.ratio else ""
            clauses.append(
                f"Missing {sub.missing_ingredient}: {sub.substitute} is suggested as a {sub.confidence}-confidence alternative{ratio_str} because {sub.reason.lower()}"
            )

        return " Substitutions: " + " ".join(clauses)


# Global service singleton
substitution_service = SubstitutionService()
