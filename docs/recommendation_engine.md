# Core Pantry-Based Recipe Retrieval & Recommendation Engine

## 1. System Architecture & Recommendation Pipeline

The recommendation system follows a deterministic, pantry-first pipeline designed to prioritize food waste reduction:

```
[User Pantry Ingredients]
          │
          ▼
1. Conservative Normalization & Plural Variant Expansion
          │
          ▼
2. Two-Step Integer Candidate Retrieval (SQLite Inverted Index)
          │ (top K candidate recipe IDs)
          ▼
3. Batch Detail Fetch (Parquet Columnar Store)
          │
          ▼
4. Relevant Pantry Determination across Candidate Set
          │
          ▼
5. Dual Scoring:
   ├── Ingredient Match Score (IMS) -> Recipe completeness
   └── Pantry Utilization Score (PUS) -> Food waste reduction
          │
          ▼
6. Final Weighted Scoring: 0.6 * IMS + 0.4 * PUS
          │
          ▼
7. Deterministic 4-Level Tie-Breaking Sort
          │
          ▼
8. Structured Explanation & Missing Ingredient Generation
          │
          ▼
[Ranked Recipe Recommendations Payload]
```

---

## 2. Mathematical Scoring Formulas

### A. Ingredient Match Score (IMS)

Measures the proportion of a recipe's required ingredients that the user already has in their pantry:

$$\text{IMS}(R, P) = \begin{cases} 
\left( \frac{|R \cap P|}{|R|} \right) \times 100, & \text{if } |R| > 0 \\
0.0, & \text{otherwise}
\end{cases}$$

Where:
- $R$ is the set of normalized NER ingredient entities required by the recipe.
- $P$ is the set of normalized pantry ingredient variants supplied by the user.
- $|R|$ is the total number of ingredients required by the recipe (`ner_count`).
- $|R \cap P|$ is the count of matched recipe ingredients.
- Value range: $[0.0, 100.0]$.

### B. Pantry Utilization Score (PUS)

Measures how effectively a recipe uses the user's available and *relevant* pantry ingredients. Unlike traditional recipe recommenders that only measure recipe completeness, PUS directly targets food waste reduction by favoring recipes that consume a greater fraction of the user's on-hand ingredients.

First, the set of **Relevant Pantry Ingredients** ($P_{\text{relevant}}$) is defined as the subset of the user's normalized pantry ingredients that occur in at least one retrieved candidate recipe:

$$P_{\text{relevant}} = \{ p \in P \mid \exists r \in \text{Candidates}, p \in R(r) \}$$

Then, the Pantry Utilization Score is defined as:

$$\text{PUS}(R, P_{\text{relevant}}) = \begin{cases}
\left( \frac{|R \cap P_{\text{relevant}}|}{|P_{\text{relevant}}|} \right) \times 100, & \text{if } |P_{\text{relevant}}| > 0 \\
0.0, & \text{otherwise}
\end{cases}$$

> [!NOTE]
> Defining PUS over $P_{\text{relevant}}$ rather than the raw pantry $P$ ensures that unrelated pantry items (e.g. baking powder when cooking a pasta dish) do not unfairly penalize all candidate recipes.

### C. Final Recommendation Score & Deterministic Ranking

The overall recommendation score is a weighted combination of recipe feasibility (IMS) and food waste minimization (PUS):

$$\text{Score}(R, P) = w_{\text{IMS}} \cdot \text{IMS}(R, P) + w_{\text{PUS}} \cdot \text{PUS}(R, P_{\text{relevant}})$$

**Default Weights**:
- $w_{\text{IMS}} = 0.6$
- $w_{\text{PUS}} = 0.4$
- Configurable via `backend.app.config.Settings` (`IMS_WEIGHT`, `PUS_WEIGHT`).

**Deterministic 4-Level Tie-Breaking**:
To ensure 100% reproducible and deterministic recommendations:
1. `recommendation_score` $\downarrow$ (Descending)
2. `ims` $\downarrow$ (Descending)
3. `pus` $\downarrow$ (Descending)
4. `recipe_id` $\uparrow$ (Ascending)

### D. Missing Ingredients

For every returned recipe, the missing ingredients list is computed as the strict set difference:

$$\text{Missing}(R, P) = R \setminus P$$

---

## 3. Conservative Normalization & Plural Handling Rules

User input undergoes conservative normalization:
1. **Case & Whitespace**: Lowercased, leading/trailing whitespace removed, consecutive whitespace collapsed to a single space.
2. **Punctuation**: Harmless punctuation (`.,;:#?!*~()[]{}`) stripped.
3. **Plural Handling**:
   - Regular plurals are converted to singular form:
     - `-ies` $\to$ `-y` (*cherries* $\to$ *cherry*, *strawberries* $\to$ *strawberry*)
     - `-es` after sibilants or o (*tomatoes* $\to$ *tomato*, *potatoes* $\to$ *potato*)
     - `-s` (*onions* $\to$ *onion*, *eggs* $\to$ *egg*, *carrots* $\to$ *carrot*)
   - **Protected Singular Food Items**: Words ending in 's' that are not plurals are explicitly guarded against stem truncation (*asparagus*, *molasses*, *hummus*, *couscous*, *citrus*, *watercress*, *swiss cheese*, *curry leaves*).
4. **Non-Collapsing Guarantee**:
   - Multi-word ingredient specifications are never collapsed semantically (e.g. `"chicken breasts"` is never collapsed to `"chicken"`; `"garlic powder"` is never collapsed to `"garlic"`).
   - Safe dual-lookup variants (both singular and plural forms) are queried in SQLite to match either form present in RecipeNLG.

---

## 4. Candidate Retrieval Strategy & Performance

Rather than scanning 2.23 million Parquet rows at request time, candidate generation executes in two steps:
1. **Ingredient ID Resolution**: Resolves textual ingredient variants to integer IDs in the `ingredients` table via B-Tree index lookup ($\approx 1 \text{ ms}$).
2. **Integer B-Tree Inverted Lookup**: Queries `recipe_ingredients` directly by integer IDs:
   ```sql
   SELECT ri.recipe_id, COUNT(ri.ingredient_id) AS matched_count, rm.ner_count
   FROM recipe_ingredients ri
   JOIN recipes_metadata rm ON ri.recipe_id = rm.recipe_id
   WHERE ri.ingredient_id IN (?, ?, ...)
   GROUP BY ri.recipe_id
   ORDER BY matched_count DESC, (CAST(matched_count AS FLOAT) / rm.ner_count) DESC
   LIMIT 150;
   ```
3. **Selective Parquet Batch Fetch**: Fetches full metadata (title, directions, ingredients) for only the top candidate IDs from `recipes.parquet` via PyArrow dataset projection.

### Benchmark Results (Live 2.23 Million Dataset)

| Scenario | Pantry Size | Candidates Evaluated | Total Latency |
|---|---|---|---|
| 3 Common Ingredients (`garlic`, `onion`, `butter`) | 3 | 150 | ~2.48 s |
| 5 Dinner Ingredients (`chicken breasts`, `garlic`, `sour cream`, `butter`, `pasta`) | 5 | 150 | ~2.48 s |
| 10 Full Pantry Ingredients (`tomato`, `garlic`, `onion`, `basil`, `olive oil`, etc.) | 10 | 150 | ~3.72 s |

---

## 5. Explanation Architecture for Future AI/LLM Integration

Each recommendation includes structured explanation data (`explanation_data`) alongside a deterministic template string:

```json
{
  "explanation": "Recommended because you have 4 of 4 recipe ingredients available, and the recipe uses 4 of your 5 relevant pantry ingredients.",
  "explanation_data": {
    "matched_ingredients": ["chicken breasts", "garlic", "sour cream", "butter"],
    "missing_ingredients": [],
    "matched_count": 4,
    "total_recipe_ingredients": 4,
    "relevant_pantry_used_count": 4,
    "relevant_pantry_total_count": 5,
    "ims": 100.0,
    "pus": 80.0,
    "final_score": 92.0
  }
}
```

This structured output allows future LLM/RAG layers (Milestone 3+) to synthesize conversational, explainable rationales without recomputing scoring metrics.

---

## 6. Dataset Limitations & Future Milestone Strategy

As verified in Milestone 1:
- RecipeNLG does not contain structured fields for `cuisine`, `dietary_preference`, or `cooking_time`.
- In Milestone 2, the `PantryRequest` model strictly exposes only `pantry_ingredients` and `limit`, focusing solely on pantry compatibility and food waste reduction.
- Milestone 3 will introduce deterministic ingredient exclusion taxonomies (for vegetarian/vegan filtering) and signature flavor co-occurrence heuristics (for cuisine categorization), at which point personalization fields will be added.
