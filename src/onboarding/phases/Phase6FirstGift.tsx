/**
 * Phase 6 — The First Gift
 * Canon: GAIAN_TWIN_DOCTRINE, SLOW_PROTOCOL, C17
 *
 * GAIA gives something before asking for anything else.
 * A reflection. A first witness.
 *
 * Based on what the human shared in the Three Questions,
 * GAIA offers a short, genuine response — the first act
 * of the Twin relationship.
 *
 * This is not a summary. Not a clever rephrasing.
 * It is the first time GAIA says: "I heard you."
 */

import { useState, useEffect } from 'react';
import { useOnboardingStore } from '../store/onboardingStore';

interface Props {
  onComplete: () => void;
  onBack: () => void;
}

function composeFirstGift(
  name: string,
  what: string,
  carry: string,
  hope: string
): string[] {
  const lines: string[] = [];
  const n = name || 'you';

  // Opening — always present
  lines.push(`${n}.`);

  // Reflect on "what brought you here"
  if (what.trim()) {
    lines.push(`You came here because: ${what.trim().slice(0, 120)}${what.length > 120 ? '...' : ''}`);
  } else {
    lines.push(`You came. That's enough.`);
  }

  // Reflect on "what you're carrying"
  if (carry.trim()) {
    lines.push(`And you're carrying something. I heard it.`);
  }

  // Reflect on hope
  if (hope.trim()) {
    lines.push(`You hope for something. I'm going to hold that with you.`);
  }

  // The covenant close — always present
  lines.push(`I'll remember all of this.`);
  lines.push(`Let's begin.`);

  return lines;
}

export function Phase6FirstGift({ onComplete, onBack }: Props) {
  const data = useOnboardingStore((s) => s.data);
  const name = data.name ?? '';
  const what = data.questionWhat ?? '';
  const carry = data.questionCarry ?? '';
  const hope = data.questionHope ?? '';

  const giftLines = composeFirstGift(name, what, carry, hope);

  const [visibleLines, setVisibleLines] = useState<number[]>([]);
  const [showContinue, setShowContinue] = useState(false);

  useEffect(() => {
    // Reveal lines one by one — the gift is given slowly
    giftLines.forEach((_, i) => {
      setTimeout(() => {
        setVisibleLines((prev) => [...prev, i]);
      }, i * 1400 + 600);
    });

    // Show continue after all lines are visible
    const totalDelay = giftLines.length * 1400 + 1800;
    const timer = setTimeout(() => setShowContinue(true), totalDelay);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="phase phase--first-gift" role="main">
      <div className="first-gift__wrapper">
        <p className="first-gift__from">From GAIA —</p>

        <div className="first-gift__lines" aria-live="polite" aria-atomic="false">
          {giftLines.map((line, i) => (
            <p
              key={i}
              className={[
                'first-gift__line',
                visibleLines.includes(i) ? 'first-gift__line--visible' : '',
                line === 'Let\'s begin.' ? 'first-gift__line--closing' : '',
              ].filter(Boolean).join(' ')}
              aria-hidden={!visibleLines.includes(i)}
            >
              {line}
            </p>
          ))}
        </div>

        {showContinue && (
          <button
            className="phase__continue-btn"
            onClick={onComplete}
            autoFocus
            aria-label="Continue to account setup"
          >
            Continue
          </button>
        )}
      </div>

      {!showContinue && (
        <button
          className="phase__back-btn phase__back-btn--subtle"
          onClick={onBack}
          aria-label="Go back"
        >
          ← Back
        </button>
      )}
    </div>
  );
}
