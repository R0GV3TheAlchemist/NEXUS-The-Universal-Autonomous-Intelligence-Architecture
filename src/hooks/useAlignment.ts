/**
 * src/hooks/useAlignment.ts
 *
 * React hook — polls the Rust `get_alignment_state` Tauri command
 * every POLL_INTERVAL_MS milliseconds and returns the live
 * AlignmentStateResponse for use by ViritasWidget and any other
 * consumer that needs the current biometric alignment tier.
 *
 * Usage:
 *   const { state, loading, error, refresh } = useAlignment();
 *
 * Privacy contract:
 *   rawRmssd is sourced from the wearable store if available;
 *   passes null when no wearable is connected so the Rust layer
 *   uses the neutral HRV baseline.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

// ---------------------------------------------------------------------------
// Types  (mirror AlignmentStateResponse in src-tauri/src/schumann.rs)
// ---------------------------------------------------------------------------

export type AlignmentTier =
  | 'minimal'
  | 'core'
  | 'standard'
  | 'full'
  | 'vibrant';

export interface AlignmentState {
  score:            number;   // 0–100
  hrv_score:        number;   // 0–100
  schumann_score:   number;   // 0–100
  solar_kp:         number;
  ui_tier:          AlignmentTier;
  last_updated:     string;   // ISO-8601 UTC
  fallback_mode:    string;   // empty when all feeds healthy
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS  = 30_000;   // 30 seconds
const ERROR_BACKOFF_MS  = 10_000;   // retry after 10 s on error

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

interface UseAlignmentResult {
  state:    AlignmentState | null;
  loading:  boolean;
  error:    string | null;
  refresh:  () => void;
}

export function useAlignment(rawRmssd: number | null = null): UseAlignmentResult {
  const [state,   setState]   = useState<AlignmentState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  const timerRef   = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const fetchAlignment = useCallback(async () => {
    if (!mountedRef.current) return;
    setLoading(true);

    try {
      const result = await invoke<AlignmentState>('get_alignment_state', {
        rawRmssd: rawRmssd ?? null,
      });

      if (!mountedRef.current) return;
      setState(result);
      setError(null);

      // Schedule next poll at normal cadence
      timerRef.current = setTimeout(fetchAlignment, POLL_INTERVAL_MS);
    } catch (err) {
      if (!mountedRef.current) return;
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);

      // Retry sooner after a failure
      timerRef.current = setTimeout(fetchAlignment, ERROR_BACKOFF_MS);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [rawRmssd]);

  // Manual refresh exposed to consumers
  const refresh = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    fetchAlignment();
  }, [fetchAlignment]);

  useEffect(() => {
    mountedRef.current = true;
    fetchAlignment();

    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [fetchAlignment]);

  return { state, loading, error, refresh };
}
