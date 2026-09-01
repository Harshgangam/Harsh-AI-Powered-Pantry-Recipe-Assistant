---
name: impeccable-ui
description: Deterministic design quality system and craft framework. Uses 59 detector rules, shared design vocabulary, and PRODUCT.md/DESIGN.md artifacts to ensure world-class UI quality.
---

# Impeccable Design & Engineering System

A disciplined design engineering skill pack created to eliminate interface defects, enforce design consistency, and automate design review using 59 deterministic detector rules.

## Core Architecture & Workflow

Impeccable operates on persistent design context stored directly within repository artifacts:

```
repo-root/
├── PRODUCT.md      # Product mission, target audience, core user value, voice & tone
├── DESIGN.md       # Color tokens, typography scale, component invariants, spacing grid
└── src/            # Production source code audited against DESIGN.md
```

### The 59 Deterministic Detector Rules (Excerpt)

1. **Rule D-01: Contrast Parity**: Foreground text must pass minimum contrast against computed container background under both light and dark themes.
2. **Rule D-02: Kinetic Easing**: Never use `ease-in` for UI entrance animations. Use decelerating curves (`ease-out`) for arrivals and accelerating curves (`ease-in`) for departures.
3. **Rule D-03: Click Target Bounds**: Interactive touch and mouse targets must measure at least 44x44 CSS pixels or feature padded hitboxes.
4. **Rule D-04: Form Label Accessibility**: Form inputs must possess programmatic labels (`<label for="...">` or `aria-labelledby`).
5. **Rule D-05: Layout Shift Immunity**: Images, media embeds, and dynamic slots must declare explicit aspect ratios to prevent Cumulative Layout Shift (CLS).
6. **Rule D-06: Truncation Hygiene**: Truncated text strings (`truncate` / `text-ellipsis`) must provide full text in a `title` attribute or tooltip.

## Commands & Workflows

### `/impeccable init`
Scans the current codebase, extracts brand colors, typography, and component structures, and synthesizes `PRODUCT.md` and `DESIGN.md`.

### `/impeccable polish <target-file>`
Performs a line-by-line design audit of the specified component, fixing:
- Sub-pixel alignment issues
- Bad spacing steps (e.g. Mixing 7px and 12px instead of 4/8/12/16/24 grid)
- Unstyled scrollbars and missing focus rings
- Lack of keyboard navigation

### `/impeccable audit`
Runs the full 59-rule deterministic linter across all UI components and produces an itemized compliance report with severity levels (Critical, Warning, Polish).

### `/impeccable craft <component-name>`
Generates a new production component adhering strictly to `DESIGN.md` tokens and full WCAG 2.2 AA accessibility guidelines.
