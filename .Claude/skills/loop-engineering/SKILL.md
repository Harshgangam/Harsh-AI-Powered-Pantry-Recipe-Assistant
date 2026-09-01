---
name: loop-engineering
description: Autonomous loop orchestration framework. Implements closed-loop state machines (Discover -> Assign -> Verify -> Persist -> Handoff) with safety brakes and human-in-the-loop controls.
---

# Loop Engineering: Autonomous Agent Loops

A structured engineering framework for building reliable, self-monitoring autonomous agent loops. It replaces brittle single-prompt chains with robust, observable state machines capable of sustained autonomous operation while preventing infinite loops and catastrophic drift.

## The 5-Stage Autonomous Loop

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DISCOVER                                                 │
│    Inspect project state, scan backlog, detect errors/todos │
├─────────────────────────────────────────────────────────────┤
│ 2. ASSIGN                                                   │
│    Formulate discrete sub-task, select tools & parameters   │
├─────────────────────────────────────────────────────────────┤
│ 3. EXECUTE & VERIFY                                         │
│    Perform modification, run automated tests & assertions  │
├─────────────────────────────────────────────────────────────┤
│ 4. PERSIST                                                  │
│    Commit state, record execution log, update task tracker  │
├─────────────────────────────────────────────────────────────┤
│ 5. HANDOFF / RE-ENTRY                                       │
│    Check termination condition or loop to next item         │
└─────────────────────────────────────────────────────────────┘
```

## Safety Brakes & Invariants

1. **Max Iteration Bounds**: Strict ceiling on consecutive loop iterations (N <= 20) before requiring explicit user confirmation.
2. **Cost & Token Circuit Breakers**: Automatic halt if token burn exceeds budget threshold.
3. **No-Progress Watchdog**: If 3 consecutive iterations produce failing tests or identical file diffs, the loop suspends and requests human clarification.
4. **State Snapshotting**: Each step creates an immutable git checkpoint allowing instant rollback if an invariant is violated.

## Commands & Usage

- `/loop init <goal>`: Define a multi-step objective with acceptance criteria and loop boundaries.
- `/loop run`: Start the autonomous execution loop.
- `/loop step`: Execute a single cycle (Discover -> Assign -> Verify -> Persist) and pause for inspection.
- `/loop status`: View current iteration index, progress towards goal, and circuit breaker health.
