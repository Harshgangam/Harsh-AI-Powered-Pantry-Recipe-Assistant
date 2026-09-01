---
name: everything-claude-code
description: Comprehensive agent harness and capability hub. Provides modular instincts, automated pre-commit and post-edit hooks, multi-tool configuration, and production agent workflows.
---

# Everything Claude Code (ECC) Harness

A comprehensive ecosystem and harness standard for AI coding agents. ECC bundles battle-tested instincts, lifecycle hooks, cost-aware model routing, and specialized workflow recipes into a single cohesive operating layer.

## Architecture & Subsystems

### 1. Agent Instincts & Rules Engine
- Declarative behavioral rules loaded per repository (`.claude/rules/*.md`).
- Context-aware rule injection: Frontend rules fire only when touching UI files; security rules fire on auth/API endpoints.

### 2. Lifecycle Hooks
- **Pre-Edit Gate**: Checks file size, syntax, and git state before writing modifications.
- **Post-Edit Linter**: Automatically triggers formatters (`prettier`, `black`, `rustfmt`, `gofmt`) and linters (`eslint`, `ruff`, `clippy`) immediately after edits.
- **Pre-Commit Verifier**: Runs test suites and type checkers before generating commits.

### 3. Modular Skill Hub
- Integrates specialized skills across domain verticals (Design, Backend, DB Migrations, Security, Performance).
- Provides self-contained tools with zero external runtime requirements.

## Commands & Usage

- `/ecc install <profile>`: Install standard rule sets (`frontend`, `backend`, `fullstack`, `security`).
- `/ecc audit`: Audit the current agent workspace for configuration leaks, bloated prompts, or missing hooks.
- `/ecc hooks setup`: Configure git hooks and automated lint/test execution upon file changes.
- `/ecc optimize`: Run context budget advisor to compress active prompt memory.
