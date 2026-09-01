# RecipeNLG Dataset Analysis & Pipeline Report

## 1. Project & Dataset Overview

- **Project**: AI-Powered Pantry Recipe Assistant: An Intelligent Food Waste Reduction System
- **Dataset**: [RecipeNLG: A Large Scale Dataset for Semi-Structured Recipe Generation](https://aclanthology.org/2020.inlg-1.4.pdf) (Bień et al., INLG 2020)
- **Source File**: `RecipeNLG_dataset.csv`
- **File Size**: 2,294,981,083 bytes (~2.14 GB / 2.29 GiB on disk)
- **Total Records**: 2,231,142 rows

The dataset contains recipes aggregated from multiple web sources (primarily "Gathered" cookbooks and "Recipes1M"). Each record includes the recipe title, ingredient lists with measurements, preparation directions, source URL, and most importantly, an extracted **Named Entity Recognition (NER)** list of food items.

---

## 2. Dataset Schema (Verified from Source CSV)

| Field | Type in CSV | Description | Example |
|---|---|---|---|
| *(unnamed col 0)* | Integer | Row index (0-indexed) | `0` |
| `title` | Text | Recipe title / name | `"No-Bake Nut Cookies"` |
| `ingredients` | JSON/Python list string | Raw ingredient list with quantities and units | `["1 c. firmly packed brown sugar", "1/2 c. evaporated milk"]` |
| `directions` | JSON/Python list string | Ordered preparation and cooking steps | `["In a heavy 2-quart saucepan...", "Boil 5 minutes..."]` |
| `link` | Text | Source recipe URL | `www.cookbooks.com/Recipe-Details.aspx?id=44874` |
| `source` | Text | Origin corpus (`Gathered` or `Recipes1M`) | `"Gathered"` |
| `NER` | JSON/Python list string | Extracted and normalized food item entities | `["brown sugar", "milk", "vanilla", "nuts", "butter"]` |

---

## 3. Dataset Limitations & Missing Attributes

> [!IMPORTANT]
> The RecipeNLG dataset **does not contain structured fields** for:
> 1. **Cuisine Category** (e.g., Italian, Indian, Mexican, Chinese, American)
> 2. **Dietary Category** (e.g., Vegetarian, Vegan, Gluten-Free, Dairy-Free, Halal, Kosher)
> 3. **Cooking / Preparation Time** (no prep time, cook time, or total minutes)
> 4. **Serving Size / Yield** (only occasionally mentioned unstructured inside directions)
> 5. **Nutritional Information** (no calories, macronutrients, or sodium)
> 6. **Difficulty / Skill Level** (no beginner, intermediate, advanced tags)

### Defensible Strategy for Deriving Missing Information in Later Milestones

To satisfy project features such as cuisine filtering, dietary preferences, and cooking time constraints without fabricating data, the following multi-tier approach will be used in subsequent milestones:

1. **Dietary Preference Derivation**:
   - Build deterministic ingredient-exclusion taxonomies (e.g., meat/poultry/seafood lists to flag vegetarian; dairy/egg lists to flag vegan).
   - Because we have 198,385 normalized ingredients in SQLite, a curated dictionary of non-vegetarian and non-vegan food items allows fast, 100% deterministic labeling.
2. **Cuisine Classification**:
   - Heuristic matching based on signature ingredient co-occurrence profiles (e.g., soy sauce + ginger + sesame oil -> East Asian; cumin + coriander + turmeric + garam masala -> Indian; basil + oregano + parmesan -> Italian).
   - Keyword detection on recipe titles.
   - Offline LLM/classifier enrichment for top-ranked candidate recipes.
3. **Cooking Time Estimation**:
   - Regular expression extraction of time mentions from `directions` (e.g., `"bake for 30 minutes"`, `"simmer 15 min"`).
   - In the absence of explicit time, default heuristics based on cooking method and number of steps.

---

## 4. Preprocessing Decisions & Architecture

### A. Memory-Safe Streaming Chunk Pipeline
- Loading the full 2.29 GB CSV into memory causes heavy RAM spikes and Out-Of-Memory risks on standard machines.
- The pipeline processes the dataset in configurable streaming chunks of **50,000 rows** using `pandas.read_csv(chunksize=...)` and `itertuples()`, maintaining near-constant low memory footprint (< 300 MB RAM).

### B. Normalization Rules
1. **NER Normalization**:
   - Lowercase all ingredient entities.
   - Strip leading and trailing whitespace, surrounding quotes, and punctuation.
   - Collapse multiple internal whitespace characters into single spaces.
   - Deduplicate ingredients within each recipe while preserving order.
2. **Missing & Malformed Handling**:
   - Detect `NaN`, empty strings, null representations, and malformed list syntax.
   - Require non-empty title, valid integer ID, non-empty directions, and at least 1 valid ingredient entity in NER.
   - Log any invalid rows to `data/logs/malformed_rows.log` without aborting the pipeline.

### C. Output Storage Formats

#### 1. Columnar Parquet (`data/processed/recipes.parquet`)
- **Format**: Apache Parquet with Snappy compression.
- **Size**: **951.03 MB** (compressed down from 2.29 GB raw CSV, ~58% space savings).
- **Schema**: Strongly typed PyArrow schema with native `list<string>` support for `ingredients`, `directions`, and `ner`.
- **Purpose**: Fast random and batch access by recipe ID during recipe presentation and detail retrieval.

#### 2. Inverted SQLite Index (`data/processed/ingredient_index.sqlite`)
- **Format**: SQLite 3 database with WAL mode and clustered B-Tree indexing.
- **Size**: **861.03 MB**.
- **Schema**:
  - `ingredients(id INTEGER PRIMARY KEY, name TEXT UNIQUE, recipe_count INTEGER)`
  - `recipes_metadata(recipe_id INTEGER PRIMARY KEY, ner_count INTEGER)`
  - `recipe_ingredients(ingredient_id INTEGER, recipe_id INTEGER, PRIMARY KEY (ingredient_id, recipe_id))`
- **Purpose**: Powers sub-millisecond candidate recipe retrieval given a user's pantry contents:
  ```sql
  SELECT ri.recipe_id, COUNT(ri.ingredient_id) AS matched_count, rm.ner_count
  FROM recipe_ingredients ri
  JOIN ingredients i ON ri.ingredient_id = i.id
  JOIN recipes_metadata rm ON ri.recipe_id = rm.recipe_id
  WHERE i.name IN ('garlic', 'onion', 'tomato')
  GROUP BY ri.recipe_id
  HAVING matched_count >= 1
  ORDER BY matched_count DESC, (CAST(matched_count AS FLOAT) / rm.ner_count) DESC
  LIMIT 50;
  ```

---

## 5. Dataset Processing Statistics

Summary of full dataset preprocessing completed on August 29, 2026:

| Metric | Measured Value |
|---|---|
| **Raw Rows Read** | **2,231,142** |
| **Valid Recipes Processed** | **2,230,559** (99.97%) |
| **Malformed Records Skipped** | **583** (0.026%) |
| — Empty NER list after normalization | 580 |
| — Empty recipe title | 3 |
| **Duplicate Recipe IDs** | **0** |
| **Unique Ingredients** | **198,385** |
| **Total Recipe-Ingredient Links** | **18,419,714** |
| **Sources: Gathered** | 1,642,753 recipes |
| **Sources: Recipes1M** | 587,806 recipes |
| **Average Ingredients per Recipe** | ~8.25 |
| **Raw CSV File Size** | 2,294,981,083 bytes (2.14 GB) |
| **Output Parquet Size** | 997,222,404 bytes (951.03 MB) |
| **Output SQLite Index Size** | 902,856,704 bytes (861.03 MB) |
| **Total Pipeline Processing Time** | 315.39 seconds (5.26 minutes) |
| **Processing Throughput** | ~7,074 rows/second |
