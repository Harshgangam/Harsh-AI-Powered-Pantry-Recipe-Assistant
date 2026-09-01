---
name: headroom-compression
description: High-ratio context compression layer for AI agents. Compresses tool outputs, compiler logs, file contents, and RAG chunks by 60-95% without loss of technical fidelity.
---

# Headroom: Context Compression Layer

An open-source token reduction and context compression engine designed for agentic workflows. Headroom sits between tool outputs (command executions, large file reads, log streams) and the LLM context window, eliminating redundant tokens while retaining all actionable errors, line numbers, and semantic facts.

## Compression Strategies

1. **Repetitive Log Deduplication**: Collapses 5,000 lines of repeating stack traces into `[Repeated 4,992 times: NullPointerException at ...]`.
2. **Surgical Diff Pruning**: Strips unchanged multi-page context blocks from git diffs, keeping only affected hunks and bounding function signatures.
3. **AST-Aware File Truncation**: When reading large files, preserves declarations, interfaces, and target functions while folding non-relevant implementation bodies.
4. **JSON Schema Folding**: Strips redundant null/empty fields and repetitive array items from large API payloads.

## Operational Benchmarks

- **Compiler & Linter Outputs**: 85-92% token reduction.
- **Git Diffs & Patches**: 60-75% token reduction.
- **Raw API & JSON Responses**: 70-80% token reduction.

## Commands & Triggers

- `/headroom compress <text-or-file>`: Apply compression algorithms to raw text or file payloads.
- `/headroom stats`: Display session compression ratio and estimated tokens/cost saved.
- `/headroom prune-logs <log-file>`: Filter out noise and extract key failure signals.
