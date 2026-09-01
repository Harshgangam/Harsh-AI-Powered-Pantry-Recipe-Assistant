# Milestone 6: AI-Assisted Grounded Recipe Guidance & Structured RAG Layer

## Executive Summary

Milestone 6 introduces an **AI-Assisted Grounded Recipe Guidance & Structured RAG Layer** (also termed **Entity-Grounded RAG**) to the AI-Powered Pantry Recipe Assistant. 

Crucially, the generative AI layer **does not replace or override** the deterministic recommendation engine developed in Milestones 1–5. Instead, it serves as an interactive, grounded explanatory and culinary guidance lens built on top of the deterministic foundation.

---

## 1. Core Architectural Principle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    DETERMINISTIC RETRIEVAL & SCORING ENGINE                     │
│                        (Milestones 1–5 Foundation)                              │
│                                                                                 │
│  - Candidate Retrieval: SQLite inverted index via clustered B-Tree              │
│  - Mathematical Scoring: Ingredient Match Score (IMS) & Pantry Utilization (PUS)│
│  - Preference Guidance: Bounded cuisine bonus, time adjustment, diet filter     │
│  - Missing Ingredients: Exact set difference (recipe_ner - pantry)              │
│  - Substitutions: Curated Knowledge Base (51 entries, ratios & reasons)         │
│  - 4-Level Deterministic Tie-Breaking & Ranking                                 │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Authoritative Recipe Context
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│             STRUCTURED RAG / ENTITY-GROUNDED AI GUIDANCE LAYER                  │
│                              (Milestone 6)                                      │
│                                                                                 │
│  - Context Assembler: Assembles verified ground truth from Parquet & SQLite     │
│  - Grounding System Prompt: Strict negative constraints against hallucinations  │
│  - Pluggable LLM Gateway: Google Gemini / OpenAI-compatible / MockLLMClient     │
│  - Interactive Capabilities:                                                    │
│      1. Recommendation Explanation ("Why was this recipe recommended?")        │
│      2. Instruction Simplification ("Break down into simple beginner steps")    │
│      3. Pantry-Aware Guidance ("What should I prep first?")                     │
│      4. Grounded Recipe Q&A ("Can I make this without basil?")                  │
│  - Unverified Substitution Refusal: Explicitly declines unverified substitutes │
└─────────────────────────────────────────────────────────────────────────────────┘
```

The system strictly enforces this separation of concerns:
- **The deterministic engine decides**: what recipes match, how they rank, what is missing, and what curated substitutes exist.
- **The Generative AI explains and guides**: translating structured relational records into natural-language cooking instructions, prep sequences, and grounded Q&A.

---

## 2. Structured RAG vs. Vector-Database RAG

In traditional unstructured document QA, vector retrieval (embeddings in FAISS/Chroma) is used to locate relevant chunks across large unstructured corpora. 

In this recipe assistant, **Structured RAG (Entity-Grounded RAG)** was selected as the superior architectural pattern for the following reasons:

1. **The Recipe is Already Identified**: When a user seeks guidance, they have already selected a specific ranked recipe (e.g. *Bowtie Pasta & Mushrooms*).
2. **Relational Ground Truth**: A recipe consists of sequential step-by-step directions, exact ingredient proportions, and curated substitution relationships. Vector chunking fragments these relationships and loses step order.
3. **No Irrelevant Chunk Retrieval**: Direct entity retrieval retrieves the exact recipe record from Parquet, derived metadata from SQLite, and verified substitutions from the curated knowledge base, reducing irrelevant context retrieval.
4. **Academic Precision**: While structured retrieval provides the LLM with the authoritative application context, hallucination controls and negative prompts are applied to mitigate generative unfaithfulness without falsely claiming complete correctness of generated language.
5. **Zero Infrastructure Overhead**: No vector database service, zero embedding latency, and sub-millisecond retrieval of the context packet directly from existing local databases.

---

## 3. Assembled Structured Context Packet

For each query, the backend `ContextAssembler` compiles the following authoritative packet:

```yaml
=== RECIPE CONTEXT (AUTHORITATIVE GROUND TRUTH) ===
Recipe ID: 1316605
Title: Bowtie Pasta & Mushrooms
Cuisine: Italian (Confidence: high)
Dietary Compatibility: vegan_compatible (Confidence: low)
Estimated Active Cooking Time: 5 minutes

=== PANTRY MATCH & SCORING ===
Matched Pantry Ingredients (3): pasta, garlic, olive oil
Missing Recipe Ingredients (2): mushrooms, fresh basil
Ingredient Match Score (IMS): 60.0%
Pantry Utilization Score (PUS): 100.0%
Recommendation Score: 91.0

=== CURATED KNOWLEDGE BASE SUBSTITUTIONS (VERIFIED) ===
- Missing 'fresh basil': Use 'dried basil' (Ratio: 1:0.33) [Confidence: high]. Reason: Concentrated essential oils in dried herbs infuse flavor into warm pasta.
- Missing 'mushrooms': No verified substitute available in knowledge base.

=== RAW INGREDIENTS LIST ===
1. 2 cups bowtie pasta
2. 1 cup sliced mushrooms
3. 2 cloves garlic, minced
4. 2 tbsp olive oil
5. 1 tsp fresh basil

=== COOKING DIRECTIONS ===
Step 1: Cook bowtie pasta in boiling salted water.
Step 2: Sauté minced garlic and sliced mushrooms in olive oil over medium heat.
Step 3: Toss drained pasta with garlic, mushrooms, and fresh basil; serve warm.
```

---

## 4. Hallucination Controls & Defense-in-Depth

| Threat Category | Safeguard Mechanism | System Behavior |
|---|---|---|
| **Invented Substitutions** (e.g. suggesting apples for mushrooms) | Curated KB Verification + System Prompt Negative Constraint | If queried item is in the curated knowledge base, provides verified ratio and culinary reason. If NOT in curated knowledge base, model explicitly states: *"I cannot confirm a reliable culinary substitute for [ingredient] based on our verified knowledge base. Substituting it may alter the intended flavor or structure."* |
| **Invented Cooking Times** | Context Metadata Constraint | Only quotes the verified `estimated_time_minutes`. If missing, states that original directions do not specify an exact duration. |
| **False Dietary Claims** | Taxonomy Pass-Through | Prohibited from asserting vegetarian/vegan status unless explicitly present in the provided `dietary_compatibility` metadata. |
| **Score Fabrication** | Read-Only Scoring Contract | Prohibited from recalculating or modifying the mathematical IMS, PUS, or recommendation scores. |
| **Prompt Injection** | Input Sanitization & Role Isolation | Max 300 characters on user questions; user text strictly encapsulated in isolated `User Question` section. |
| **Offline / Key Failure** | Deterministic `MockLLMClient` | Graceful fallback ensuring that automated test suites and live presentations work seamlessly without network connectivity or API costs. |

---

## 5. Pluggable LLM Gateway

The backend provides a pluggable gateway with three provider implementations:

1. **Google Gemini (`GeminiClient`)**:
   - Primary cloud provider (`gemini-1.5-flash` or `gemini-2.5-flash`).
   - Connects directly via lightweight HTTP (`httpx`) to the Gemini REST endpoint.
   - Low latency (~400–700ms) with generous free tier.
2. **OpenAI-Compatible (`OpenAIClient`)**:
   - Supports OpenAI (`gpt-4o-mini`), Groq (`llama-3.3-70b-versatile`), or local endpoints (Ollama/vLLM).
3. **Deterministic Mock Client (`MockLLMClient`)**:
   - Zero-dependency, offline fallback generating realistic, grounded culinary responses directly from the structured context.
   - Ensures all tests pass deterministically without paid external API calls.

---

## 6. API Endpoints

### `POST /api/assistant/ask`
Receives structured session information and returns grounded guidance:

**Request Body:**
```json
{
  "recipe_id": 1316605,
  "task": "question",
  "question": "Can I make this without basil?",
  "pantry_ingredients": ["pasta", "garlic", "olive oil"],
  "cuisine": "Italian",
  "dietary_preference": "vegetarian",
  "max_cooking_time_minutes": 30
}
```

**Response Body:**
```json
{
  "recipe_id": 1316605,
  "recipe_title": "Bowtie Pasta & Mushrooms",
  "task": "question",
  "answer": "Yes, according to our curated knowledge base, you can substitute fresh basil with dried basil with a ratio of 1:0.33 (Confidence: high). Reason: Concentrated essential oils in dried herbs infuse flavor into warm pasta.",
  "citations": [
    {
      "source_type": "curated_substitution",
      "detail": "Verified substitute for fresh basil: dried basil (Ratio: 1:0.33)"
    }
  ],
  "substitutions_used": ["fresh basil -> dried basil"],
  "unsupported_inquiries": [],
  "provider": "mock",
  "model": "deterministic-rule-grounded",
  "is_mock": true
}
```

### `GET /api/assistant/status`
Returns provider health and configuration:
```json
{
  "status": "online",
  "provider": "gemini",
  "model": "gemini-1.5-flash",
  "is_mock": false,
  "has_api_key": true
}
```

---

## 7. Frontend Integration

The assistant is embedded directly into `RecipeDetailModal.tsx` via `AiAssistantPanel.tsx`:
- **Header**: Displays "AI Recipe Guidance & Grounded Assistant" with an active "Grounded in Recipe Data" pill.
- **Quick Action Chips**: Single-click triggers for:
  - 💡 *Why this recipe?* (`explain`)
  - 📝 *Simplify instructions* (`simplify`)
  - 🍳 *Pantry prep guidance* (`guidance`)
- **Interactive Q&A Input**: Allows asking specific recipe questions with live character counter (300 chars max) and submit button.
- **Grounding Citations**: Shows clickable entity tags (e.g. 🏷️ *Verified Substitute: dried basil*).
- **Academic Disclaimer Banner**: Emphasizes that advice is grounded in verified recipe directions and curated substitutions, and does not alter ranking scores.

---

## 8. Evaluation Benchmark Results

Automated benchmark executed via `backend/tests/evaluate_assistant.py`:

| Evaluation Metric | Target Benchmark | Measured Result |
|---|---|---|
| **Groundedness Pass Rate** | $\ge 95.0\%$ | **100.0% (5/5)** |
| **Unverified Substitution Refusal Rate** | $100.0\%$ | **100.0% (1/1)** |
| **Mock Inference Latency** | $< 250\text{ ms}$ | **172.91 ms** |
| **Backend Test Suite Pass Rate** | $100.0\%$ | **100.0% (55/55 passed)** |
| **Frontend Test Suite Pass Rate** | $100.0\%$ | **100.0% (10/10 passed)** |
| **TypeScript / Vite Production Build** | Zero errors | **Clean build in 9.28s** |
