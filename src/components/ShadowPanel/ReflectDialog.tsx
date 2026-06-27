/**
 * src/components/ShadowPanel/ReflectDialog.tsx
 * GAIA-OS — Reflect Confirmation Dialog
 *
 * A three-state native <dialog> that gates the shadow.reflect() action:
 *
 *   idle      →  prompt (confirm / cancel)
 *   pending   →  spinner while reflect() awaits
 *   done      →  success confirmation with integration delta
 *
 * Usage:
 *   <ReflectDialog
 *     open={reflectOpen}
 *     integrationPct={shadow.integrationPct}
 *     dominantArchetype={shadow.dominantArchetype}
 *     dominantColor={dominantColor}
 *     onConfirm={shadow.reflect}
 *     onClose={() => setReflectOpen(false)}
 *   />
 *
 * Design contract:
 *   • Never fires onConfirm more than once per open.
 *   • Resets to idle every time open transitions false → true.
 *   • Escape and backdrop click cancel (idle) or dismiss (done).
 *   • Uses the shadow CSS custom-property vocabulary: --sp-hue, --sp-dominant.
 *
 * Canon: Shadow Engine — 7-Archetype Integration Layer
 */

import React, {
  useEffect,
  useRef,
  useCallback,
  useState,
} from 'react';
import type { ShadowArchetypeName } from '../../shared/shadowTypes';
import './reflect-dialog.css';

// ── Archetype colour map (keep in sync with ArchetypeDrawer) ──────────────

const ARCHETYPE_HUES: Partial<Record<ShadowArchetypeName, string>> = {
  Orphan:    '#7c9ef5',
  Warrior:   '#f55c5c',
  Wanderer:  '#f5c842',
  Caregiver: '#5cf592',
  Seeker:    '#42e8d5',
  Destroyer: '#e07b39',
  Creator:   '#b28aff',
};

const ARCHETYPE_GLYPHS: Partial<Record<ShadowArchetypeName, string>> = {
  Orphan:    '◯',
  Warrior:   '⚔',
  Wanderer:  '↯',
  Caregiver: '❧',
  Seeker:    '◎',
  Destroyer: '⬙',
  Creator:   '✶',
};

// Reflection prompts — one is picked at random on each open.
// Each nudges the user toward genuine introspection before confirming.
const REFLECTION_PROMPTS: string[] = [
  'What arose in you today that you would rather not have seen?',
  'Where did you resist something that was trying to move through you?',
  'What feeling did you push away this week rather than letting it speak?',
  'Name one pattern you noticed in yourself that you did not choose.',
  'What did you judge in another that you recognise in yourself?',
  'Where did you abandon yourself to keep peace with someone else?',
  'What were you afraid others would see if you let your guard down?',
];

function randomPrompt(): string {
  return REFLECTION_PROMPTS[Math.floor(Math.random() * REFLECTION_PROMPTS.length)];
}

// ── Dialog state machine ───────────────────────────────────────────────────────

type Phase = 'idle' | 'pending' | 'done';

// ── Props ─────────────────────────────────────────────────────────────────

export interface ReflectDialogProps {
  open:              boolean;
  integrationPct:    number;                      // 0–100, before reflect
  dominantArchetype: ShadowArchetypeName | null;
  onConfirm:         () => Promise<void>;         // shadow.reflect()
  onClose:           () => void;
}

// ── Component ────────────────────────────────────────────────────────────

export function ReflectDialog({
  open,
  integrationPct,
  dominantArchetype,
  onConfirm,
  onClose,
}: ReflectDialogProps) {
  const dialogRef  = useRef<HTMLDialogElement>(null);
  const [phase,   setPhase]  = useState<Phase>('idle');
  const [prompt,  setPrompt] = useState(randomPrompt);
  const firedRef  = useRef(false);   // guard: never fire onConfirm twice per open

  // Reset on every open transition
  useEffect(() => {
    if (open) {
      setPhase('idle');
      setPrompt(randomPrompt());
      firedRef.current = false;
    }
  }, [open]);

  // Sync native <dialog> open state
  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    else if (!open && el.open) el.close();
  }, [open]);

  // 'cancel' fires on Escape
  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    const handler = (e: Event) => {
      e.preventDefault();
      if (phase !== 'pending') onClose();
    };
    el.addEventListener('cancel', handler);
    return () => el.removeEventListener('cancel', handler);
  }, [phase, onClose]);

  // Backdrop click
  const handleBackdropClick = useCallback(
    (e: React.MouseEvent<HTMLDialogElement>) => {
      if (e.target === dialogRef.current && phase !== 'pending') onClose();
    },
    [phase, onClose],
  );

  const handleConfirm = useCallback(async () => {
    if (firedRef.current || phase !== 'idle') return;
    firedRef.current = true;
    setPhase('pending');
    try {
      await onConfirm();
      setPhase('done');
    } catch {
      // If the reflect call fails, drop back to idle so the user can retry
      firedRef.current = false;
      setPhase('idle');
    }
  }, [phase, onConfirm]);

  const hue   = dominantArchetype ? (ARCHETYPE_HUES[dominantArchetype] ?? 'var(--color-primary)') : 'var(--color-primary)';
  const glyph = dominantArchetype ? (ARCHETYPE_GLYPHS[dominantArchetype] ?? '◎') : '◎';

  return (
    <dialog
      ref={dialogRef}
      className={`rd rd--${phase}`}
      style={{ '--sp-hue': hue } as React.CSSProperties}
      aria-label="Reflection confirmation"
      aria-modal="true"
      onClick={handleBackdropClick}
    >
      <div className="rd__card" role="document">

        {/* ── IDLE phase — prompt + confirm/cancel ── */}
        {phase === 'idle' && (
          <>
            <div className="rd__glyph" aria-hidden>{glyph}</div>

            <h2 className="rd__title">Record a reflection</h2>

            <p className="rd__instruction">
              Sit with this question for a moment before confirming:
            </p>

            <blockquote className="rd__prompt">
              &ldquo;{prompt}&rdquo;
            </blockquote>

            <p className="rd__effect">
              Confirming will add <strong>+5%</strong> to your integration progress.
            </p>

            <div className="rd__progress-preview">
              <div className="rd__progress-track">
                <div
                  className="rd__progress-before"
                  style={{ '--sp-pct': `${integrationPct}%` } as React.CSSProperties}
                />
                <div
                  className="rd__progress-delta"
                  style={{
                    '--sp-start': `${integrationPct}%`,
                    '--sp-width': `${Math.min(5, 100 - integrationPct)}%`,
                  } as React.CSSProperties}
                />
              </div>
              <div className="rd__progress-labels">
                <span>{integrationPct}%</span>
                <span className="rd__progress-plus">+5% → {Math.min(100, integrationPct + 5)}%</span>
              </div>
            </div>

            <div className="rd__actions">
              <button
                className="rd__cancel"
                onClick={onClose}
                type="button"
              >
                Cancel
              </button>
              <button
                className="rd__confirm"
                onClick={handleConfirm}
                type="button"
                autoFocus
              >
                ◎&ensp;Confirm Reflection
              </button>
            </div>
          </>
        )}

        {/* ── PENDING phase — spinner ── */}
        {phase === 'pending' && (
          <div className="rd__pending" aria-label="Recording reflection…" aria-live="polite">
            <div className="rd__spinner" aria-hidden />
            <p className="rd__pending-label">Recording…</p>
          </div>
        )}

        {/* ── DONE phase — success ── */}
        {phase === 'done' && (
          <>
            <div className="rd__done-glyph" aria-hidden>✓</div>
            <h2 className="rd__title">Reflection recorded</h2>
            <p className="rd__done-body">
              Integration updated to{' '}
              <strong>{Math.min(100, integrationPct + 5)}%</strong>.
              The shadow acknowledges your attention.
            </p>
            <div className="rd__actions rd__actions--single">
              <button
                className="rd__confirm"
                onClick={onClose}
                type="button"
                autoFocus
              >
                Done
              </button>
            </div>
          </>
        )}

      </div>
    </dialog>
  );
}

export default ReflectDialog;
