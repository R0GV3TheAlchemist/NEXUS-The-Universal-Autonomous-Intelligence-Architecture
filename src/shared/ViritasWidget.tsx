/**
 * src/shared/ViritasWidget.tsx
 *
 * GAIA-OS Viriditas Biometric Alignment Widget
 * Pillar II: Viriditas — Issue #64 (Phase 2, frontend)
 * Issue #68 Phase 3: GSAP breathing animation
 * Issue #68 Phase 5: expand button + ViritasPanel
 *
 * Renders a tier-driven animated orb + score ring that reflects the
 * current Schumann–HRV alignment state fetched by `useAlignment`.
 *
 * Phase 5 change: adds an expand toggle button that opens ViritasPanel,
 * the full-detail floating panel with sparkline + signal bars + narrative.
 *
 * Props:
 *   rawRmssd     — live RMSSD from wearable (ms), or null
 *   showDetail   — legacy prop (kept for back-compat); use ViritasPanel
 *   className    — optional additional class names
 */

import React, { useMemo, useRef, useState } from 'react';
import { useAlignment, AlignmentTier }  from '../hooks/useAlignment';
import { useBreathingAnimation }         from '../hooks/useBreathingAnimation';
import { useScoreHistory }               from '../hooks/useScoreHistory';
import { ViritasPanel }                  from './ViritasPanel';
import './ViritasWidget.css';

const RING_RADIUS = 42;
const CIRCUMF     = 2 * Math.PI * RING_RADIUS;

const TIER_LABELS: Record<AlignmentTier, string> = {
  minimal:  'Restorative',
  core:     'Grounding',
  standard: 'Balanced',
  full:     'Coherent',
  vibrant:  'Vibrant',
};

const TIER_ICONS: Record<AlignmentTier, string> = {
  minimal:  '\uD83C\uDF11',
  core:     '\uD83C\uDF12',
  standard: '\uD83C\uDF15',
  full:     '\u2728',
  vibrant:  '\uD83C\uDF1F',
};

interface ViritasWidgetProps {
  rawRmssd?:   number | null;
  showDetail?: boolean; // legacy; ViritasPanel now handles detail
  className?:  string;
}

export const ViritasWidget: React.FC<ViritasWidgetProps> = ({
  rawRmssd  = null,
  className = '',
}) => {
  const { state, loading, error, refresh } = useAlignment(rawRmssd);
  const orbRef    = useRef<HTMLDivElement>(null);
  const [panelOpen, setPanelOpen] = useState(false);

  const dashArray = useMemo(() => {
    const score  = state?.score ?? 50;
    const filled = (score / 100) * CIRCUMF;
    return `${filled.toFixed(2)} ${(CIRCUMF - filled).toFixed(2)}`;
  }, [state?.score]);

  const tier: AlignmentTier = state?.ui_tier ?? 'standard';
  const score               = state?.score   ?? 50;
  const isFallback          = !!state?.fallback_mode;

  // Phase 3: GSAP breathing
  useBreathingAnimation(orbRef, tier);

  // Phase 5: score history for sparkline
  const history = useScoreHistory(state ?? null);

  return (
    <>
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
        {/* ── Animated orb ———————————————————————————————— */}
        <div className="viriditas-widget__orb-wrap" aria-hidden="true">
          <svg
            className="viriditas-widget__ring"
            viewBox="0 0 100 100"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle cx="50" cy="50" r={RING_RADIUS}
              className="viriditas-widget__ring-track"
              fill="none" strokeWidth="6"
            />
            <circle cx="50" cy="50" r={RING_RADIUS}
              className="viriditas-widget__ring-fill"
              fill="none" strokeWidth="6"
              strokeDasharray={dashArray}
              strokeDashoffset="0"
              strokeLinecap="round"
              transform="rotate(-90 50 50)"
            />
          </svg>
          <div
            ref={orbRef}
            className={`viriditas-widget__orb${loading ? ' viriditas-widget__orb--loading' : ''}`}
            aria-hidden="true"
          >
            <span className="viriditas-widget__icon">
              {error ? '\uD83D\uDED1' : loading ? '\u25EF' : TIER_ICONS[tier]}
            </span>
          </div>
        </div>

        {/* ── Score + tier label ——————————————————————————— */}
        <div className="viriditas-widget__labels">
          <span className="viriditas-widget__score">
            {loading ? '\u2014' : error ? 'offline' : Math.round(score)}
          </span>
          <span className="viriditas-widget__tier-label">
            {error ? 'Unavailable' : TIER_LABELS[tier]}
          </span>
        </div>

        {/* ── Footer buttons ——————————————————————————————— */}
        <div className="viriditas-widget__footer">
          <button
            className="viriditas-widget__expand"
            onClick={() => setPanelOpen(v => !v)}
            aria-expanded={panelOpen}
            aria-label={panelOpen ? 'Close alignment detail' : 'Open alignment detail'}
            title="Alignment detail"
          >
            {panelOpen ? '\u2039' : '\u203a'}
          </button>
          <button
            className="viriditas-widget__refresh"
            onClick={refresh}
            disabled={loading}
            aria-label="Refresh alignment"
            title="Refresh alignment"
          >
            \u21bb
          </button>
        </div>

      </div>

      {/* ViritasPanel rendered as sibling so it escapes the rail clip */}
      <ViritasPanel
        open={panelOpen}
        onClose={() => setPanelOpen(false)}
        state={state ?? null}
        history={history}
      />
    </>
  );
};

export default ViritasWidget;
