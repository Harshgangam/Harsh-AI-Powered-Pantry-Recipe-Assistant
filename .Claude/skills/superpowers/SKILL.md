---
name: superpowers
description: Agentic engineering discipline framework. Enforces rigorous engineering habits: Test-Driven Development (TDD), root-cause debugging, verified step execution, and gate-checked code modifications.
---

# Superpowers: Disciplined Agentic Engineering

A software engineering methodology and habit framework for AI agents. Rather than making assumptions, Superpowers wraps the agent in disciplined engineering workflows: test-first implementation, systematic bug isolation, small verifiable commits, and multi-stage review gates.

## Core Disciplines

### 1. Test-Driven Development (TDD) Mandatory Protocol
- **Red Phase**: Write a minimal, failing unit/integration test that precisely captures the target requirement or reproduces the reported defect. Run the test and prove it fails with the expected error.
- **Green Phase**: Write the smallest possible implementation to pass the test. Run the test suite and prove it passes.
- **Refactor Phase**: Clean up the code, remove duplication, and optimize structure while keeping tests green.

### 2. Systematic Root-Cause Debugging
- **Never guess fixes**: Do not make speculative code edits hoping they resolve a bug.
- **Isolate the Failure**: Reproduce the failure with a deterministic test case or CLI command.
- **Inspect State**: Trace variables, stack frames, network payloads, or database state at the point of failure.
- **Formulate & Test Hypothesis**: Formulate a single testable hypothesis, test it, and verify resolution before committing changes.

### 3. Stepwise Plan-First Execution
- Break large tasks into discrete, logically ordered work units.
- State explicitly what file will be touched, what lines will change, and how each step is verified.
- Run tests and static analysis after every single edit.

## Operational Workflow

```
[User Request] 
      │
      ▼
[1. Deep Research] ─── (Trace Call Graphs & Contracts)
      │
      ▼
[2. Implementation Plan] ─── (List exact diffs & Verification Steps)
      │
      ▼
[3. Failing Test (Red)] ─── (Verify Expected Failure)
      │
      ▼
[4. Minimal Fix (Green)] ─── (Run Test Suite)
      │
      ▼
[5. Refactor & Lint] ─── (Keep Suite Green)
      │
      ▼
[6. Review Gate & Proof] ─── (Deliver Verified Output)
```

## Commands & Triggers

- `/superpowers plan`: Create a structured, testable engineering plan for complex features.
- `/superpowers tdd <feature>`: Execute the red-green-refactor loop for a feature or module.
- `/superpowers debug <error>`: Initiate systematic bug isolation without guessing.
- `/superpowers review`: Conduct a strict code review checking for regressions, types, and test coverage.
