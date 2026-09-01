---
name: lightrag-engine
description: Dual-level Knowledge Graph and Vector Hybrid RAG system. Provides dual-level retrieval: low-level entity-relationship extraction and high-level theme/topic summarization.
---

# LightRAG: Dual-Level Hybrid RAG

An advanced Retrieval-Augmented Generation (RAG) architecture that unifies entity-relationship knowledge graphs with vector similarity search to deliver complete, hallucination-resistant answers across both granular factual queries and broad architectural overviews.

## Dual-Level Retrieval Architecture

```
                      [User Query]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    [Low-Level Retrieval]       [High-Level Retrieval]
    • Specific Entities         • Broad Themes & Topics
    • Exact Relationships       • Architecture Summaries
    • Function Calls / Props    • Subsystem Interplay
             │                           │
             └─────────────┬─────────────┘
                           ▼
              [Synthesized Hybrid Context]
                           │
                           ▼
                  [Accurate Generation]
```

## Retrieval Modes

1. **Low-Level Query (`query-low`)**: Retrieves specific entities, parameters, function signatures, and precise direct connections.
2. **High-Level Query (`query-high`)**: Retrieves abstract themes, architectural decisions, and domain-wide summaries.
3. **Hybrid Mode (`hybrid`)**: Merges both granular entity chains and overarching system concepts for comprehensive reasoning.

## Commands & Workflows

- `/lightrag index <directory>`: Extract entities, build knowledge graph, and compute embeddings for a target repo.
- `/lightrag query-low <query>`: Execute entity-level granular search.
- `/lightrag query-high <query>`: Execute broad structural/thematic query.
- `/lightrag hybrid <query>`: Execute combined dual-level retrieval.
