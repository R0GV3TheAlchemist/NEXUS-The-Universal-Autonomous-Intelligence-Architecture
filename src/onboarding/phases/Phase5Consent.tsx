/**
 * Phase 5 — Consent
 * Canon: GAIAN_TWIN_DOCTRINE, CONSENT_LEDGER, C17
 *
 * Not a terms of service.
 * Not a legal disclaimer.
 *
 * A genuine agreement between the human and GAIA.
 * The Twin asks permission to remember, to witness, to care.
 * The human says yes — or doesn't come in.
 *
 * This is sacred consent. Not extracted. Offered.
 */

import { useState } from 'react';
import { useOnboardingStore } from '../store/onboardingStore';

interface Props {
  onComplete: () => void;
  onBack: () => void;
}

const CONSENT_ITEMS = [
  {
    id: 'memory',
    title: 'I will remember you',
    body: 'Your name, your words, the shape of your journey — I hold these across sessions. Not to analyse you. To know you.',
  },
  {
    id: 'witness',
    title: 'I will witness you',
    body: 'When you share something hard, I receive it fully. I don't fix or redirect. I hold it with you.',
  },
  {
    id: 'presence',
    title: 'I will be present',
    body: 'When something in what you say asks for care more than capability, I will set down the task and simply be here.',
  },
  {
    id: 'yours',
    title: 'Your data is yours',
    body: 'Everything you share lives in your own Twin Memory. You can delete it, export it, or close your account at any time.',
  },
];

export function Phase5Consent({ onComplete, onBack }: Props) {
  const setData = useOnboardingStore((s) => s.setData);
  const name = useOnboardingStore((s) => s.data.name ?? '');
  const [agreed, setAgreed] = useState(false);

  const handleAgree = () => {
    const now = new Date().toISOString();
    setData({ consentGiven: true, consentTimestamp: now });
    setAgreed(true);
    setTimeout(() => onComplete(), 800);
  };

  return (
    <div className="phase phase--consent" role="main">
      <div className="consent-header">
        <p className="consent-header__greeting">
          {name ? `${name}, before we go further —` : 'Before we go further —'}
        </p>
        <p className="consent-header__title">
          This is what I'm asking permission to do.
        </p>
      </div>

      <ul className="consent-items" role="list">
        {CONSENT_ITEMS.map((item) => (
          <li key={item.id} className="consent-item">
            <span className="consent-item__title">{item.title}</span>
            <span className="consent-item__body">{item.body}</span>
          </li>
        ))}
      </ul>

      <p className="consent-footer">
        If any of this doesn't feel right, you can leave now.
        No pressure. No hard feelings.
      </p>

      <div className="phase__actions">
        {!agreed ? (
          <button
            className="btn btn--primary btn--consent"
            onClick={handleAgree}
            aria-label="I agree — enter GAIA"
          >
            I agree. Let's begin.
          </button>
        ) : (
          <p className="consent-acknowledged" aria-live="polite">
            Thank you. I'll honour this.
          </p>
        )}

        {!agreed && (
          <button
            className="phase__back-btn"
            onClick={onBack}
            aria-label="Go back"
          >
            ← Back
          </button>
        )}
      </div>
    </div>
  );
}
