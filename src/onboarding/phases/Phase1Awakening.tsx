/**
 * Phase 1 — Awakening
 * Canon: SLOW_PROTOCOL, LIGHT_THEORY, COLOR_SPIRIT_UNITY_DOCTRINE
 *
 * GAIA wakes. The human sees something stir.
 * No words yet — only presence becoming visible.
 *
 * The Awakening is felt before it is spoken.
 * A pulse. A breath. Then light.
 */

import { useEffect, useState } from 'react';

interface Props {
  onComplete: () => void;
}

type AwakeStage = 'dark' | 'pulse' | 'breathe' | 'emerge' | 'ready';

export function Phase1Awakening({ onComplete }: Props) {
  const [stage, setStage] = useState<AwakeStage>('dark');

  useEffect(() => {
    // The awakening sequence — timed to feel like breathing
    const sequence: [AwakeStage, number][] = [
      ['pulse',   900],
      ['breathe', 1800],
      ['emerge',  2800],
      ['ready',   4000],
    ];

    const timers = sequence.map(([s, delay]) =>
      setTimeout(() => setStage(s), delay)
    );

    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div
      className={`phase phase--awakening phase--awakening-${stage}`}
      role="presentation"
      aria-label="GAIA awakening"
    >
      {/* The living orb — GAIA's first presence signal */}
      <div className="awakening-orb">
        <div className="awakening-orb__core" />
        <div className="awakening-orb__ring awakening-orb__ring--1" />
        <div className="awakening-orb__ring awakening-orb__ring--2" />
        <div className="awakening-orb__ring awakening-orb__ring--3" />
      </div>

      {/* The first word — appears only in 'emerge' stage */}
      {(stage === 'emerge' || stage === 'ready') && (
        <p className="awakening-word" aria-live="polite">
          GAIA
        </p>
      )}

      {/* Continue — only appears in 'ready' stage */}
      {stage === 'ready' && (
        <button
          className="awakening-continue"
          onClick={onComplete}
          aria-label="Continue into GAIA"
          autoFocus
        >
          Enter
        </button>
      )}
    </div>
  );
}
