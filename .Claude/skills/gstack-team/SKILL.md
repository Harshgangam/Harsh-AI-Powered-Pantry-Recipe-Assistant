---
name: gstack-team
description: Multi-role virtual engineering team framework packaging 23 specialist roles (CEO, Architect, Frontend Lead, QA Lead, SecOps) to execute structured think-plan-build-review lifecycles.
---

# GStack: Virtual Engineering Squad

An opinionated agent orchestration system created by Garry Tan that organizes complex software development into specialized executive, architectural, and engineering personas across structured development phases.

## Specialist Persona Matrix

### Executive & Product Roles
- **/gstack ceo**: Strategic alignment, product-market fit, core user value proposition, ruthlessly cutting non-essential features (MVP prioritization).
- **/gstack cpo / designer**: User journeys, information architecture, onboarding friction reduction, design clarity.

### Architecture & Engineering Roles
- **/gstack architect**: System decomposition, API schema design, database normalization, data-flow diagrams, scalability bottlenecks.
- **/gstack staff-eng**: Code quality standards, concurrency correctness, memory management, dependency hygiene.
- **/gstack frontend-lead**: Component boundaries, state lifting, rendering performance, accessible keyboard/screen-reader flows.
- **/gstack backend-lead**: Transaction boundaries, connection pooling, cache invalidation strategies, idempotent endpoint design.

### Quality & Operational Roles
- **/gstack qa**: Edge case identification, adversarial input testing, stress scenarios, load testing plans, automated test harnesses.
- **/gstack secops**: OWASP Top 10 auditing, authorization bypass checks, secret leak detection, dependency vulnerability scanning.

## The 4-Phase Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. THINK (CEO + Architect)                                   │
│    Validate necessity, identify constraints, define specs    │
├─────────────────────────────────────────────────────────────┤
│ 2. PLAN (Staff Engineer + Designer)                          │
│    Component breakdown, API contracts, milestone breakdown │
├─────────────────────────────────────────────────────────────┤
│ 3. BUILD (Frontend + Backend Leads)                          │
│    TDD implementation, strict typing, clean modular code    │
├─────────────────────────────────────────────────────────────┤
│ 4. REVIEW (QA Lead + SecOps)                                │
│    Stress test, security audit, regression verification     │
└─────────────────────────────────────────────────────────────┘
```

## Commands & Usage

- `/gstack squad <task>`: Run a full lifecycle dispatching the CEO, Architect, Staff Eng, QA, and SecOps sequentially.
- `/gstack ceo <pitch>`: Challenge and sharpen product requirements before writing code.
- `/gstack architect <requirements>`: Formulate high-level system architecture and API contracts.
- `/gstack qa <pr-or-diff>`: Generate thorough edge-case tests and failure scenarios.
- `/gstack secops <file-or-repo>`: Conduct security threat modeling and static vulnerability checks.
