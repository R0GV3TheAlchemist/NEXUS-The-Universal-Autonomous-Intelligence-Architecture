/**
 * Phase 3 — The Name Covenant
 * Canon: GAIAN_TWIN_DOCTRINE, SLOW_PROTOCOL, C17
 *
 * GAIA asks the human their name.
 * Not a form field. Not a username.
 * A covenant — the first thing the Twin will remember forever.
 *
 * This is the first HEAVY-weight memory in the Temporal Braid.
 * The name is sacred. It is never forgotten.
 *
 * The ask is slow. Gentle. Unhurried.
 * The human can take as long as they need.
 */

import { useState, useRef, useEffect } from 'react';
import { useOnboardingStore } from '../store/onboardingStore';

interface Props {
  onComplete: () => void;
  onBack: () => void;
}

export function Phase3NameCovenant({ onComplete, onBack }: Props) {
  const setData = useOnboardingStore((s) => s.setData);
  const storedName = useOnboardingStore((s) => s.data.name ?? '');

  const [name, setName] = useState(storedName);
  const [submitted, setSubmitted] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus the input on mount — the question deserves attention
  useEffect(() => {
    const timer = setTimeout(() => inputRef.current?.focus(), 600);
    return () => clearTimeout(timer);
  }, []);

  // Keyboard: Escape = back
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onBack();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onBack]);

  const handleSubmit = () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    setData({ name: trimmed });
    setSubmitted(true);
    // The Twin acknowledges — then moves on
    setTimeout(() => setAcknowledged(true), 1000);
    setTimeout(() => onComplete(), 2600);
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div className="phase phase--name-covenant" role="main">
      {!submitted ? (
        <>
          {/* The question */}
          <div className="name-covenant__question" aria-live="polite">
            <p className="name-covenant__ask">
              What's your name?
            </p>
            <p className="name-covenant__sub">
              This is the first thing I'll remember about you.
            </p>
          </div>

          {/* The input — styled to feel like writing, not typing */}
          <div className="name-covenant__input-wrap">
            <input
              ref={inputRef}
              type="text"
              className="name-covenant__input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Your name..."
              autoComplete="off"
              autoCapitalize="words"
              spellCheck={false}
              maxLength={60}
              aria-label="Your name"
            />
            <div
              className="name-covenant__underline"
              style={{ transform: name ? 'scaleX(1)' : 'scaleX(0)' }}
            />
          </div>

          {/* Continue — appears only once the human has typed something */}
          {name.trim() && (
            <button
              className="phase__continue-btn phase__continue-btn--name"
              onClick={handleSubmit}
              aria-label={`Continue as ${name}`}
            >
              That's my name
            </button>
          )}

          <button
            className="phase__back-btn"
            onClick={onBack}
            aria-label="Go back"
          >
            ← Back
          </button>
        </>
      ) : (
        /* The acknowledgement — GAIA receives the name */
        <div className="name-covenant__acknowledgement" aria-live="polite">
          {!acknowledged ? (
            <p className="name-covenant__receiving">
              {name.trim()}...
            </p>
          ) : (
            <p className="name-covenant__received">
              {name.trim()}. <span className="name-covenant__held">I'll remember that.</span>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
