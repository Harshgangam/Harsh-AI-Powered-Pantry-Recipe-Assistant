---
name: context7-docs
description: Real-time library documentation and verified code example lookup via Context7 MCP. Provides version-accurate API signatures and patterns to eliminate training data hallucinations.
---

# Context7: Real-Time Documentation Engine

A documentation retrieval skill powered by Upstash Context7 MCP. It provides AI agents with instant, up-to-date, version-specific documentation, official code examples, and API schemas for modern libraries and frameworks.

## Why Context7 is Essential

- **Eliminates Stale Knowledge**: Avoids using deprecated APIs (e.g. Next.js App Router vs Pages Router, Pydantic v1 vs v2, React 19 Actions).
- **Official Patterns**: Ingests canonical examples directly from official documentation sources.
- **Reduces Hallucinations**: Verifies function arguments, return types, and configuration flags before generating code.

## Usage Protocol

```
[Need to use library/framework] (e.g. "Create Stripe Checkout session with Next.js 15")
          │
          ▼
[Context7 Query] ─── `context7_get_docs(library="stripe", version="latest", topic="checkout")`
          │
          ▼
[Receive Verified Docs & Signatures]
          │
          ▼
[Generate Accurate Code]
```

## Commands & Triggers

- `/context7 lookup <library> <topic>`: Fetch verified documentation and official snippets.
- `/context7 search <query>`: Search across indexed open-source library documentation.
- `/context7 api-reference <package> <version>`: Retrieve full API signature reference for a package version.
