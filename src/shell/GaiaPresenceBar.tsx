/**
 * GaiaPresenceBar.tsx — GAIA's Persistent Heartbeat
 *
 * A compact ambient strip that shows GAIA's current mode at all times.
 * Lives in the top bar of GaiaShell, always visible, never intrusive.
 *
 * Modes:
 *   listening  — orb breathes teal + waveform bars animate
 *   thinking   — orb pulses amethyst + quantum dots travel
 *   speaking   — orb glows gold + waveform bars animate faster
 *   resting    — orb breathes softly in amethyst, no activity indicators
 *   offline    — orb dim grey, flat
 *
 * Integration (GaiaShell.tsx):
 *   import { GaiaPresenceBar, useGaiaMode } from './GaiaPresenceBar';
 *
 *   // In ShellMain:
 *   const { mode, setMode } = useGaiaMode();
 *   // Drop into topbar JSX:
 *   <GaiaPresenceBar mode={mode} />
 *
 *   // Wire setMode to your GaiaChat events:
 *   // onUserStartTyping  → setMode('listening')
 *   // onGaiaStartStream  → setMode('thinking')
 *   // onGaiaStartSpeak   → setMode('speaking')
 *   // onStreamComplete   → setMode('resting')
 *
 * Accessibility:
 *   The bar is an aria-live="polite" region. Mode changes announce
 *   themselves to screen readers with a human-readable label.
 *   Visual animation respects prefers-reduced-motion.
 *
 * Tokens consumed (all from src/styles.css):
 *   --color-amethyst, --color-teal, --color-gold, --color-rose
 *   --color-amethyst-glow, --color-teal-glow, --color-text-faint
 *   --color-surface-3, --color-border
 *   --font-body, --font-mono
 *   --text-xs, --space-1/2/3/4
 *   --duration-fast/base/slow
 *   --ease-out, --ease-spring
 *   --radius-full, --radius-sm
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import './GaiaPresenceBar.css';

// ── Mode types ────────────────────────────────────────────────────────────────

export type GaiaMode = 'listening' | 'thinking' | 'speaking' | 'resting' | 'offline';

const MODE_LABELS: Record<GaiaMode, string> = {
  listening: 'Listening',
  thinking:  'Thinking',
  speaking:  'Speaking',
  resting:   'Resting',
  offline:   'Offline',
};

const MODE_ARIA: Record<GaiaMode, string> = {
  listening: 'GAIA is listening',
  thinking:  'GAIA is thinking',
  speaking:  'GAIA is speaking',
  resting:   'GAIA is resting',
  offline:   'GAIA is offline',
};

// ── useGaiaMode — external mode control hook ──────────────────────────────────
//
// Provides a shared mode signal. In a full integration, replace
// local useState with a Zustand slice or Tauri event listener.
//
export function useGaiaMode(initial: GaiaMode = 'resting') {
  const [mode, setModeRaw] = useState<GaiaMode>(initial);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const setMode = useCallback((next: GaiaMode) => {
    setModeRaw(next);
    // Auto-rest after active modes complete
    if (next === 'speaking' || next === 'thinking') {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setModeRaw('resting'), 8000);
    }
  }, []);

  useEffect(() => () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  }, []);

  return { mode, setMode };
}

// ── PresenceOrb ───────────────────────────────────────────────────────────────
//
// The living core — an animated orb whose colour and pulse reflect GAIA's mode.
//
function PresenceOrb({ mode }: { mode: GaiaMode }) {
  return (
    <div
      className="gpb-orb"
      data-mode={mode}
      aria-hidden="true"
    >
      <div className="gpb-orb__core" />
      <div className="gpb-orb__ring gpb-orb__ring--1" />
      <div className="gpb-orb__ring gpb-orb__ring--2" />
    </div>
  );
}

// ── WaveformBars ─────────────────────────────────────────────────────────────
//
// 5 vertical bars that animate like an audio waveform.
// Active during 'listening' and 'speaking' modes.
//
const BAR_COUNT = 5;

function WaveformBars({ active, fast }: { active: boolean; fast: boolean }) {
  return (
    <div
      className={`gpb-wave${
        active ? ' gpb-wave--active' : ''
      }${
        fast ? ' gpb-wave--fast' : ''
      }`}
      aria-hidden="true"
    >
      {Array.from({ length: BAR_COUNT }, (_, i) => (
        <div key={i} className="gpb-wave__bar" style={{ '--bar-i': i } as React.CSSProperties} />
      ))}
    </div>
  );
}

// ── QuantumDots ───────────────────────────────────────────────────────────────
//
// 4 dots that travel as a quantum wave — active during 'thinking'.
//
const DOT_COUNT = 4;

function QuantumDots({ active }: { active: boolean }) {
  return (
    <div className={`gpb-qdots${active ? ' gpb-qdots--active' : ''}`} aria-hidden="true">
      {Array.from({ length: DOT_COUNT }, (_, i) => (
        <div key={i} className="gpb-qdot" style={{ '--dot-i': i } as React.CSSProperties} />
      ))}
    </div>
  );
}

// ── GaiaPresenceBar ───────────────────────────────────────────────────────────

export interface GaiaPresenceBarProps {
  mode?: GaiaMode;
  /** Called when the user clicks the bar — useful for opening a mode details panel */
  onClick?: () => void;
  /** Additional CSS class */
  className?: string;
}

export function GaiaPresenceBar({
  mode = 'resting',
  onClick,
  className = '',
}: GaiaPresenceBarProps) {
  // Collapse to orb-only after 8s of inactivity
  const [collapsed, setCollapsed]   = useState(false);
  const [prevMode,  setPrevMode]    = useState<GaiaMode>(mode);
  const collapseTimerRef            = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reducedMotion               =
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;

  // Expand on mode change, re-collapse after idle
  useEffect(() => {
    if (mode !== prevMode) {
      setCollapsed(false);
      setPrevMode(mode);
    }

    if (collapseTimerRef.current) clearTimeout(collapseTimerRef.current);

    // Only collapse in resting/offline mode
    if (mode === 'resting' || mode === 'offline') {
      collapseTimerRef.current = setTimeout(
        () => setCollapsed(true),
        reducedMotion ? 200 : 8000,
      );
    }

    return () => {
      if (collapseTimerRef.current) clearTimeout(collapseTimerRef.current);
    };
  }, [mode, prevMode, reducedMotion]);

  // Expand on hover
  const handleMouseEnter = () => {
    if (collapseTimerRef.current) clearTimeout(collapseTimerRef.current);
    setCollapsed(false);
  };
  const handleMouseLeave = () => {
    if (mode === 'resting' || mode === 'offline') {
      collapseTimerRef.current = setTimeout(
        () => setCollapsed(true),
        reducedMotion ? 200 : 3000,
      );
    }
  };

  const showWave  = mode === 'listening' || mode === 'speaking';
  const showDots  = mode === 'thinking';
  const fastWave  = mode === 'speaking';

  return (
    <div
      className={`gpb${
        collapsed ? ' gpb--collapsed' : ''
      } gpb--mode-${mode} ${className}`.trim()}
      role="status"
      aria-live="polite"
      aria-label={MODE_ARIA[mode]}
      aria-atomic="true"
      onClick={onClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      title={`GAIA · ${MODE_LABELS[mode]}`}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {/* Orb — always visible, even when collapsed */}
      <PresenceOrb mode={mode} />

      {/* Expandable content — hidden when collapsed */}
      <div className="gpb__content" aria-hidden={collapsed}>
        {/* Waveform (listening / speaking) */}
        <WaveformBars active={showWave} fast={fastWave} />

        {/* Quantum dots (thinking) */}
        <QuantumDots active={showDots} />

        {/* Mode label */}
        <span className="gpb__label">{MODE_LABELS[mode]}</span>
      </div>

      {/* Screen-reader only live text */}
      <span className="sr-only">{MODE_ARIA[mode]}</span>
    </div>
  );
}

export default GaiaPresenceBar;
