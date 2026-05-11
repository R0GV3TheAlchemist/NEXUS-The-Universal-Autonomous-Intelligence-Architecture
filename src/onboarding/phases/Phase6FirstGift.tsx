// C-OB01 — Phase 6: The First Gift
// GAIA gives something based on user intent before asking anything more.
// Intentional inversion of standard onboarding psychology.

import React, { useMemo } from 'react';
import { useOnboardingStore } from '../store/onboardingStore';

interface Gift {
  title: string;
  body: string;
  action?: string;
}

function selectGift(intent: string[]): Gift {
  if (intent.includes('productivity')) {
    return {
      title: 'Your Daily Briefing ritual',
      body: "A pre-built template to start each day with GAIA — your tasks, your intentions, your context. It's ready when you are.",
      action: 'Open Daily Briefing',
    };
  }
  if (intent.includes('exploration')) {
    return {
      title: "How GAIA's memory works",
      body: "A short interactive walkthrough of how I remember things, what I notice, and how you can guide what I learn about you.",
      action: 'Show me',
    };
  }
  if (intent.includes('self_discovery')) {
    return {
      title: 'A question to begin with',
      body: "What's one thing you want more of in your life right now?",
      action: 'Tell GAIA',
    };
  }
  if (intent.includes('privacy')) {
    return {
      title: 'Where your data lives',
      body: 'A visual map of exactly where GAIA stores data on your device — every file, every folder, every path. Nothing hidden.',
      action: 'Show me the map',
    };
  }
  if (intent.includes('building')) {
    return {
      title: 'An empty canvas',
      body: "A blank project space with me ready to think alongside you. Bring an idea — or just start talking.",
      action: 'Open canvas',
    };
  }
  // Default
  return {
    title: 'A place to begin',
    body: 'GAIA is ready. Explore at whatever pace feels right. There is no wrong way to start.',
    action: 'Continue',
  };
}

export function Phase6FirstGift() {
  const intent = useOnboardingStore((s) => s.intent);
  const nextPhase = useOnboardingStore((s) => s.nextPhase);

  const gift = useMemo(() => selectGift(intent), [intent]);

  return (
    <section className="phase phase--first-gift" aria-label="Your first gift from GAIA">
      <div className="phase__content phase__content--centered">
        <p className="gaia-aside">
          Here's something to start with. There's no right way to use this.
        </p>
        <div className="gift-card" role="region" aria-label={gift.title}>
          <h2 className="gift-card__title">{gift.title}</h2>
          <p className="gift-card__body">{gift.body}</p>
          {gift.action && (
            <button
              className="btn btn--secondary"
              onClick={() => {
                // Gift-specific action hook — extend per gift type in future
                nextPhase();
              }}
            >
              {gift.action}
            </button>
          )}
        </div>
        <button
          className="btn btn--ghost btn--small"
          onClick={nextPhase}
          aria-label="Skip this and continue"
        >
          Skip for now
        </button>
      </div>
    </section>
  );
}
