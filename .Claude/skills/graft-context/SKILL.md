---
name: graft-context
description: Persistent codebase context engine. Builds and maintains a live, cached representation of project architecture, drastically reducing agent re-orientation time and token overhead.
---

# Graft: Persistent Codebase Context Engine

A high-efficiency context engine developed by Nanonets that maintains a continuous, cached mental model of the codebase. Instead of forcing coding agents to explore and grep through hundreds of files on every turn, Graft provides instant topological context.

## How Graft Works

1. **Warm Start Execution**: Upon session initialization, Graft loads pre-indexed module boundaries, interfaces, and architecture layers in under 100ms.
2. **Differential Delta Syncing**: Watches file system events (`fs.watch`) and updates only modified AST subtrees, ensuring zero stale context.
3. **Re-Orientation Elimination**: Benchmarks show a 70%+ reduction in preliminary exploratory commands (`ls`, `grep`, `find`) per agent session.

## Operational Workflow

```
[Agent Session Starts]
         │
         ▼
[Graft Fast Load] ─── (Read Cached Codebase Manifest)
         │
         ▼
[Instant Target Resolution] ─── (Directly navigate to exact files requiring edits)
         │
         ▼
[Atomic Edit & Delta Update] ─── (Re-index only modified files)
```

## Commands & Triggers

- `/graft init`: Index the repository and build the initial persistent context cache.
- `/graft sync`: Re-sync modified files and update the symbol manifest.
- `/graft context <task>`: Retrieve the exact minimal set of files and symbols needed for a specific task.
- `/graft cache-status`: Display memory size, tracked files, and cache freshness.
