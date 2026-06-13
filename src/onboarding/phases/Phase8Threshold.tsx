// C-OB01 — Phase 8: The Threshold v3.1
// Fix #364: buildLines() depthMap corrected to match DepthPreference type.
//
// DepthPreference = 'surface' | 'reflective' | 'deep'  (from types.ts)
//
// The v3 depthMap had 'familiar' and 'architect' which are not valid
// DepthPreference values and would always fall through to the default line.
// Corrected to 'surface', 'reflective', 'deep'.
//
// Also reads s.depth (alias) instead of s.depth_preference directly,
// and s.intentOther (alias) is available if needed by future gift logic.

import { useEffect, useRef, useState, useCallback } from 'react';
import { useOnboardingStore, type OnboardingStore } from '../store/onboardingStore';
import { GaiaSigil } from '../components/GaiaSigil';

// ── Personalised lines ────────────────────────────────────────────────────────
//
// intent values (UserIntent):  productivity | exploration | self_discovery |
//                               privacy | building | other
// depth values (DepthPreference): surface | reflective | deep

function buildLines(
  name:   string,
  intent: string,
  depth:  string,
): { text: string; muted: boolean }[] {
  // Line 1 — acknowledge what they came for
  const intentMap: Record<string, string> = {
    productivity:    'Your workflows are waiting.',
    exploration:     'The depths are open.',
    self_discovery:  'Your mirror is ready.',
    privacy:         'What is yours stays yours.',
    building:        'The tools are ready.',
    other:           'Your path is your own.',
  };
  const line1 = intentMap[intent] ?? 'The foundation is set.';

  // Line 2 — acknowledge depth tier
  // Matches DepthPreference: 'surface' | 'reflective' | 'deep'
  const depthMap: Record<string, string> = {
    surface:    'Clean slate each time. No threads held.',
    reflective: 'Context will grow with you.',
    deep:       'Every thread remembered.',
  };
  const line2 = depthMap[depth] ?? 'Your context is yours.';

  // Line 3 — the payoff line
  const line3 = name ? `GAIA is ready, ${name}.` : 'GAIA is ready.';

  return [
    { text: line1, muted: true  },
    { text: line2, muted: true  },
    { text: line3, muted: false },
  ];
}

// ── Timing constants ──────────────────────────────────────────────────────────

const LINE_DELAY_BASE = 700;
const LINE_STAGGER    = 750;
const CTA_AFTER_LAST  = 500;

// ── Component ─────────────────────────────────────────────────────────────────

interface Phase8ThresholdProps {
  onComplete: () => void;
}

export function Phase8Threshold({ onComplete }: Phase8ThresholdProps) {
  const completeOnboarding = useOnboardingStore((s: OnboardingStore) => s.completeOnboarding);
  const markInterrupted    = useOnboardingStore((s: OnboardingStore) => s.markInterrupted);
  const name               = useOnboardingStore((s: OnboardingStore) => s.name);

  // FIX #364: read camelCase aliases — these are guaranteed non-undefined
  // because the store initialises them from INITIAL_STATE and keeps them
  // in sync via setDepthPreference / setIntentOther.
  const depth  = useOnboardingStore((s: OnboardingStore) => s.depth);
  const intent = useOnboardingStore((s: OnboardingStore) => s.intent);

  // Use the first intent if multiple were selected; fall back to empty string
  const primaryIntent = Array.isArray(intent) ? (intent[0] ?? '') : '';

  const lines = buildLines(name ?? '', primaryIntent, depth ?? 'reflective');

  const [visibleCount, setVisibleCount] = useState(0);
  const [showCta,      setShowCta]      = useState(false);

  const timersFired = useRef(false);

  useEffect(() => {
    if (timersFired.current) return;
    timersFired.current = true;

    lines.forEach((_, i) => {
      setTimeout(() => {
        setVisibleCount((n) => n + 1);
      }, LINE_DELAY_BASE + i * LINE_STAGGER);
    });

    const ctaDelay = LINE_DELAY_BASE + lines.length * LINE_STAGGER + CTA_AFTER_LAST;
    setTimeout(() => setShowCta(true), ctaDelay);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleEnter = useCallback(() => {
    completeOnboarding();
    onComplete();
  }, [completeOnboarding, onComplete]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { markInterrupted(); return; }
      if ((e.key === 'Enter' || e.key === ' ') && showCta) {
        const tag = (document.activeElement as HTMLElement)?.tagName;
        if (tag !== 'BUTTON') handleEnter();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showCta, handleEnter, markInterrupted]);

  return (
    <section
      className="phase phase--threshold phase--enter"
      aria-label="Entering GAIA"
    >
      <div className="phase__content phase__content--centered">

        <GaiaSigil animate size={140} />

        <h1 className="threshold-greeting">
          {name ? `Welcome, ${name}.` : 'Welcome.'}
        </h1>

        <div className="threshold-lines" aria-live="polite">
          {lines.map((line, i) => (
            <p
              key={line.text}
              className={[
                'threshold-line',
                line.muted ? 'threshold-line--muted' : '',
                i < visibleCount ? 'threshold-line--visible' : '',
              ].filter(Boolean).join(' ')}
            >
              {line.text}
            </p>
          ))}
        </div>

        {showCta && (
          <div className="threshold-cta">
            <button
              className="btn btn--primary btn--large"
              onClick={handleEnter}
              autoFocus
              aria-label="Enter GAIA"
            >
              Enter
            </button>
          </div>
        )}

      </div>
    </section>
  );
}
