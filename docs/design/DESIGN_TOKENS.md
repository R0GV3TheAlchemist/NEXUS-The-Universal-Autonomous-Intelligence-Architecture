# GAIA-OS Design Token Reference

> **Issue:** #68 Phase 1 — Alignment Design Token System  
> **Canon:** C19 (Color Doctrine), Pillar II (Viriditas)  
> **Status:** Phase 1 complete — tokens defined, documented, Phase 2 will wire runtime injection

---

## Overview

GAIA-OS uses a **biometric-driven design token system**. Rather than static themes, the interface adapts in real time to the user's current alignment state — a composite of HRV coherence and Schumann resonance proximity. The visual result is an interface that literally breathes differently depending on how you are.

All tokens are defined in `src/shell/tokens.css`. At runtime, `applyAlignmentTheme()` (Phase 2) reads the current `AlignmentTier` from `useAlignment` and injects the matching token values onto `document.documentElement` as inline custom properties, overriding the `:root` defaults.

---

## The Five Alignment Tiers

| Tier | Score Range | Physiological state | Accent colour |
|---|---|---|---|
| `minimal` | 0–19 | Deep rest / restorative | Slate `#4a4a6a` |
| `core` | 20–39 | Recovering / building | HRV Amber `#f9a825` |
| `standard` | 40–59 | Neutral baseline | Sovereign Violet `#a78bfa` |
| `full` | 60–79 | Coherent / in-flow | Schumann Teal `#52c7b8` |
| `vibrant` | 80–100 | Peak alignment / singing | Gold `#f9d342` |

---

## Token Reference Table

### `--animation-speed` (ms)

Base duration multiplier for **all** CSS transitions and keyframe animations. Components express durations as `calc(var(--animation-speed) * <factor>)` so they scale automatically with tier changes.

| Tier | Value | Effect |
|---|---|---|
| `minimal` | `700ms` | Slow, sleep-like — nothing jerks or demands attention |
| `core` | `550ms` | Calm — deliberate, unhurried |
| `standard` | `400ms` | Neutral — comfortable reading/working pace |
| `full` | `300ms` | Crisp — the interface feels responsive and alive |
| `vibrant` | `200ms` | Fast — peak reactivity, everything is instantaneous |

---

### `--color-saturation` (%)

Applied globally via `filter: saturate(var(--color-saturation))` on the shell body (Phase 2 responsibility), and used in component-level `color-mix()` calls. Controls the overall chromatic vibrancy of the interface.

| Tier | Value | Effect |
|---|---|---|
| `minimal` | `30%` | Near-monochrome — the colour drains away, reducing stimulation |
| `core` | `55%` | Muted — present but not assertive |
| `standard` | `85%` | Normal — full design intent |
| `full` | `100%` | Saturated — colours are at their designed richness |
| `vibrant` | `120%` | Supersaturated — the palette glows beyond its rest state |

---

### `--info-density` (0–1)

A logical signal read by TypeScript (not used in CSS directly). Phase 2 will read this via `getComputedStyle()` and show/hide secondary UI elements (metadata, sub-scores, contextual hints) based on the current density level.

| Tier | Value | Secondary elements shown |
|---|---|---|
| `minimal` | `0.2` | Almost nothing — breath pacer and single action only |
| `core` | `0.45` | Primary content only — no metadata |
| `standard` | `0.75` | Normal — most elements visible |
| `full` | `0.90` | All primary + most secondary |
| `vibrant` | `1.0` | Everything — the full information environment |

---

### `--glow-intensity` (0–1)

Scales box-shadow glow spread on all orbs, crystals, and accent surfaces. Component CSS should use:

```css
box-shadow: 0 0 calc(var(--glow-intensity) * 32px)
                calc(var(--glow-intensity) * 12px)
                var(--crystal-glow);
```

| Tier | Value | Effect |
|---|---|---|
| `minimal` | `0.15` | Barely present — a faint phosphorescence |
| `core` | `0.28` | Soft halo — visible but not demanding |
| `standard` | `0.50` | Normal glow — balanced presence |
| `full` | `0.72` | Bright — the interface feels energised |
| `vibrant` | `1.0` | Maximum — everything is radiant |

---

### `--breathing-rate` (s)

Controls the period of the ambient breathing/pulse animation on the GAIA orb, shell overlays, and any breathing-rate-aware component. Values are chosen to match physiological breath guidance at each tier:

| Tier | Value | Breath pattern |
|---|---|---|
| `minimal` | `8s` | Box breath: 4s in / 4s out — deepest rest |
| `core` | `6s` | Coherent breathing: 3s in / 3s out |
| `standard` | `4s` | Neutral: 2s in / 2s out |
| `full` | `3s` | Energised coherence |
| `vibrant` | `2s` | Peak activation |

---

### Colour tokens

Four companion colour tokens are set per tier. They replace the previous hardcoded `--crystal-*` values scattered across components:

| Token | Purpose |
|---|---|
| `--crystal-primary` | Dominant accent: orb colour, ring stroke, active labels |
| `--crystal-glow` | RGBA version for `box-shadow` / `text-shadow` glow effects |
| `--crystal-surface` | Subtle tinted background for tier-aware cards and panels |
| `--crystal-text-muted` | Muted text that still respects the tier's chromatic identity |

| Tier | `--crystal-primary` | Named colour |
|---|---|---|
| `minimal` | `#4a4a6a` | Restorative Slate |
| `core` | `#f9a825` | HRV Amber |
| `standard` | `#a78bfa` | Sovereign Violet |
| `full` | `#52c7b8` | Schumann Teal |
| `vibrant` | `#f9d342` | Doctrine Gold |

---

## How to consume tokens in component CSS

### Animation durations
```css
/* Scale with tier — never hardcode ms values */
.my-component {
  transition: opacity calc(var(--animation-speed) * 0.6) ease,
              transform calc(var(--animation-speed) * 0.8) cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Glow effects
```css
.my-orb {
  box-shadow: 0 0 calc(var(--glow-intensity) * 32px)
                  calc(var(--glow-intensity) * 12px)
                  var(--crystal-glow);
}
```

### Accent colour
```css
.my-accent {
  color: var(--crystal-primary);
  background: var(--crystal-surface);
  border-color: color-mix(in srgb, var(--crystal-primary) 40%, transparent);
}
```

### Info density (TypeScript only)
```ts
// Read in Phase 2 applyAlignmentTheme() to show/hide secondary elements
const density = parseFloat(
  getComputedStyle(document.documentElement)
    .getPropertyValue('--info-density').trim()
);
const showSecondary = density >= 0.75;
```

---

## Naming conventions

- All alignment tokens are prefixed `--animation-`, `--color-`, `--info-`, `--glow-`, `--breathing-` or `--crystal-`
- Never add a tier-specific prefix (e.g. `--vibrant-animation-speed`) — tier is controlled by the selector, not the name
- All new tokens must be added to **this document** and to `src/shell/tokens.css` simultaneously
- All tokens must have a default value on `:root` (the `standard` tier values serve as the safe default)

---

## Extension rules

When adding a new design token:

1. Define default on `:root` in `tokens.css`
2. Add a value for **all five tiers** in the `[data-alignment-tier]` blocks
3. Document it in this file with a description and the tier table
4. Consume only via `var(--token-name)` — never hardcode values that should be tier-aware

---

## Cross-references

- **C19** — Color Doctrine and Signal System (`src/shell/tokens.css` §1–3)
- **Issue #64** — Schumann Biometric Layer (source of `AlignmentTier`)
- **Issue #68 Phase 2** — `applyAlignmentTheme()` runtime injection
- **Issue #68 Phase 3** — Framer Motion breathing animation system
- `src/hooks/useAlignment.ts` — hook that reads `AlignmentTier` from Tauri IPC
- `src/shared/ViritasWidget.tsx` — first consumer of `--crystal-*` tokens
