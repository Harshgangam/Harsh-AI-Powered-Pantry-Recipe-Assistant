# Milestone 4: Missing Ingredients and Substitution Intelligence

## 1. Executive Summary & Purpose

In a pantry-first recommendation system, recipes frequently match most—but not all—of a user's on-hand ingredients. For every candidate recipe, the engine deterministically identifies:
$$\text{missing\_ingredients} = \text{Recipe NER} \setminus \text{Normalized User Pantry}$$

Milestone 4 adds **deterministic culinary substitution intelligence** to suggest practical, context-appropriate, and dietary-compliant alternatives for missing items.

> [!IMPORTANT]
> **Culinary Advisory**: Substitutions are **suggested culinary alternatives**, not identical chemical replacements. While carefully curated according to culinary reference standards, substitutions may introduce subtle variations in moisture, texture, browning, or flavor nuances.

---

## 2. Substitution Knowledge-Base Design & Schema

The substitution knowledge base resides in [backend/app/substitutions/knowledge_base.py](file:///c:/Users/sward/AI-Powered-Pantry-Recipe-Assistant/backend/app/substitutions/knowledge_base.py) as an independent, maintainable catalog of **51 curated culinary substitution relationships**.

### Schema Specification (`SubstitutionEntry`)

| Field | Type | Example | Description |
|---|---|---|---|
| `original_ingredient` | `str` | `"butter"` | Canonical name of the missing ingredient. |
| `substitute` | `str` | `"margarine"` | Recommended replacement item. |
| `ratio` | `Optional[str]` | `"1:1"` | Standardized culinary substitution ratio, or `None` if unquantified. |
| `confidence` | `str` | `"high"` | `"high"` (direct standard), `"medium"` (functional substitute), `"low"` (emergency fallback). |
| `dietary_compatibility` | `List[str]` | `["vegetarian", "vegan"]` | List of dietary lifestyles this substitute satisfies. |
| `use_cases` | `List[str]` | `["baking", "cooking"]` | Culinary contexts where this substitution is suitable. |
| `reason` | `str` | `"Provides identical fat..."` | Culinary justification explaining flavor, moisture, and chemical behavior. |
| `notes` | `Optional[str]` | `"Use stick margarine..."` | Practical preparation notes. |
| `source` | `str` | `"USDA / CIA Standards"` | Authoritative culinary benchmark source. |

---

## 3. Supported Substitution Categories (51 Curated Entries)

The knowledge base covers 7 essential cooking categories:

1. **Dairy**:
   - `butter` $\to$ `margarine` (baking, 1:1), `olive oil` (frying, 1:0.75), `applesauce` (baking, 1:0.5).
   - `milk` $\to$ `soy milk` (1:1), `almond milk` (1:1), `oat milk` (1:1).
   - `heavy cream` $\to$ `milk and melted butter` (1:1), `coconut cream` (1:1 plant-based).
   - `sour cream` $\to$ `plain greek yogurt` (1:1), `silken tofu with lemon juice` (1:1 plant-based).
   - `buttermilk` $\to$ `milk with lemon juice` (1:1), `soy milk with lemon juice` (1:1 plant-based).
   - `parmesan cheese` $\to$ `pecorino romano` (1:1), `nutritional yeast` (1:0.5 plant-based).
   - `cheddar cheese` $\to$ `monterey jack cheese` (1:1).
   - `ricotta cheese` $\to$ `strained cottage cheese` (1:1).
   - `yogurt` $\to$ `sour cream` (1:1), `coconut yogurt` (1:1 plant-based).

2. **Eggs**:
   - `egg` $\to$ `flaxseed meal with water (flax egg)` (1:1 egg = 1 tbsp flax + 3 tbsp water, baking).
   - `egg` $\to$ `applesauce` (1:1 egg = 0.25 cup, baking).
   - `egg` $\to$ `mashed banana` (1:1 egg = 0.5 banana, baking).

3. **Fats & Oils**:
   - `olive oil` $\to$ `vegetable oil` (1:1).
   - `vegetable oil` $\to$ `canola oil` (1:1), `applesauce` (1:0.75 baking).

4. **Acidic Ingredients**:
   - `lemon juice` $\to$ `lime juice` (1:1), `apple cider vinegar` (1:0.5).
   - `lime juice` $\to$ `lemon juice` (1:1).
   - `white wine` (cooking) $\to$ `vegetable broth with lemon juice` (1:1).
   - `apple cider vinegar` $\to$ `white vinegar with apple juice` (1:1).

5. **Thickening Agents**:
   - `cornstarch` $\to$ `all-purpose flour` (1:2 ratio, 1 tbsp cornstarch = 2 tbsp flour), `arrowroot powder` (1:1).
   - `all-purpose flour` (thickening) $\to$ `cornstarch` (1:0.5 ratio, 2 tbsp flour = 1 tbsp cornstarch).

6. **Herbs & Aromatics**:
   - `garlic` $\to$ `garlic powder` (1 clove = 0.125 tsp), `shallots` (1 clove = 0.5 shallot).
   - `onion` $\to$ `onion powder` (1 medium onion = 1 tbsp powder), `shallots` (1:1).
   - `fresh basil` $\to$ `dried basil` (1 tbsp fresh = 1 tsp dried).
   - `fresh oregano` $\to$ `dried oregano` (1 tbsp fresh = 1 tsp dried).
   - `fresh ginger` $\to$ `ground ginger` (1 tbsp fresh = 0.25 tsp ground).
   - `cilantro` $\to$ `flat-leaf parsley with lime zest` (1:1).

7. **Pantry Staples & Sweeteners**:
   - `brown sugar` $\to$ `white sugar with molasses` (1 cup sugar + 1 tbsp molasses), `white sugar` (1:1).
   - `honey` $\to$ `maple syrup` (1:1 plant-based), `agave nectar` (1:1 plant-based).
   - `chicken broth` $\to$ `vegetable broth` (1:1), `water with butter and herbs` (1:1).
   - `beef broth` $\to$ `vegetable broth with soy sauce` (1:1 cup = 1 cup broth + 1 tsp soy sauce).
   - `soy sauce` $\to$ `tamari` (1:1 gluten-free), `coconut aminos` (1:1).
   - `tomato sauce` $\to$ `tomato paste with water` (1:1), `pureed canned tomatoes` (1:1).

---

## 4. Dietary Filtering & Safety Guarantee

Substitutions strictly enforce active dietary restrictions:
- **`dietary_preference = "vegan"`**:
  - Animal-derived substitutes are strictly eliminated (e.g. cow milk, cream, dairy butter, cheese, honey).
  - Plant-based alternatives are selected: `milk` $\to$ `soy milk` / `almond milk`; `butter` $\to$ `margarine` / `olive oil`; `parmesan` $\to$ `nutritional yeast`; `honey` $\to$ `maple syrup`.
- **`dietary_preference = "vegetarian"`**:
  - Meat and seafood derivatives are strictly eliminated: `chicken broth` $\to$ `vegetable broth` (never beef broth).
- **Hallucination Prevention**:
  - If no compatible substitution exists in the knowledge base, the system returns an empty list (`[]`). It **never fabricates** a replacement.

---

## 5. Context & Use-Case Awareness

Ingredients perform different culinary roles depending on the cooking technique. The system analyzes the recipe's title and directions text to infer the primary context:
- `baking`: prioritizes moisture retention and structural binding (e.g., `butter` in cookies $\implies$ `margarine` or `applesauce`).
- `frying`: prioritizes heat stability and smoke point (e.g., `butter` in skillet $\implies$ `olive oil` or `vegetable oil`).
- `sauces`: prioritizes emulsification and thickening (e.g., `cornstarch` in soup $\implies$ `all-purpose flour` slurry).
- `general`: balanced default when multiple or neutral methods are used.

---

## 6. Ratio Handling & Confidence Levels

1. **Explicit Quantified Ratios**:
   - Exposed as clear conversion multipliers (e.g., `1:1`, `1:0.75`, `1 tbsp fresh = 1 tsp dried`).
   - Ratios are only provided when backed by standardized culinary literature; otherwise stored as `None` (null).
2. **Confidence Calibration**:
   - **`high`**: Direct culinary equivalent with near-identical functional performance (e.g., lime juice for lemon juice, margarine for butter, soy milk for milk).
   - **`medium`**: Functional substitute with minor flavor or texture variation (e.g., applesauce for butter, nutritional yeast for parmesan).
   - **`low`**: Emergency fallback (e.g., water with seasonings).

---

## 7. API Representation

In `POST /api/recommendations`, each recipe item includes:

```json
{
  "recipe_id": 1333578,
  "title": "Salsa Cruda For Pasta",
  "missing_ingredients": ["parmesan cheese"],
  "missing_count": 1,
  "substitutions": [
    {
      "missing_ingredient": "parmesan cheese",
      "substitute": "pecorino romano",
      "ratio": "1:1",
      "confidence": "high",
      "reason": "Aged sheep's milk hard cheese providing identical savory umami, crystalline texture, and grateability.",
      "use_case": "general",
      "dietary_compatible": true,
      "notes": "Pecorino is slightly saltier; adjust recipe salt downward.",
      "source": "Italian Culinary Standards"
    }
  ],
  "explanation": "Recommended because you have 4 of 5 recipe ingredients available, and the recipe uses 4 of your 5 relevant pantry ingredients. Personalization: matches your Italian cuisine preference (+15.0 pts, high confidence). Substitutions: Missing parmesan cheese: pecorino romano is suggested as a high-confidence alternative (1:1) because aged sheep's milk hard cheese providing identical savory umami, crystalline texture, and grateability."
}
```

---

## 8. Evaluation Summary

Evaluated using [evaluate_substitutions.py](file:///c:/Users/sward/AI-Powered-Pantry-Recipe-Assistant/backend/tests/evaluate_substitutions.py):
- **Curated Entries**: 51
- **Common Ingredient Coverage**: **100.0%** (25/25 evaluated)
- **High-Confidence Ratio**: **100.0%**
- **Hallucination Prevention (Negative Controls)**: **100.0%** (0 false substitutions on exotic ingredients)
- **Vegan Dietary Compliance**: **100.0%** (all dairy replacements strictly switched to plant-based)
- **Latency Overhead**: **< 1 millisecond** (in-memory indexed dictionary lookup)
