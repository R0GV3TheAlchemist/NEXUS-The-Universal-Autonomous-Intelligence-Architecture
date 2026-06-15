/**
 * Phase 0 — Bootstrap
 * Silent. Invisible. GAIA wakes.
 *
 * No UI. Just the system initialising.
 * Completes automatically after a breath.
 */

import { useEffect } from 'react';
import { useOnboardingStore } from '../store/onboardingStore';

interface Props {
  onComplete: () => void;
}

export function Phase0Bootstrap({ onComplete }: Props) {
  const setData = useOnboardingStore((s) => s.setData);

  useEffect(() => {
    // Initialise the human's IDs on first boot
    const now = new Date().toISOString();
    const humanId = `human_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    setData({ humanId, sessionId });

    // The sacred pause — GAIA wakes in silence
    const timer = setTimeout(() => onComplete(), 1200);
    return () => clearTimeout(timer);
  }, [onComplete, setData]);

  // Intentionally blank — this phase has no face
  return (
    <div
      className="phase phase--bootstrap"
      aria-hidden="true"
      style={{ background: 'transparent' }}
    />
  );
}
