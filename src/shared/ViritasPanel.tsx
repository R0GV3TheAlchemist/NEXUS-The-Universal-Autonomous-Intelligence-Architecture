/**
 * src/shared/ViritasPanel.tsx
 * GAIA-OS — Viriditas Expanded Detail Panel
 * Issue #68 Phase 5
 *
 * A floating Crystal-card panel that slides in above the rail
 * alignment slot when the user clicks the expand button on
 * ViritasWidget. Shows:
 *
 *   1. Header   — score, tier badge, last-updated time
 *   2. Sparkline — ScoreSparkline for overall score + session stats
 *   3. Signals  — animated progress bars: HRV, Schumann, Kp
 *   4. Narrative — contextual two-line description of current state
 *
 * Props:
 *   open      — boolean           panel visibility
 *   onClose   — () => void        close callback
 *   state     — AlignmentState | null
 *   history   — ScoreHistory
 *
 * Animation: GSAP translateY slide-in on open, slide-out on close.
 * Closes on Escape key press and click outside the panel.
 */

import React, { useEffect, useRef, useCallback } from 'react';
import gsap from 'gsap';
import type { AlignmentState, AlignmentTier } from '../hooks/useAlignment';
import type { ScoreHistory }                   from '../hooks/useScoreHistory';
import { ScoreSparkline }                       from './ScoreSparkline';
import './ViritasPanel.css';

// ---------------------------------------------------------------------------
// Tier narrative map
// Provides a two-line contextual reading of the current state.
// ---------------------------------------------------------------------------

const TIER_NARRATIVE: Record<AlignmentTier, [string, string]> = {
  minimal: [
    'Your system is in restorative mode.',
    'Rest deeply — coherence will rise naturally.',
  ],
  core: [
    'Grounding rhythms detected.',
    'You are stabilising. Slow breathing will accelerate recovery.',
  ],
  standard: [
    'Balanced coherence across all signals.',
    'A good state for focused, intentional work.',
  ],
  full: [
    'High biometric coherence achieved.',
    'Your heart, mind and field are aligned.',
  ],
  vibrant: [
    'Peak viriditas — all signals in resonance.',
    'This is your most expansive creative and cognitive state.',
  ],
};

const TIER_BADGES: Record<AlignmentTier, string> = {
  minimal:  'Restorative',
  core:     'Grounding',
  standard: 'Balanced',
  full:     'Coherent',
  vibrant:  'Vibrant',
};

function prefersReducedMotion(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

function formatTime(isoString: string): string {
  try {
    return new Date(isoString).toLocaleTimeString([], {
      hour:   '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return '';
  }
}

// ---------------------------------------------------------------------------
// Kp score: invert for display (low Kp = good coherence)
// Kp 0 → 100%, Kp 9 → 0% (capped at 9)
// ---------------------------------------------------------------------------
function kpToBar(kp: number): number {
  return Math.max(0, Math.round((1 - Math.min(kp, 9) / 9) * 100));
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface ViratasPanelProps {
  open:    boolean;
  onClose: () => void;
  state:   AlignmentState | null;
  history: ScoreHistory;
}

export const ViritasPanel: React.FC<ViratasPanelProps> = ({
  open,
  onClose,
  state,
  history,
}) => {
  const panelRef    = useRef<HTMLDivElement>(null);
  const overlayRef  = useRef<HTMLDivElement>(null);
  const isAnimating = useRef(false);

  const tier: AlignmentTier = state?.ui_tier ?? 'standard';
  const score  = state?.score        ?? 0;
  const hrv    = state?.hrv_score    ?? 0;
  const schum  = state?.schumann_score ?? 0;
  const kp     = state?.solar_kp     ?? 0;
  const kpBar  = kpToBar(kp);
  const [narrativeLine1, narrativeLine2] = TIER_NARRATIVE[tier];

  // —— Slide-in / slide-out ——
  useEffect(() => {
    const el = panelRef.current;
    if (!el) return;
    if (isAnimating.current) return;

    if (open) {
      el.style.display = 'flex';
      if (prefersReducedMotion()) {
        gsap.set(el, { opacity: 1, y: 0 });
      } else {
        isAnimating.current = true;
        gsap.fromTo(
          el,
          { opacity: 0, y: 24 },
          {
            opacity:  1,
            y:        0,
            duration: 0.35,
            ease:     'power3.out',
            onComplete: () => { isAnimating.current = false; },
          },
        );
      }
    } else {
      if (prefersReducedMotion()) {
        el.style.display = 'none';
      } else {
        isAnimating.current = true;
        gsap.to(el, {
          opacity:  0,
          y:        16,
          duration: 0.22,
          ease:     'power2.in',
          onComplete: () => {
            el.style.display = 'none';
            isAnimating.current = false;
          },
        });
      }
    }
  }, [open]);

  // —— Escape key ——
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && open) onClose();
  }, [open, onClose]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // —— Outside click (on the overlay) ——
  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  }, [onClose]);

  return (
    <div
      ref={overlayRef}
      className={`viriditas-panel-overlay${open ? ' viriditas-panel-overlay--open' : ''}`}
      onClick={handleOverlayClick}
      aria-hidden={!open}
    >
      <div
        ref={panelRef}
        className={`viriditas-panel crystal-card crystal-card--elevated viriditas-panel--${tier}`}
        role="dialog"
        aria-label="Alignment detail"
        aria-modal="false"
        style={{ display: 'none' }}
      >

        {/* ── Header ──────────────────────────────────────── */}
        <div className="viriditas-panel__header">
          <div className="viriditas-panel__score-block">
            <span className="viriditas-panel__score-num">{Math.round(score)}</span>
            <span className="viriditas-panel__score-label">/ 100</span>
          </div>
          <div className="viriditas-panel__meta">
            <span className={`viriditas-panel__tier-badge viriditas-panel__tier-badge--${tier}`}>
              {TIER_BADGES[tier]}
            </span>
            {state?.last_updated && (
              <span className="viriditas-panel__updated">
                {formatTime(state.last_updated)}
              </span>
            )}
            {state?.fallback_mode && (
              <span className="viriditas-panel__fallback">
                {state.fallback_mode.replace(/_/g, ' ')}
              </span>
            )}
          </div>
          <button
            className="viriditas-panel__close"
            onClick={onClose}
            aria-label="Close alignment panel"
          >×</button>
        </div>

        {/* ── Sparkline ─────────────────────────────────────── */}
        <div className="viriditas-panel__sparkline-wrap">
          <ScoreSparkline scores={history.scores} height={52} />
          <div className="viriditas-panel__spark-legend">
            <span className="viriditas-panel__spark-stat">
              ▼ {history.sessionMin}
            </span>
            <span className="viriditas-panel__spark-avg">
              avg {history.sessionAvg}
            </span>
            <span className="viriditas-panel__spark-stat">
              ▲ {history.sessionMax}
            </span>
            <span className={`viriditas-panel__trend viriditas-panel__trend--${history.trendDir}`}>
              {history.trendDir === 'rising'  ? '↗ rising'  :
               history.trendDir === 'falling' ? '↘ falling' : '→ stable'}
            </span>
          </div>
        </div>

        {/* ── Signal bars ───────────────────────────────────── */}
        <div className="viriditas-panel__signals">

          <div className="viriditas-panel__signal-row">
            <span className="viriditas-panel__signal-label">♥ HRV</span>
            <div className="viriditas-panel__bar-track">
              <div
                className="viriditas-panel__bar-fill viriditas-panel__bar-fill--hrv"
                style={{ '--bar-pct': `${Math.round(hrv)}%` } as React.CSSProperties}
              />
            </div>
            <span className="viriditas-panel__signal-val">{Math.round(hrv)}</span>
          </div>

          <div className="viriditas-panel__signal-row">
            <span className="viriditas-panel__signal-label">🌊 Schumann</span>
            <div className="viriditas-panel__bar-track">
              <div
                className="viriditas-panel__bar-fill viriditas-panel__bar-fill--schumann"
                style={{ '--bar-pct': `${Math.round(schum)}%` } as React.CSSProperties}
              />
            </div>
            <span className="viriditas-panel__signal-val">{Math.round(schum)}</span>
          </div>

          <div className="viriditas-panel__signal-row">
            <span className="viriditas-panel__signal-label">☀️ Kp index</span>
            <div className="viriditas-panel__bar-track">
              <div
                className="viriditas-panel__bar-fill viriditas-panel__bar-fill--kp"
                style={{ '--bar-pct': `${kpBar}%` } as React.CSSProperties}
              />
            </div>
            <span className="viriditas-panel__signal-val">{kp.toFixed(1)}</span>
          </div>

        </div>

        {/* ── Narrative ─────────────────────────────────────── */}
        <div className="viriditas-panel__narrative crystal-panel">
          <p className="viriditas-panel__narrative-line1">{narrativeLine1}</p>
          <p className="viriditas-panel__narrative-line2">{narrativeLine2}</p>
        </div>

      </div>
    </div>
  );
};

export default ViritasPanel;
