import React from 'react';
import type { GaiaState } from '../shared/gaia-state';

interface Props {
  state: GaiaState | null;
  activeTalismanCount: number;
  loading?: boolean;
  error?: string | null;
}

function metricClass(value: number, invert = false): string {
  if (!invert) {
    if (value >= 0.7) return 'gaia-good';
    if (value >= 0.4) return 'gaia-medium';
    return 'gaia-low';
  }
  if (value <= 0.3) return 'gaia-good';
  if (value <= 0.6) return 'gaia-medium';
  return 'gaia-low';
}

export function GaiaStateHUD({ state, activeTalismanCount, loading, error }: Props) {
  if (loading) {
    return <section className="gaia-hud"><div className="gaia-hud__title">GAIAState</div><div>Loading state…</div></section>;
  }

  if (error) {
    return <section className="gaia-hud"><div className="gaia-hud__title">GAIAState</div><div className="gaia-error">{error}</div></section>;
  }

  if (!state) return null;

  return (
    <section className="gaia-hud">
      <div className="gaia-hud__header">
        <div>
          <div className="gaia-hud__title">GAIAState</div>
          <div className={`gaia-mode gaia-mode--${state.system_state}`}>{state.system_state}</div>
        </div>
        <div className="gaia-flags">
          <span className={state.high_risk_allowed ? 'flag-on' : 'flag-off'}>High-Risk {state.high_risk_allowed ? 'On' : 'Off'}</span>
          <span className={state.canon_write_allowed ? 'flag-on' : 'flag-off'}>Canon {state.canon_write_allowed ? 'Writable' : 'Locked'}</span>
        </div>
      </div>

      <div className="gaia-metrics">
        <div className={`gaia-metric ${metricClass(state.coherence)}`}><label>Coherence</label><strong>{state.coherence.toFixed(2)}</strong></div>
        <div className={`gaia-metric ${metricClass(state.energy)}`}><label>Energy</label><strong>{state.energy.toFixed(2)}</strong></div>
        <div className={`gaia-metric ${metricClass(state.stress, true)}`}><label>Stress</label><strong>{state.stress.toFixed(2)}</strong></div>
        <div className={`gaia-metric ${metricClass(state.entropy, true)}`}><label>Entropy</label><strong>{state.entropy.toFixed(2)}</strong></div>
      </div>

      <div className="gaia-submetrics">
        <span>Personal {state.personal_coherence.toFixed(2)}</span>
        <span>Planetary {state.planetary_coherence.toFixed(2)}</span>
        <span>Talismans {activeTalismanCount}</span>
      </div>
    </section>
  );
}
