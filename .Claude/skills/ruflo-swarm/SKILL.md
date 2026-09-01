---
name: ruflo-swarm
description: Multi-agent swarm meta-harness for coordinating multi-agent topologies, peer-to-peer delegation, distributed task queues, and consensus-driven execution.
---

# Ruflo: Multi-Agent Swarm Harness

An enterprise-grade multi-agent orchestration harness designed for deploying and coordinating agent swarms. Ruflo allows a primary orchestrator to spawn specialized peer workers, manage shared blackboard memory, and synthesize outputs through consensus protocols.

## Swarm Topologies

1. **Hierarchical Swarm**:
   - Master Orchestrator decomposes tasks -> Dispatches to Domain Specialists (DB, Frontend, SecOps) -> Aggregates & verifies results.
2. **Peer Mesh**:
   - Autonomous peer agents collaborate directly via pub/sub messaging channels, passing intermediate work products.
3. **Competitive / Adversarial Verification**:
   - Two or more agents implement the same feature or test independently; an Evaluator agent benchmarks and chooses the optimal implementation.

## Operational Protocol

```
[Master Task]
      │
      ├───> Worker Agent 1 (Backend API) ──────┐
      │                                         │
      ├───> Worker Agent 2 (Frontend UI) ───────┼───> [Shared Blackboard Memory] ───> [Consensus / Merge Gate]
      │                                         │
      └───> Worker Agent 3 (QA & E2E Tests) ────┘
```

## Consensus & Quality Gates

- **Quorum Verification**: Critical changes require approval from both the Implementation Agent and an Independent Auditor Agent.
- **Isolated Workspaces**: Each sub-agent operates in an isolated git branch or worktree to prevent filesystem collision.
- **Failover & Self-Healing**: If a sub-agent gets stuck or errors out, the swarm supervisor detects the timeout and respawns the worker with error context.

## Commands & Triggers

- `/ruflo swarm-init <topology>`: Initialize a swarm configuration (hierarchical, mesh, adversarial).
- `/ruflo dispatch <task> --workers=<n>`: Break down a task and dispatch parallel sub-agents.
- `/ruflo consensus`: Evaluate competing agent outputs and merge the winning implementation.
- `/ruflo monitor`: Display live telemetry, agent states, and active subagent conversation channels.
