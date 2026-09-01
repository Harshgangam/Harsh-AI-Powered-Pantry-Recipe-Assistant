---
name: memory-bank
description: Persistent multi-session memory system and MCP server. Maintains structured markdown files (activeContext, systemPatterns, techContext, decisionLog) to preserve context across chat sessions.
---

# Memory Bank: Multi-Session Persistent Memory

A structured repository memory framework that enables AI agents to maintain comprehensive continuity across multiple coding sessions, team members, and branches by anchoring context in standardized project files.

## The Memory Bank File System

```
memory-bank/
├── projectbrief.md     # Core project requirements, goals, and scope
├── productContext.md   # Why this project exists, target audience, UX goals
├── systemPatterns.md   # System architecture, design patterns, component relationships
├── techContext.md      # Tech stack, dependencies, dev environment, constraints
├── activeContext.md    # Current focus, recent changes, immediate next steps
└── decisionLog.md      # Record of architectural decisions and trade-offs made
```

## Protocol & Rules

1. **Session Start**: The agent reads `activeContext.md` and `systemPatterns.md` before executing user instructions.
2. **Architectural Change**: Whenever an architecture pattern or dependency is added/modified, `systemPatterns.md` and `decisionLog.md` must be updated.
3. **Session End / Task Completion**: The agent updates `activeContext.md` with what was completed and what remains to be done.

## Commands & Triggers

- `/memory-bank init`: Scaffold the standard memory-bank folder and initial files.
- `/memory-bank update`: Synchronize current progress and decisions into `activeContext.md` and `decisionLog.md`.
- `/memory-bank status`: Display a summary of current project status and active focus.
