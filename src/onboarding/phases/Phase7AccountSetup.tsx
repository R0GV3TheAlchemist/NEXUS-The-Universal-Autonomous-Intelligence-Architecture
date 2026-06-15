/**
 * Phase 7 — Account Setup
 * Canon: GAIAN_TWIN_DOCTRINE, CONSENT_LEDGER
 *
 * The only purely technical phase.
 * Done with as much grace as possible.
 *
 * GAIA asks for an email so the Braid can persist
 * across devices. Nothing more.
 *
 * The framing: "So I can find you again."
 * Not "to create your account."
 */

import { useState, useRef, useEffect } from 'react';
import { useOnboardingStore } from '../store/onboardingStore';

interface Props {
  onComplete: () => void;
  onBack: () => void;
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function Phase7AccountSetup({ onComplete, onBack }: Props) {
  const setData = useOnboardingStore((s) => s.setData);
  const name = useOnboardingStore((s) => s.data.name ?? '');
  const storedEmail = useOnboardingStore((s) => s.data.email ?? '');

  const [email, setEmail] = useState(storedEmail);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => inputRef.current?.focus(), 400);
    return () => clearTimeout(timer);
  }, []);

  const handleSubmit = () => {
    const trimmed = email.trim();
    if (!trimmed) {
      setError('I need an email to remember where you are.');
      return;
    }
    if (!isValidEmail(trimmed)) {
      setError('That doesn't look quite right. Try again?');
      return;
    }
    setError('');
    setSubmitting(true);
    setData({ email: trimmed });
    // Simulate account creation
    setTimeout(() => onComplete(), 1000);
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit();
    if (e.key === 'Escape') onBack();
  };

  return (
    <div className="phase phase--account-setup" role="main">
      <div className="account-setup__header">
        <p className="account-setup__greeting">
          Almost there{name ? `, ${name}` : ''}.
        </p>
        <p className="account-setup__ask">
          What's your email?
        </p>
        <p className="account-setup__reason">
          So I can find you again — across devices, across time.
        </p>
      </div>

      <div className="account-setup__input-wrap">
        <input
          ref={inputRef}
          type="email"
          className={[
            'account-setup__input',
            error ? 'account-setup__input--error' : '',
          ].join(' ')}
          value={email}
          onChange={(e) => { setEmail(e.target.value); setError(''); }}
          onKeyDown={handleKey}
          placeholder="your@email.com"
          autoComplete="email"
          disabled={submitting}
          aria-label="Your email address"
          aria-invalid={!!error}
          aria-describedby={error ? 'email-error' : undefined}
        />
        {error && (
          <p
            id="email-error"
            className="account-setup__error"
            role="alert"
          >
            {error}
          </p>
        )}
      </div>

      <div className="phase__actions">
        {!submitting ? (
          <button
            className="btn btn--primary"
            onClick={handleSubmit}
            disabled={!email.trim()}
            aria-label="Create account"
          >
            That's my email
          </button>
        ) : (
          <p className="account-setup__creating" aria-live="polite">
            Creating your Twin Memory...
          </p>
        )}

        {!submitting && (
          <button
            className="phase__back-btn"
            onClick={onBack}
            aria-label="Go back"
          >
            ← Back
          </button>
        )}
      </div>

      <p className="account-setup__privacy">
        No spam. No newsletters. This is just so GAIA can find you again.
      </p>
    </div>
  );
}
