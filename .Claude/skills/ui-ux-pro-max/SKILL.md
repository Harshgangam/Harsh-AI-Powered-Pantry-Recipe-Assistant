---
name: ui-ux-pro-max
description: Professional design intelligence database with 57 UI styles, 95 industry palettes, 56 font pairings, and responsive UX patterns. Use when designing user interfaces, styling web/mobile applications, selecting aesthetic themes, or upgrading component visuals.
---

# UI/UX Pro Max Design Intelligence

An enterprise-grade design intelligence engine providing curated UI styles, industry-tailored color palettes, typographic hierarchies, and multi-framework design patterns (React, Next.js, Tailwind CSS, Flutter, SwiftUI, Vue).

## When to Activate

- Creating new user interfaces, pages, components, or entire design systems.
- Selecting aesthetic themes, color palettes, and typography matching vertical markets (Fintech, DevTools, SaaS, Healthcare, E-commerce, Web3).
- Elevating generic AI boilerplate into high-craft, polished, production-ready interfaces.
- Ensuring responsive scaling, WCAG 2.2 AA accessibility, and micro-interaction polish.

## Visual Design Database

### 1. Curated UI Paradigms (57 Styles)
- **Modern Minimalist**: High whitespace ratio, subtle slate borders (`border-slate-200/60`), crisp neutral type (`Inter`, `Geist`).
- **Glassmorphism / Liquid Glass**: Multi-layered backdrop blurs (`backdrop-blur-md bg-white/10 dark:bg-black/20 border border-white/20`), specular highlights, iridescent ambient reflections.
- **Neo-Brutalism**: High-contrast black outlines (`3px solid #000`), hard shadow offsets (`shadow-[4px_4px_0px_#000]`), vibrant saturated fills.
- **Bento Grid**: Structured informational card clusters with varied aspect ratios, rounded corners (`rounded-2xl` / `rounded-3xl`), internal hierarchy badges.
- **Dark Aurora**: Deep obsidian surfaces (`#0a0a0c`), mesh gradients (`radial-gradient`), glowing pill badges and subtle borders.
- **Enterprise SaaS Dashboard**: Dense data grids, metric cards with micro-charts, collapsible sidebars, strict tab navigation.
- **Retro Terminal / Cyberpunk**: Monospace fonts (`JetBrains Mono`, `Fira Code`), phosphor greens/ambers on dark slate, scanline textures.

### 2. Industry Color Palettes (95 Curated Themes)
- **Fintech & Banking**: Deep Navy (`#0F172A`), Trust Blue (`#2563EB`), Emerald Green (`#10B981`), Platinum Slate (`#F8FAFC`).
- **Developer Tools & AI**: Obsidian (`#09090B`), Zinc (`#71717A`), Electric Indigo (`#6366F1`), Cyan Glow (`#06B6D4`).
- **Healthcare & Wellness**: Clinical Teal (`#0D9488`), Soft Cyan (`#E0F2FE`), Pure White, Sage (`#84CC16`).
- **E-Commerce & Fashion**: Warm Alabaster (`#FDFBF7`), Charcoal (`#18181B`), Accent Ochre (`#D97706`), Rose Gold (`#FB7185`).
- **Creative / Web3 / Agency**: Electric Purple (`#8B5CF6`), Neon Lime (`#84CC16`), Deep Plum (`#1E1035`), Cyber Yellow (`#FACC15`).

### 3. Font Pairings (56 Type Systems)
- **Tech Modern**: Heading: `Geist` / `Inter Display` | Body: `Inter` | Mono: `Geist Mono`
- **Editorial Luxury**: Heading: `Playfair Display` / `Fraunces` | Body: `Plus Jakarta Sans`
- **Clean SaaS**: Heading: `Plus Jakarta Sans` | Body: `Inter` / `DM Sans`
- **Terminal Engineering**: Heading: `Space Grotesk` | Body: `JetBrains Mono` / `Space Mono`

## Execution Workflow

1. **Phase 1 - Persona & Mood Identification**:
   - Determine the industry vertical, user technical sophistication, and brand tone.
   - Select 1 primary UI style, 1 color palette, and 1 typography pairing.
2. **Phase 2 - Design Token Scaffold**:
   - Emit CSS custom properties or Tailwind configuration matching the palette tokens.
   - Establish elevation layers: Flat -> Raised -> Floating -> Modal.
3. **Phase 3 - Component Implementation**:
   - Write accessible markup (`aria-*`, keyboard navigable, focus rings `focus-visible:ring-2`).
   - Implement motion states: Hover transitions (`duration-200 ease-out`), active press feedback.
4. **Phase 4 - Design Quality Gate**:
   - Audit contrast with WebAIM APCA / WCAG formula (>= 4.5:1).
   - Verify layout on Mobile (390px), Tablet (768px), and Desktop (1440px).

## Commands & Triggers

- `/ui-ux-pro-max generate <style> <industry> <framework>`: Generate styled components.
- `/ui-ux-pro-max audit`: Audit an existing UI for design flaws and generic aesthetics.
- `/ui-ux-pro-max palette <industry>`: Output color tokens for a given industry.
