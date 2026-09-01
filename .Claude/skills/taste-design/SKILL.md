---
name: taste-design
description: Anti-slop frontend craft and aesthetic guidelines for AI agents. Prevents generic AI UI boilerplate through deliberate typography, spatial cadence, micro-interactions, and tunable design variance.
---

# Taste: Anti-Slop Frontend Craft

A specialized aesthetic framework designed to eradicate generic AI frontend patterns ("AI slop") by enforcing opinionated visual craft, refined spatial rhythms, typography hierarchy, and deliberate micro-interactions.

## The Anti-Slop Principles

1. **Never Default to Generic Purple/Indigo Gradients**: AI agents default to `#6366F1` / `#8B5CF6` on white cards. Use deliberate brand accents, monochromatic neutrals, or unexpected high-craft color harmonies.
2. **Death to Uniform Padding**: Do not use `p-6` everywhere. Create visual hierarchy using intentional asymmetric spacing: tight metadata clusters (`gap-1.5`), expansive hero sections (`py-24 px-8`), and structured card insets (`p-8 md:p-10`).
3. **Border Sophistication**: Stop using harsh `border-gray-200`. Use translucent borders (`border-foreground/10`), inner bevel highlights (`shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]`), and layered surface depths.
4. **Typography Leading & Tracking**:
   - Large headings (>= 32px): Tighten tracking (`tracking-tight` / `-0.02em`) and decrease line-height (`leading-tight`).
   - Small uppercase labels (11-13px): Loosen tracking (`tracking-widest` / `+0.05em`) with `font-semibold` and `uppercase`.
   - Body copy: Generous line-height (`leading-relaxed`) with max line length <= 65ch.

## Tunable Parameters

When generating or refactoring UI, configure parameters on a 1-10 scale:

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `DESIGN_VARIANCE` | `7` | 1 = Ultra-conservative enterprise; 10 = Avant-garde experimental |
| `MOTION_INTENSITY`| `5` | 1 = Instant/static; 5 = Subtle spring physics; 10 = Cinematic choreographies |
| `SURFACE_DENSITY`  | `6` | 1 = High-density Bloomberg terminal; 10 = Expansive Apple/Linear minimalism |
| `COLOR_SATURATION`| `4` | 1 = Strict monochrome; 10 = Hyper-vibrant synthwave |

## Interaction & Motion Standards

- Use physics-based springs over linear easing (`cubic-bezier(0.16, 1, 0.3, 1)` or `framer-motion` springs: `{ stiffness: 400, damping: 30 }`).
- Interactive elements must reflect hover, active, focus-visible, and disabled states.
- Micro-interaction checklist:
  - Buttons depress slightly on click (`active:scale-[0.98]`).
  - Cards elevate and illuminate borders on hover (`hover:border-foreground/20 hover:shadow-lg`).
  - Dropdowns & tooltips enter with subtle scale and translation (`opacity-0 scale-95 -> opacity-100 scale-100`).

## Commands & Triggers

- `/taste apply`: Transform existing frontend component or page to high-craft taste standards.
- `/taste audit`: Inspect codebase for AI slop patterns, generic styles, and unrefined layouts.
- `/taste tune <parameter> <value>`: Set variance, motion, density, or saturation levels.
