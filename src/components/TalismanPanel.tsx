import React, { useState } from 'react';
import type { Talisman } from '../shared/gaia-state';

interface Props {
  talismans: Talisman[];
  onRefresh: () => Promise<void> | void;
}

export function TalismanPanel({ talismans, onRefresh }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const invoke = async (id: string, action: 'activate' | 'deactivate') => {
    try {
      setBusyId(id);
      setError(null);
      const res = await fetch(`/gaia/talismans/${id}/${action}`, { method: 'POST' });
      if (!res.ok) throw new Error(`${action} failed: ${res.status}`);
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown talisman error');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="talisman-panel">
      <div className="talisman-panel__title">Talismans</div>
      {error ? <div className="gaia-error">{error}</div> : null}
      <div className="talisman-list">
        {talismans.map((t) => {
          const active = t.status === 'active';
          return (
            <article key={t.id} className={`talisman-card ${active ? 'talisman-card--active' : ''}`}>
              <div className="talisman-card__header">
                <div>
                  <h3>{t.name}</h3>
                  <p>{t.purpose}</p>
                </div>
                <span className={`talisman-status talisman-status--${t.status}`}>{t.status}</span>
              </div>
              <div className="talisman-effects">
                <span>+C {t.effect.coherence_delta.toFixed(2)}</span>
                <span>+E {t.effect.energy_delta.toFixed(2)}</span>
                <span>S {t.effect.stress_delta.toFixed(2)}</span>
                <span>H {t.effect.entropy_delta.toFixed(2)}</span>
              </div>
              <div className="talisman-card__footer">
                <small>{t.notes}</small>
                <button disabled={busyId === t.id} onClick={() => invoke(t.id, active ? 'deactivate' : 'activate')}>
                  {busyId === t.id ? 'Working…' : active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
