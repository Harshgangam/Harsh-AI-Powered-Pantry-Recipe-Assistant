---
name: codeburn-telemetry
description: Local AI token usage and session cost tracker. Monitors token burn rates across models and projects, enforces budget limits, and suggests prompt optimizations.
---

# Codeburn: AI Token & Cost Telemetry

A privacy-first, local telemetry tool designed to track AI coding agent expenditures, token burn rates, and session efficiency across Claude Code, Cursor, Gemini CLI, and custom agents.

## Core Capabilities

### 1. Granular Spend Tracking
- Tracks input tokens, output tokens, cache read tokens, and cache creation tokens per model (Claude 3.5 Sonnet, Claude Opus, Gemini 1.5 Pro, GPT-4o).
- Calculates exact dollar costs based on live provider pricing tiers.

### 2. Session & Project Telemetry
- Breaks down spend by project, task branch, subagent invocation, and timestamp.
- Identifies expensive runaway loops and un-cached prompt bloat.

### 3. Budget Enforcements & Alerts
- Set hard spending caps (e.g. `$5.00 / session` or `$50.00 / day`).
- Triggers high-priority warnings when burn rate exceeds thresholds.

## Telemetry Report Format

```
┌─────────────────────────────────────────────────────────────┐
│ CODEBURN SESSION TELEMETRY                                  │
├──────────────────────┬─────────────┬───────────┬────────────┤
│ Model                │ In / Out (k)│ Cache (%) │ Cost ($)   │
├──────────────────────┼─────────────┼───────────┼────────────┤
│ Claude 3.5 Sonnet    │ 142k / 18k  │ 74.2%     │ $0.48      │
│ Gemini 1.5 Pro       │ 410k / 32k  │ 88.5%     │ $0.22      │
├──────────────────────┼─────────────┼───────────┼────────────┤
│ Total Session Spend  │             │           │ $0.70      │
└──────────────────────┴─────────────┴───────────┴────────────┘
```

## Commands & Triggers

- `/codeburn status`: Display active session token usage and real-time cost.
- `/codeburn report --days=<n>`: Generate project spending breakdown over time.
- `/codeburn set-budget <amount>`: Configure session budget ceiling.
- `/codeburn suggest-optimizations`: Analyze conversation transcripts and recommend token-saving measures.
