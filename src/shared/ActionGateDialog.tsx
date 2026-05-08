/**
 * src/shared/ActionGateDialog.tsx
 *
 * ActionGate confirmation dialog — Task 4 of C-TODAY sprint.
 *
 * Listens for 'action-gate-confirm' custom window events dispatched
 * by the useActionGate hook (which polls the backend SSE log bridge
 * or receives Tauri IPC events).
 *
 * Renders a modal overlay with:
 *   - Risk tier badge (GREEN / YELLOW / RED)
 *   - Action type + human-readable description
 *   - Countdown timer showing remaining decision window
 *   - Approve / Deny buttons
 *
 * On decision: POSTs to /action-gate/respond with {request_id, approved}.
 * On timeout: the backend handles the default automatically (YELLOW →
 * approved on silence, RED → blocked on silence). The dialog simply
 * closes when the timer reaches zero.
 *
 * Canon: Doc 35 (Security), Doc 21 (Sovereignty)
 */

import React, { useEffect, useRef, useState } from 'react';
import './ActionGateDialog.css';
import { useActionGate } from '../hooks/useActionGate';

// ---- Sub-components -------------------------------------------------------

const TierBadge: React.FC<{ tier: string }> = ({ tier }) => (
  <span
    className={`action-gate-dialog__tier action-gate-dialog__tier--${tier}`}
    aria-label={`Risk tier: ${tier.toUpperCase()}`}
  >
    {tier.toUpperCase()}
  </span>
);

const Countdown: React.FC<{ seconds: number }> = ({ seconds }) => (
  <span
    className={`action-gate-dialog__countdown${seconds <= 10 ? ' action-gate-dialog__countdown--urgent' : ''}`}
    aria-live="polite"
  >
    {seconds}s
  </span>
);

// ---- Main component -------------------------------------------------------

export const ActionGateDialog: React.FC = () => {
  const { pending, resolve } = useActionGate();
  const [secondsLeft, setSecondsLeft] = useState<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentEvent = pending[0] ?? null;

  // Countdown timer tied to the current pending event
  useEffect(() => {
    if (!currentEvent) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }
    setSecondsLeft(currentEvent.timeout);
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setSecondsLeft(s => {
        if (s <= 1) {
          if (timerRef.current) clearInterval(timerRef.current);
          // Backend handles default on timeout — just close the dialog
          resolve(currentEvent.request_id, currentEvent.default);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [currentEvent?.request_id]);

  if (!currentEvent) return null;

  function handleDecision(approved: boolean): void {
    if (timerRef.current) clearInterval(timerRef.current);
    resolve(currentEvent!.request_id, approved);
  }

  const isRed = currentEvent.tier === 'red';
  const defaultLabel = currentEvent.default ? 'Approved on silence' : 'Blocked on silence';

  return (
    <div
      className="action-gate-overlay"
      role="alertdialog"
      aria-modal="true"
      aria-label="GAIA Action Gate — Human Sovereignty Confirmation"
    >
      <div className={`action-gate-dialog action-gate-dialog--${currentEvent.tier}`}>

        <header className="action-gate-dialog__header">
          <TierBadge tier={currentEvent.tier} />
          <h2 className="action-gate-dialog__title">Action Requires Approval</h2>
          <Countdown seconds={secondsLeft} />
        </header>

        <section className="action-gate-dialog__body">
          <p className="action-gate-dialog__type">
            <span className="action-gate-dialog__label">Type</span>
            <code className="action-gate-dialog__value">{currentEvent.type}</code>
          </p>
          <p className="action-gate-dialog__description">
            <span className="action-gate-dialog__label">Description</span>
            <span className="action-gate-dialog__value">{currentEvent.description}</span>
          </p>
          <p className="action-gate-dialog__default">
            <span className="action-gate-dialog__label">On timeout</span>
            <span className="action-gate-dialog__value">{defaultLabel}</span>
          </p>
        </section>

        <footer className="action-gate-dialog__footer">
          {isRed && (
            <p className="action-gate-dialog__sovereign-notice" role="note">
              ◆ Your explicit approval is required. Silence blocks this action.
            </p>
          )}
          <div className="action-gate-dialog__buttons">
            <button
              className="action-gate-dialog__btn action-gate-dialog__btn--deny"
              onClick={() => handleDecision(false)}
              aria-label="Deny this action"
            >
              ■ Deny
            </button>
            <button
              className="action-gate-dialog__btn action-gate-dialog__btn--approve"
              onClick={() => handleDecision(true)}
              aria-label="Approve this action"
            >
              ✔ Approve
            </button>
          </div>
        </footer>

        {pending.length > 1 && (
          <div className="action-gate-dialog__queue" aria-live="polite">
            +{pending.length - 1} more action{pending.length - 1 > 1 ? 's' : ''} queued
          </div>
        )}
      </div>
    </div>
  );
};

export default ActionGateDialog;
