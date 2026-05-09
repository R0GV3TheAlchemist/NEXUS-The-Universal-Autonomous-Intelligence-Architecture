/**
 * src/lib/applyAlignmentTheme.ts
 * GAIA-OS — Alignment Theme Injector
 * Issue #68 Phase 2
 *
 * Pure utility — no React dependency.
 * Reads the canonical tier values defined in Phase 1 (tokens.css §4)
 * and injects them as inline custom properties onto
 * document.documentElement, overriding the :root defaults.
 *
 * A CSS transition bridge (--alignment-transition-active) ensures
 * all token-consuming components animate smoothly through the change
 * rather than snapping. The bridge is skipped when
 * prefers-reduced-motion: reduce is active (accessibility).
 *
 * Usage:
 *   import { applyAlignmentTheme } from '../lib/applyAlignmentTheme';
 *   applyAlignmentTheme('full');
 */

import type { AlignmentTier } from '../hooks/useAlignment';

// ---------------------------------------------------------------------------
// Token map — mirrors tokens.css §6 exactly.
// This is the single source-of-truth for the JS side.
// If you update tokens.css, update this map and DESIGN_TOKENS.md together.
// ---------------------------------------------------------------------------

export interface TierTokens {
  animationSpeed:   string; // --animation-speed
  colorSaturation:  string; // --color-saturation
  infoDensity:      string; // --info-density
  glowIntensity:    string; // --glow-intensity
  breathingRate:    string; // --breathing-rate
  crystalPrimary:   string; // --crystal-primary
  crystalGlow:      string; // --crystal-glow
  crystalSurface:   string; // --crystal-surface
  crystalTextMuted: string; // --crystal-text-muted
}

export const TIER_TOKENS: Record<AlignmentTier, TierTokens> = {
  minimal: {
    animationSpeed:   '700ms',
    colorSaturation:  '30%',
    infoDensity:      '0.2',
    glowIntensity:    '0.15',
    breathingRate:    '8s',
    crystalPrimary:   '#4a4a6a',
    crystalGlow:      'rgba(74, 74, 106, 0.18)',
    crystalSurface:   'rgba(74, 74, 106, 0.06)',
    crystalTextMuted: 'rgba(255, 255, 255, 0.28)',
  },
  core: {
    animationSpeed:   '550ms',
    colorSaturation:  '55%',
    infoDensity:      '0.45',
    glowIntensity:    '0.28',
    breathingRate:    '6s',
    crystalPrimary:   '#f9a825',
    crystalGlow:      'rgba(249, 168, 37, 0.22)',
    crystalSurface:   'rgba(249, 168, 37, 0.06)',
    crystalTextMuted: 'rgba(255, 255, 255, 0.38)',
  },
  standard: {
    animationSpeed:   '400ms',
    colorSaturation:  '85%',
    infoDensity:      '0.75',
    glowIntensity:    '0.50',
    breathingRate:    '4s',
    crystalPrimary:   '#a78bfa',
    crystalGlow:      'rgba(167, 139, 250, 0.30)',
    crystalSurface:   'rgba(167, 139, 250, 0.06)',
    crystalTextMuted: 'rgba(255, 255, 255, 0.45)',
  },
  full: {
    animationSpeed:   '300ms',
    colorSaturation:  '100%',
    infoDensity:      '0.90',
    glowIntensity:    '0.72',
    breathingRate:    '3s',
    crystalPrimary:   '#52c7b8',
    crystalGlow:      'rgba(82, 199, 184, 0.32)',
    crystalSurface:   'rgba(82, 199, 184, 0.07)',
    crystalTextMuted: 'rgba(255, 255, 255, 0.55)',
  },
  vibrant: {
    animationSpeed:   '200ms',
    colorSaturation:  '120%',
    infoDensity:      '1.0',
    glowIntensity:    '1.0',
    breathingRate:    '2s',
    crystalPrimary:   '#f9d342',
    crystalGlow:      'rgba(249, 211, 66, 0.38)',
    crystalSurface:   'rgba(249, 211, 66, 0.08)',
    crystalTextMuted: 'rgba(255, 255, 255, 0.65)',
  },
};

// ---------------------------------------------------------------------------
// Transition duration (ms) — must match the CSS transition we set below.
// Phase 3 (Framer Motion) uses this same constant for animation variants.
// ---------------------------------------------------------------------------
export const TIER_TRANSITION_MS = 3_000;

// ---------------------------------------------------------------------------
// prefersReducedMotion()
// ---------------------------------------------------------------------------
function prefersReducedMotion(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

// ---------------------------------------------------------------------------
// applyAlignmentTheme()
//
// Injects the nine tier tokens onto document.documentElement.
// If reduced motion is NOT active, wraps the injection in a CSS
// transition bridge so every token-consuming property animates.
//
// The transition bridge works by temporarily adding a CSS transition
// for all custom properties on :root (via a class), injecting the
// new values, then removing the class after TIER_TRANSITION_MS so
// subsequent non-tier changes are not affected.
// ---------------------------------------------------------------------------

let _currentTier: AlignmentTier | null = null;
let _bridgeTimer: ReturnType<typeof setTimeout> | null = null;

export function applyAlignmentTheme(tier: AlignmentTier): void {
  if (typeof document === 'undefined') return; // SSR guard
  if (tier === _currentTier) return;           // no-op if tier unchanged

  const root    = document.documentElement;
  const tokens  = TIER_TOKENS[tier];
  const reduced = prefersReducedMotion();

  // —— 1. Activate transition bridge ——
  if (!reduced) {
    // Clear any in-flight bridge timer from a rapid tier change
    if (_bridgeTimer) clearTimeout(_bridgeTimer);
    root.setAttribute('data-alignment-transitioning', 'true');
  }

  // —— 2. Inject tokens ——
  root.style.setProperty('--animation-speed',    tokens.animationSpeed);
  root.style.setProperty('--color-saturation',   tokens.colorSaturation);
  root.style.setProperty('--info-density',       tokens.infoDensity);
  root.style.setProperty('--glow-intensity',     tokens.glowIntensity);
  root.style.setProperty('--breathing-rate',     tokens.breathingRate);
  root.style.setProperty('--crystal-primary',    tokens.crystalPrimary);
  root.style.setProperty('--crystal-glow',       tokens.crystalGlow);
  root.style.setProperty('--crystal-surface',    tokens.crystalSurface);
  root.style.setProperty('--crystal-text-muted', tokens.crystalTextMuted);

  // —— 3. Update tier attribute (used by CSS selectors + Playwright) ——
  root.setAttribute('data-alignment-tier', tier);

  // —— 4. Deactivate bridge after transition completes ——
  if (!reduced) {
    _bridgeTimer = setTimeout(() => {
      root.removeAttribute('data-alignment-transitioning');
      _bridgeTimer = null;
    }, TIER_TRANSITION_MS + 50); // +50 ms buffer
  }

  _currentTier = tier;
}

// ---------------------------------------------------------------------------
// resetAlignmentTheme()
// Removes all injected inline properties and restores :root defaults.
// Used by tests and on logout to return to the standard baseline.
// ---------------------------------------------------------------------------
export function resetAlignmentTheme(): void {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const props = [
    '--animation-speed', '--color-saturation', '--info-density',
    '--glow-intensity',  '--breathing-rate',   '--crystal-primary',
    '--crystal-glow',    '--crystal-surface',  '--crystal-text-muted',
  ];
  props.forEach(p => root.style.removeProperty(p));
  root.removeAttribute('data-alignment-tier');
  root.removeAttribute('data-alignment-transitioning');
  _currentTier = null;
}
