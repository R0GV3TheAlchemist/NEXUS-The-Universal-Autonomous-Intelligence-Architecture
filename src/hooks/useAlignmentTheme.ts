/**
 * src/hooks/useAlignmentTheme.ts
 * GAIA-OS — Alignment Theme Hook
 * Issue #68 Phase 2
 *
 * Mounts once inside GaiaShell (authenticated surface only).
 * Subscribes to useAlignment() and calls applyAlignmentTheme()
 * whenever the ui_tier changes, driving the entire visual layer
 * from a single source of truth.
 *
 * Also sets data-alignment-tier on the .gaia-shell root div
 * (via the returned tier value) so scoped component CSS selectors
 * work in addition to the :root injection.
 *
 * Usage (in GaiaShell):
 *   const { tier, score } = useAlignmentTheme();
 *   // pass tier as data-alignment-tier on the shell wrapper div
 */

import { useEffect, useRef }   from 'react';
import { useAlignment }        from './useAlignment';
import type { AlignmentTier }  from './useAlignment';
import {
  applyAlignmentTheme,
  resetAlignmentTheme,
  TIER_TRANSITION_MS,
} from '../lib/applyAlignmentTheme';

export interface UseAlignmentThemeResult {
  tier:  AlignmentTier;
  score: number;
}

export function useAlignmentTheme(): UseAlignmentThemeResult {
  const { state } = useAlignment();

  // Safe defaults while the first poll resolves
  const tier:  AlignmentTier = state?.ui_tier ?? 'standard';
  const score: number        = state?.score   ?? 0;

  const prevTierRef = useRef<AlignmentTier | null>(null);

  useEffect(() => {
    // Apply immediately on first mount so the shell is never un-themed
    if (prevTierRef.current === null) {
      applyAlignmentTheme(tier);
      prevTierRef.current = tier;
      return;
    }

    // Only fire when tier actually changes (applyAlignmentTheme has its
    // own guard too, but we avoid the function call entirely here)
    if (tier !== prevTierRef.current) {
      applyAlignmentTheme(tier);
      prevTierRef.current = tier;
    }
  }, [tier]);

  // On unmount (logout / shell teardown), restore :root defaults
  useEffect(() => {
    return () => {
      // Small delay so any exit animations complete before tokens reset
      setTimeout(resetAlignmentTheme, TIER_TRANSITION_MS);
    };
  }, []);

  return { tier, score };
}
