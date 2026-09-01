---
name: graphify-ast
description: Deterministic AST-based code knowledge graph generator. Transforms complex codebases, schemas, and dependencies into queryable graph relationships without external vector databases.
---

# Graphify: Code Knowledge Graph Engine

A high-performance code comprehension engine that analyzes source files via Abstract Syntax Trees (AST) and constructs a deterministic, queryable knowledge graph of codebases. It maps function definitions, class inheritances, module imports, SQL schemas, and endpoint routes.

## Core Advantages over Vector RAG

- **100% Deterministic Recall**: No semantic similarity hallucinations; edges represent exact import statements, type annotations, and function calls.
- **Zero Vector Database Setup**: Operates entirely locally via lightweight graph structures (SQLite / JSON / GraphML).
- **Multi-Language Support**: Parsers for TypeScript/JavaScript, Python, Go, Rust, Java, C++, and SQL schemas.

## Graph Data Model

```
[Module: payment.ts] ──(defines)──> [Function: processCharge]
       │                                     │
       │(imports)                            │(calls)
       ▼                                     ▼
[Module: stripe.ts]                [Function: stripe.charges.create]
```

## Commands & Workflows

- `/graphify build`: Parse all repository files and construct the local knowledge graph.
- `/graphify query <node>`: Query all incoming/outgoing edges for a specific function, class, or route.
- `/graphify inspect <module>`: View structural overview, exported symbols, and dependency tree.
- `/graphify export --format=json`: Export graph data for visualization or subagent ingestion.
