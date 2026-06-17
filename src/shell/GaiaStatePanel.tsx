/**
 * GaiaStatePanel.tsx
 *
 * Collapsible right-rail panel that surfaces GAIAState HUD + Talisman
 * management inside the existing GaiaShell layout without modifying
 * GaiaShell.tsx itself.
 *
 * Mount this ONCE in ShellMain (or the top-level shell layout) just
 * before the closing tag of the root shell container.
 *
 * Usage:
 *   import { GaiaStatePanel } from './GaiaStatePanel';
 *   // inside your JSX:
 *   <GaiaStatePanel />
 */

import React, { useState } from 'react';
import { GaiaStateHUD } from '../components/GaiaStateHUD';
import { TalismanPanel } from '../components/TalismanPanel';
import { useGaiaState } from '../hooks/useGaiaState';
import '../styles/gaia-state.css';
import './GaiaStatePanel.css';

export function GaiaStatePanel() {
  const { state, talismans, activeTalismans, loading, error, refresh } = useGaiaState(30_000);
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Toggle button — always visible in bottom-right corner */}
      <button
        className={`gaia-state-toggle ${open ? 'gaia-state-toggle--open' : ''}`}
        onClick={() => setOpen((v) => !v)}
        title="Toggle GAIA State"
        aria-label="Toggle GAIA State panel"
      >
        <span className="gaia-state-toggle__icon">⬡</span>
        {activeTalismans.length > 0 && (
          <span className="gaia-state-toggle__badge">{activeTalismans.length}</span>
        )}
      </button>

      {/* Slide-in panel */}
      {open && (
        <aside className="gaia-state-panel" role="complementary" aria-label="GAIA State">
          <GaiaStateHUD
            state={state}
            activeTalismanCount={activeTalismans.length}
            loading={loading}
            error={error}
          />
          <div className="gaia-state-panel__divider" />
          <TalismanPanel talismans={talismans} onRefresh={refresh} />
        </aside>
      )}
    </>
  );
}
