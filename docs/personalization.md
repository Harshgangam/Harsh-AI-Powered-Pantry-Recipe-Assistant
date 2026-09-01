# Milestone 3: Personalization & Derived Metadata Architecture

## 1. Executive Summary & Critical Dataset Limitation

The RecipeNLG dataset (~2.23 million recipes) contains raw recipe titles, ingredients, directions, and normalized ingredient NER tags. **It does NOT contain structured ground-truth fields for:**
- `cuisine`
- `dietary_preference` (e.g., vegetarian, vegan, gluten-free)
- `cooking_time` (e.g., active preparation or cooking duration)

> [!IMPORTANT]
> **Derived Metadata Disclaimer**: All metadata fields stored in `data/processed/recipe_metadata.sqlite` are **heuristically inferred** from title text, NER entities, and direction clauses. They represent computational estimates and conservative compatibility heuristics—**NOT certified ground-truth dietary or culinary labels**.

Milestone 3 creates an independent **Derived Metadata Layer** that enriches the recipe corpus without modifying the raw RecipeNLG dataset or the inverted ingredient index (`ingredient_index.sqlite`).

---

## 2. Derived Metadata Schema (`recipe_metadata.sqlite`)

Derived attributes are stored in an independent, replaceable SQLite database at `data/processed/recipe_metadata.sqlite`:

```sql
CREATE TABLE IF NOT EXISTS recipe_metadata (
    recipe_id INTEGER PRIMARY KEY,
    cuisine TEXT,
    cuisine_confidence TEXT,
    cuisine_method TEXT,
    dietary_compatibility TEXT,
    dietary_confidence TEXT,
    dietary_method TEXT,
    estimated_time_minutes INTEGER,
    time_confidence TEXT,
    time_method TEXT
);

CREATE INDEX IF NOT EXISTS idx_meta_cuisine ON recipe_metadata(cuisine);
CREATE INDEX IF NOT EXISTS idx_meta_dietary ON recipe_metadata(dietary_compatibility);
CREATE INDEX IF NOT EXISTS idx_meta_time ON recipe_metadata(estimated_time_minutes);
```

### Field Definitions & Semantics

| Field | Type | Possible Values | Semantics |
|---|---|---|---|
| `recipe_id` | `INTEGER` | `0` .. `2,230,558` | Primary key referencing `recipes.parquet`. |
| `cuisine` | `TEXT` | `Italian`, `Mexican`, `Indian`, `Chinese`, etc., or `NULL` | Inferred cultural/regional cuisine family. |
| `cuisine_confidence` | `TEXT` | `high`, `medium`, or `NULL` | High (explicit title keyword), Medium (signature ingredient co-occurrence). |
| `cuisine_method` | `TEXT` | `title_keyword:<kw>`, `signature_profile:<terms>`, or `insufficient_evidence` | Audit trail of evidence used for inference. |
| `dietary_compatibility` | `TEXT` | `non_vegetarian`, `vegetarian_compatible`, `vegan_compatible` | Inferred dietary compatibility based on ingredient exclusions. |
| `dietary_confidence` | `TEXT` | `high`, `medium`, `low` | High for detected meat exclusions; Medium/Low for absence-based heuristics. |
| `dietary_method` | `TEXT` | `detected_meat_or_seafood:<item>`, `detected_dairy_or_eggs:<item>`, `no_animal_ingredients_detected` | Explicit evidence string. |
| `estimated_time_minutes`| `INTEGER` | Positive integer (e.g. `25`, `45`) or `NULL` | Estimated active cooking duration extracted from directions. |
| `time_confidence` | `TEXT` | `high`, `medium`, or `NULL` | High (single active cooking verb), Medium (sum of multiple cooking steps). |
| `time_method` | `TEXT` | `single_step_regex:<details>`, `multi_step_sum:<details>`, or `no_explicit_duration_found` | Extraction method and step breakdown. |

---

## 3. Derivation Methodologies

### 3.1. Conservative Cuisine Derivation
The cuisine classifier avoids forced categorization and classifies a recipe only when defensible lexical or culinary evidence exists:
1. **High Confidence (Title Keywords)**:
   - Matches whole-word tokens in recipe title (e.g. `"Chicken Tikka Masala"` $\implies$ Indian, `"Spaghetti Carbonara"` $\implies$ Italian, `"Tacos al Pastor"` $\implies$ Mexican, `"Pad Thai"` $\implies$ Thai).
2. **Medium Confidence (Signature Ingredient Co-occurrence)**:
   - Evaluates combinations of regional ingredients (e.g. `cumin` + `coriander` + `turmeric` + `garam masala` $\implies$ Indian; `soy sauce` + `sesame oil` + `ginger` $\implies$ Chinese; `tortilla` + `salsa` + `black beans` $\implies$ Mexican).
3. **Insufficient Evidence Guard**:
   - If no profile or title matches, `cuisine` is stored as `NULL` (`unknown`). Recipes are never arbitrarily forced into a classification.

### 3.2. Dietary Compatibility Derivation
1. **Explicit Meat & Seafood Exclusions (`non_vegetarian`)**:
   - Detects red meat (beef, pork, lamb, bacon, sausage), poultry (chicken, turkey, duck), fish (salmon, tuna, cod), shellfish (shrimp, crab, lobster), and animal by-products (gelatin, lard, meat broths).
   - Assigned **`high` confidence** due to explicit keyword presence.
2. **Dairy & Egg Exclusions (`vegetarian_compatible`)**:
   - Detects milk, butter, cheeses, eggs, cream, yogurt, and honey in recipes where no meat was detected.
   - Assigned **`medium` confidence**.
3. **Absence-Based Heuristic (`vegan_compatible`)**:
   - Assigned when no animal-derived items are identified in the recipe NER.
   - Assigned **`low` confidence** because absence of detected ingredients does not preclude hidden animal additives (e.g., bone-char processed sugar, unlisted emulsifiers, animal rennet).

### 3.3. Cooking-Time Extraction
1. **Active Cooking Sentence Extraction**:
   - Scans directions text for active cooking verbs: `bake`, `cook`, `simmer`, `boil`, `fry`, `roast`, `saute`, `broil`, `microwave`, `steam`, `grill`.
   - Filters out resting/cooling verbs (e.g. `chill`, `refrigerate`, `marinate`, `freeze`) to avoid confounding passive waiting with active cooking.
2. **Duration Normalization & Aggregation**:
   - Converts hours to minutes ($1 \text{ hr} = 60 \text{ min}$).
   - Maps ranges (e.g., `"20 to 25 minutes"`) to the upper bound ($25 \text{ min}$) to ensure sufficient cooking.
   - Sums sequential active cooking intervals (e.g., saute 5 min + bake 25 min = 30 min).
   - Discards ambiguous or unrealistic durations (> 24 hours / 1440 min).
3. **Unknown Time Guard**:
   - If directions lack an explicit active cooking duration, `estimated_time_minutes` is stored as `NULL`.

---

## 4. Personalization Scoring & Ranking Model

The recommendation system preserves the foundational pantry compatibility from Milestone 2 and layers personalization on top:

$$\text{Base Score} = 0.6 \cdot \text{IMS} + 0.4 \cdot \text{PUS}$$

### 4.1. Dietary Hard Filtering
When an explicit dietary restriction is specified:
- **`dietary_preference = "vegetarian"`**: Any candidate recipe classified as `non_vegetarian` is **strictly excluded** from the candidate pool.
- **`dietary_preference = "vegan"`**: Any candidate recipe classified as `non_vegetarian` or `vegetarian_compatible` is **strictly excluded**.
- Unknown compatibility is retained with neutral scoring.

### 4.2. Cuisine Match Bonus
When `cuisine` is specified:
- **High Confidence Match**: $+15.0$ points
- **Medium Confidence Match**: $+10.0$ points
- **Mismatch or Unknown Cuisine**: $+0.0$ points (neutral)

### 4.3. Cooking-Time Bonus & Overage Penalty
When `max_cooking_time_minutes` is specified:
- **Within Maximum Time**:
  $$\text{TimeBonus} = 10.0 \times \left(\frac{\text{max\_time} - \text{estimated\_time}}{\text{max\_time}}\right), \quad \text{clamped to } [0.0, 10.0]$$
  Faster recipes receive a larger reward while respecting the user's upper limit:
  - At $0.5 \times \text{max}$: $+5.0$ points
  - At $0.75 \times \text{max}$: $+2.5$ points
  - At $\text{max}$: $+0.0$ points
- **Exceeding Maximum Time**:
  $$\text{OveragePenalty} = \min\left(15.0, 0.2 \times (\text{estimated\_time} - \text{max\_time})\right)$$
- **Unknown Time**: $+0.0$ points (neutral).

### 4.4. Final Combined Personalized Score
$$\text{Personalized Score} = \max\left(0.0, \min\left(100.0, \text{Base Score} + \text{Cuisine Bonus} + \text{Time Adjustment}\right)\right)$$

### 4.5. Deterministic 4-Level Tie-Breaking Sort
1. `recommendation_score` $\downarrow$ (Personalized Score)
2. `ims` $\downarrow$ (Ingredient Match Score)
3. `pus` $\downarrow$ (Pantry Utilization Score)
4. `recipe_id` $\uparrow$ (Canonical ID tie-breaker)

---

## 5. Foundational Pantry Guarantee

The maximum achievable personalization bonus is bounded:
$$\text{Max Bonus} = 15.0 \, (\text{Cuisine}) + 10.0 \, (\text{Time}) = +25.0 \text{ points}$$

Consequently, a recipe with poor pantry match (e.g., $\text{IMS} = 20\% \implies \text{Base} \approx 20$) cannot exceed a strongly pantry-compatible recipe (e.g., $\text{IMS} = 90\% \implies \text{Base} \approx 90$), even if the former perfectly satisfies all cuisine and timing preferences. Pantry compatibility remains the bedrock of recommendation.

---

## 6. Limitations & Future Directions

1. **Rule-Based Exclusion Scope**:
   - Certain rare or regional animal products (e.g. specialty fish pastes, animal-derived enzymes in cheeses) may not appear in simple NER strings.
2. **Single Step vs. Total Prep**:
   - Recipe directions often state baking or boiling time but omit chopping/prep time. The system strictly estimates *active cooking duration*, not total labor time.
3. **Future AI/LLM Integration**:
   - The emitted `explanation_data` and structured metadata allow future LLM agents to verify borderline ingredients and synthesize conversational explanations without recomputing ranking vectors.
