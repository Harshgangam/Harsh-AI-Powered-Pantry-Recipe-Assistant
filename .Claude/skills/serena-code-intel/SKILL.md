---
name: serena-code-intel
description: IDE-level code intelligence and semantic symbol analysis toolkit. Provides AST-based symbol navigation, definition/reference lookup, call-graph tracing, and type-safe refactoring.
---

# Serena: Semantic Code Intelligence

An advanced code navigation and semantic intelligence toolkit that equips AI agents with IDE/LSP-grade understanding of codebases: AST node analysis, cross-file symbol indexing, call-hierarchy traversal, and type-safe structural modifications.

## Capabilities & MCP Tools

### 1. Symbol-Aware Search & Navigation
- Jump to precise symbol definitions (functions, classes, interfaces, enums, types) across large repositories without fuzzy grep noise.
- Extract complete class hierarchies, method signatures, and docstrings.

### 2. Bidirectional Call Graph Tracing
- **Incoming Calls (`trace-callers`)**: Identify every location where a function or method is invoked across all project files before making breaking signature edits.
- **Outgoing Calls (`trace-callees`)**: Enumerate all external and internal functions invoked by a target routine.

### 3. Structural Refactoring
- Rename symbols project-wide with full awareness of scopes, shadowing, and module exports.
- Extract functions, inline variables, and reorder parameters while updating all references safely.

## Protocol & Workflows

```
Step 1: Symbol Identification
        `serena_lookup_symbol(name="processPayment")`
Step 2: Reference & Scope Analysis
        `serena_find_references(symbol_id="srv.PaymentService.processPayment")`
Step 3: Call Graph Verification
        `serena_get_call_hierarchy(direction="incoming")`
Step 4: Executing Structural Edit
        `serena_apply_rename(old="processPayment", new="executePaymentTransaction")`
Step 5: Type Check Verification
        Run compiler/typechecker to verify 0 errors.
```

## Commands & Triggers

- `/serena find-symbols <query>`: Search symbols by name, kind, and namespace.
- `/serena trace-callers <symbol>`: Trace all inbound invocations of a function or class.
- `/serena refactor-symbol <old> <new>`: Execute a type-safe project-wide rename refactor.
- `/serena inspect-type <type-or-interface>`: Retrieve full AST interface definitions and members.
