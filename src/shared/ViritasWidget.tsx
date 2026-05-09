/**
 * src/shared/ViritasWidget.tsx
 *
 * GAIA-OS Viriditas Biometric Alignment Widget
 * Pillar II: Viriditas — Issue #64 (Phase 2, frontend)
 *
 * Renders a tier-driven animated orb + score ring that reflects the
 * current Schumann–HRV alignment state fetched by `useAlignment`.
 *
 * Props:
 *   rawRmssd     — live RMSSD from wearable (ms), or null
 *   showDetail   — show HRV / Schumann sub-scores + Kp badge (default false)
 *   className    — optional additional class names
 *
 * Tier colours are driven by CSS custom properties on [data-tier],
 * so they automatically match any future design-token theme updates.
 *
 * Accessibility:
 *   role="status" + aria-live="polite" so screen readers announce
 *   tier changes without interrupting the current focus.
 */

import React, { useMemo } from 'react';
import { useAlignment, AlignmentTier } from '../hooks/useAlignment';
import './ViritasWidget.css';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RING_RADIUS  = 42;                         // px, inside 100x100 viewBox
const CIRCUMF      = 2 * Math.PI * RING_RADIUS;  // ~263.9

const TIER_LABELS: Record<AlignmentTier, string> = {
  minimal:  'Restorative',
  core:     'Grounding',
  standard: 'Balanced',
  full:     'Coherent',
  vibrant:  'Vibrant',
};

const TIER_ICONS: Record<AlignmentTier, string> = {
  minimal:  '🌑',
  core:     '🌒',
  standard: '🌕',
  full:     '✨',
  vibrant:  '🌟',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface ViritasWidgetProps {
  rawRmssd?:   number | null;
  showDetail?: boolean;
  className?:  string;
}

export const ViritasWidget: React.FC<ViritasWidgetProps> = ({
  rawRmssd   = null,
  showDetail = false,
  className  = '',
}) => {
  const { state, loading, error, refresh } = useAlignment(rawRmssd);

  // Stroke dasharray: filled arc proportional to score
  const dashArray = useMemo(() => {
    const score = state?.score ?? 50;
    const filled = (score / 100) * CIRCUMF;
    return `${filled.toFixed(2)} ${(CIRCUMF - filled).toFixed(2)}`;
  }, [state?.score]);

  const tier: AlignmentTier = state?.ui_tier ?? 'standard';
  const score = state?.score ?? 50;
  const isFallback = !!state?.fallback_mode;

  return (
    <div
      className={`viriditas-widget viriditas-widget--${tier}${className ? ` ${className}` : ''}`}
      data-tier={tier}
      data-fallback={isFallback ? 'true' : 'false'}
      role="status"
      aria-live="polite"
      aria-label={`Alignment: ${
        loading ? 'loading' : error ? 'unavailable' : `${TIER_LABELS[tier]}, ${Math.round(score)} of 100`
      }`}
    >
      {/* ── Animated orb ──────────────────────────────────────── */}
      <div className="viriditas-widget__orb-wrap" aria-hidden="true">
        <svg
          className="viriditas-widget__ring"
          viewBox="0 0 100 100"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* track */}
          <circle
            cx="50" cy="50" r={RING_RADIUS}
            className="viriditas-widget__ring-track"
            fill="none"
            strokeWidth="6"
          />
          {/* filled arc */}
          <circle
            cx="50" cy="50" r={RING_RADIUS}
            className="viriditas-widget__ring-fill"
            fill="none"
            strokeWidth="6"
            strokeDasharray={dashArray}
            strokeDashoffset="0"
            strokeLinecap="round"
            transform="rotate(-90 50 50)"
          />
        </svg>

        {/* pulsing orb core */}
        <div
          className={`viriditas-widget__orb${
            loading ? ' viriditas-widget__orb--loading' : ''
          }`}
          aria-hidden="true"
        >
          <span className="viriditas-widget__icon">
            {error ? '🛑' : loading ? '◯' : TIER_ICONS[tier]}
          </span>
        </div>
      </div>

      {/* ── Score + tier label ─────────────────────────────── */}
      <div className="viriditas-widget__labels">
        <span className="viriditas-widget__score">
          {loading ? '—' : error ? 'offline' : Math.round(score)}
        </span>
        <span className="viriditas-widget__tier-label">
          {error ? 'Unavailable' : TIER_LABELS[tier]}
        </span>
      </div>

      {/* ── Detail panel (opt-in) ──────────────────────────── */}
      {showDetail && state && !error && (
        <div className="viriditas-widget__detail">
          <div className="viriditas-widget__detail-row">
            <span className="viriditas-widget__detail-label">♥ HRV</span>
            <span className="viriditas-widget__detail-value">
              {Math.round(state.hrv_score)}
            </span>
          </div>
          <div className="viriditas-widget__detail-row">
            <span className="viriditas-widget__detail-label">🌊 Schumann</span>
            <span className="viriditas-widget__detail-value">
              {Math.round(state.schumann_score)}
            </span>
          </div>
          <div className="viriditas-widget__detail-row">
            <span className="viriditas-widget__detail-label">☀️ Kp</span>
            <span
              className={`viriditas-widget__kp-badge${
                state.solar_kp >= 5 ? ' viriditas-widget__kp-badge--elevated' : ''
              }${
                state.solar_kp >= 8 ? ' viriditas-widget__kp-badge--storm' : ''
              }`}
            >
              {state.solar_kp.toFixed(1)}
            </span>
          </div>
          {state.fallback_mode && (
            <p className="viriditas-widget__fallback-note">
              {state.fallback_mode.replace(/_/g, ' ')}
            </p>
          )}
        </div>
      )}

      {/* ── Refresh button ───────────────────────────────────── */}
      <button
        className="viriditas-widget__refresh"
        onClick={refresh}
        disabled={loading}
        aria-label="Refresh alignment"
        title="Refresh alignment"
      >
        ↻
      </button>
    </div>
  );
};

export default ViritasWidget;
