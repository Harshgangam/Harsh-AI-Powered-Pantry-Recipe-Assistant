---
name: one-skill-meta
description: Continuous self-improving meta-skill. Monitors active development sessions, detects user corrections, extracts recurring patterns, and synthesizes new skills and rule definitions.
---

# One Skill to Rule Them All: The Meta-Skill

An evolutionary meta-skill for AI agents that observes session transcripts, detects repeated mistakes or user corrections, extracts reusable patterns, and dynamically generates new standardized skill packages to permanently improve future agent performance.

## The Meta-Learning Cycle

```
[Agent Session Execution]
          │
          ▼
[Correction Detection] ─── (Identify moments where user corrected agent)
          │
          ▼
[Pattern Extraction] ─── (Isolate generalizable technique vs. project-specific data)
          │
          ▼
[Skill Synthesis] ─── (Generate new standardized SKILL.md)
          │
          ▼
[Registry Publication] ─── (Add to active skills directory)
```

## Pattern Taxonomy

- **Correction Traps**: Repeated misinterpretations of APIs, frameworks, or user preferences.
- **Compound Workflows**: Multi-step terminal sequences that frequently succeed (e.g. build -> test -> package -> deploy).
- **Domain Heuristics**: Project-specific domain constraints (e.g. "always use UTC timestamps", "all API endpoints must return `{ data, error }`").

## Commands & Workflows

- `/meta extract-patterns`: Analyze recent session logs and summarize learned lessons.
- `/meta synthesize-skill <name> <topic>`: Generate a complete, production-ready `SKILL.md` based on successful session patterns.
- `/meta optimize-rules`: Refine existing project rules to eliminate ambiguity and token bloat.
