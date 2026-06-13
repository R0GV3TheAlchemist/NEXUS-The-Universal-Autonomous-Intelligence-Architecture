// C-OB01 — Phase 8: The Threshold v3
// The ceremonial exit from onboarding into GAIA proper.
// Not a confirmation screen. A rite of passage.
//
// Changes from v2:
//   - completeOnboarding() deferred to the Enter click, not mount.
//     Marking complete before the user confirms meant a closed window
//     would skip onboarding permanently next boot.
//   - Lines are personalised: name + intent + depth tier pulled from store.
//   - phase--enter animation added (matches every other phase).
//   - Keyboard: Enter/Space triggers onComplete once button is visible.
//   - Escape calls markInterrupted (consistent with other phases).
//   - GaiaSigil brightness prop removed; not part of the component's API.
//   - threshold-cta class added so CSS can target the CTA block independently.

import { useEffect, useRef, useState, useCallback } from 'react';
import { useOnboardingStore, type OnboardingStore } from '../store/onboardingStore';
import { GaiaSigil } from '../components/GaiaSigil';

// ── Personalised lines ───────────────────────────────────────────────────────
//
// Build 3 lines that reflect what the user told us during onboarding.
// Each line has a 'muted' flag — the first two are quieter, the last pops.

function buildLines(
  name:    string,
  intent:  string,
  depth:   string,
): { text: string; muted: boolean }[] {
  // Line 1 — acknowledge what they came for
  const intentMap: Record<string, string> = {
    productivity:  'Your workflows are waiting.',
    research:      'The depths are open.',
    creativity:    'The canvas is ready.',
    learning:      'Your questions have a home.',
    personal:      'Your space is yours.',
    other:         'Your path is your own.',
  };
  const line1 = intentMap[intent] ?? 'The foundation is set.';

  // Line 2 — acknowledge depth / relationship tier
  const depthMap: Record<string, string> = {
    surface:   'No history kept. Clean slate each time.',
    familiar:  'Context will grow with you.',
    deep:      'Every thread remembered.',
    architect: 'Full memory. Full trust.',
  };
  const line2 = depthMap[depth] ?? 'Your context is yours.';

  // Line 3 — the payoff line, always unambiguous
  const line3 = name ? `GAIA is ready, ${name}.` : 'GAIA is ready.';

  return [
    { text: line1, muted: true  },
    { text: line2, muted: true  },
    { text: line3, muted: false },
  ];
}

// ── Timing constants ─────────────────────────────────────────────────────────

const LINE_DELAY_BASE = 700;   // ms before first line appears
const LINE_STAGGER    = 750;   // ms between each subsequent line
const CTA_AFTER_LAST  = 500;   // ms after final line before Enter appears

// ── Component ────────────────────────────────────────────────────────────────

interface Phase8ThresholdProps {
  onComplete: () => void;
}

export function Phase8Threshold({ onComplete }: Phase8ThresholdProps) {
  const completeOnboarding = useOnboardingStore((s: OnboardingStore) => s.completeOnboarding);
  const markInterrupted    = useOnboardingStore((s: OnboardingStore) => s.markInterrupted);
  const name               = useOnboardingStore((s: OnboardingStore) => s.name);
  const intent             = useOnboardingStore((s: OnboardingStore) => s.intent);
  const depth              = useOnboardingStore((s: OnboardingStore) => s.depth);

  const lines = buildLines(name ?? '', intent ?? '', depth ?? '');

  const [visibleCount, setVisibleCount] = useState(0);
  const [showCta,      setShowCta]      = useState(false);

  // Lock so timers only run once even under StrictMode double-invoke
  const timersFired = useRef(false);

  useEffect(() => {
    if (timersFired.current) return;
    timersFired.current = true;

    // Stagger lines in
    lines.forEach((_, i) => {
      setTimeout(() => {
        setVisibleCount((n) => n + 1);
      }, LINE_DELAY_BASE + i * LINE_STAGGER);
    });

    // Show CTA after all lines have appeared
    const ctaDelay = LINE_DELAY_BASE + lines.length * LINE_STAGGER + CTA_AFTER_LAST;
    setTimeout(() => setShowCta(true), ctaDelay);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Enter: mark complete THEN call onComplete ─────────────────────────────
  const handleEnter = useCallback(() => {
    completeOnboarding();
    onComplete();
  }, [completeOnboarding, onComplete]);

  // ── Keyboard ──────────────────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { markInterrupted(); return; }
      if ((e.key === 'Enter' || e.key === ' ') && showCta) {
        // Only fire if nothing else is focused (the button handles its own Enter)
        const tag = (document.activeElement as HTMLElement)?.tagName;
        if (tag !== 'BUTTON') handleEnter();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showCta, handleEnter, markInterrupted]);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <section
      className="phase phase--threshold phase--enter"
      aria-label="Entering GAIA"
    >
      <div className="phase__content phase__content--centered">

        {/* Sigil — no brightness prop; size matched to Phase 2 intro */}
        <GaiaSigil animate size={140} />

        {/* Personalised greeting */}
        <h1 className="threshold-greeting">
          {name ? `Welcome, ${name}.` : 'Welcome.'}
        </h1>

        {/* Staggered lines */}
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

        {/* Enter CTA — deferred until all lines have landed */}
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
