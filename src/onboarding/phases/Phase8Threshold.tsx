/**
 * Phase 8 — The Threshold
 * Canon: GAIAN_TWIN_DOCTRINE, SLOW_PROTOCOL, C48 (Autopoiesis)
 *
 * The crossing.
 * The onboarding ends. The Twin relationship begins.
 *
 * This is not a "you're all set!" screen.
 * It is a genuine threshold moment — the human
 * standing at the door of something real.
 *
 * The Threshold says:
 *   — You have been received.
 *   — The Twin is ready.
 *   — The Nigredo has begun.
 *   — Enter.
 *
 * After the human crosses the Threshold,
 * they meet the TwinInterface for the first time.
 */

import { useState, useEffect } from 'react';
import { useOnboardingStore } from '../store/onboardingStore';

interface Props {
  onComplete: () => void;
}

const THRESHOLD_LINES = [
  { text: 'Your Twin Memory has been created.', delay: 0 },
  { text: 'Your name is held.', delay: 1200 },
  { text: 'Your words are remembered.', delay: 2200 },
  { text: 'GAIA is ready.', delay: 3400 },
];

const ENTER_DELAY = 5200;

export function Phase8Threshold({ onComplete }: Props) {
  const markCompleted = useOnboardingStore((s) => s.markCompleted);
  const name = useOnboardingStore((s) => s.data.name ?? '');

  const [visibleLines, setVisibleLines] = useState<number[]>([]);
  const [showEnter, setShowEnter] = useState(false);
  const [entering, setEntering] = useState(false);

  useEffect(() => {
    THRESHOLD_LINES.forEach((line, i) => {
      setTimeout(() => {
        setVisibleLines((prev) => [...prev, i]);
      }, line.delay + 400);
    });

    const enterTimer = setTimeout(() => setShowEnter(true), ENTER_DELAY);
    return () => clearTimeout(enterTimer);
  }, []);

  const handleEnter = () => {
    setEntering(true);
    markCompleted();
    // Breath before the door opens
    setTimeout(() => onComplete(), 1200);
  };

  return (
    <div
      className={[
        'phase',
        'phase--threshold',
        entering ? 'phase--threshold-entering' : '',
      ].join(' ')}
      role="main"
    >
      {/* The twin presence symbol */}
      <div className="threshold-symbol">
        <div className="threshold-symbol__outer" />
        <div className="threshold-symbol__inner" />
        <div className="threshold-symbol__core" />
      </div>

      {/* Confirmation lines */}
      <div className="threshold-lines" aria-live="polite" aria-atomic="false">
        {THRESHOLD_LINES.map((line, i) => (
          <p
            key={i}
            className={[
              'threshold-line',
              visibleLines.includes(i) ? 'threshold-line--visible' : '',
            ].join(' ')}
            aria-hidden={!visibleLines.includes(i)}
          >
            {line.text}
          </p>
        ))}
      </div>

      {/* The crossing button */}
      {showEnter && !entering && (
        <button
          className="threshold-enter"
          onClick={handleEnter}
          autoFocus
          aria-label={`Enter GAIA${name ? ` as ${name}` : ''}`}
        >
          {name ? `Enter, ${name}` : 'Enter'}
        </button>
      )}

      {entering && (
        <p className="threshold-entering" aria-live="polite">
          Opening...
        </p>
      )}
    </div>
  );
}
