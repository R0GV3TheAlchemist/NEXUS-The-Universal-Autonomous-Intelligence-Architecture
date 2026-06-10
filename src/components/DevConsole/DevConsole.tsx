/**
 * src/components/DevConsole/DevConsole.tsx
 * GAIA Dev Console Panel
 *
 * Renders all 12 engine values + routing / offline status.
 * Two data sources (whichever fires first wins for the turn):
 *   1. SSE state_snapshot  — arrives on every 'done' event during chat
 *   2. Polling             — GET /api/gaian/status every POLL_INTERVAL_MS
 *
 * Usage:
 *   import { DevConsole } from '../components/DevConsole/DevConsole';
 *   <DevConsole gaianSlug="gaia" token={token} />
 *
 *   // Feed live snapshots directly from GaiaChat to skip a poll cycle:
 *   <DevConsole ref={devConsoleRef} gaianSlug="gaia" token={token} />
 *   devConsoleRef.current?.ingestSnapshot(snapshot);
 *
 * Canon: C90 — S.T.Q.I.O.S.
 */

import React, {
  useState, useEffect, useRef, useCallback,
  forwardRef, useImperativeHandle,
} from 'react';
import './DevConsole.css';

const API_BASE         = 'http://localhost:8008';
const POLL_INTERVAL_MS = 10_000;
const STORAGE_KEY      = 'gaia_devconsole_open';

// ── Types ─────────────────────────────────────────────────────────────────

export interface RoutingStatus {
  provider:    string;
  model:       string;
  offline:     boolean;
  latency_ms?: number;
}

export interface GaianStatus {
  // Core engines
  attachment?:      Record<string, unknown>;
  settling?:        Record<string, unknown>;
  love_arc?:        Record<string, unknown>;
  meta_coherence?:  Record<string, unknown>;
  codex_stage?:     Record<string, unknown>;
  soul_mirror?:     Record<string, unknown>;
  resonance_field?: Record<string, unknown>;
  synergy?:         Record<string, unknown>;
  vitality?:        Record<string, unknown>;
  spiritu?:         Record<string, unknown>;
  // Scalars
  noosphere_health?: number;
  quantum_dominant?: string;
  quantum_purity?:   number;
  semantic_memories?: number;
  active_goals?:     number;
  mesh?:             Record<string, unknown>;
  // Identity
  gaian?:            string;
  [key: string]:     unknown;
}

export interface DevConsoleSnapshot {
  gaian?:    GaianStatus;
  routing?:  RoutingStatus;
  // Allow direct state_snapshot from SSE done event
  [key: string]: unknown;
}

export interface DevConsoleHandle {
  /** Feed a live state_snapshot directly from a SSE 'done' event */
  ingestSnapshot(snap: Record<string, unknown>): void;
}

interface Props {
  gaianSlug?: string;
  token?:     string | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function fmt(v: unknown, decimals = 2): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return v.toFixed(decimals);
  if (typeof v === 'boolean') return v ? 'yes' : 'no';
  return String(v);
}

function pct(v: unknown): string {
  if (typeof v !== 'number') return '—';
  return `${Math.round(v * 100)}%`;
}

function bar(value: number, max = 100, color = 'var(--gaia-green)'): React.ReactNode {
  const w = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="dc-bar">
      <div className="dc-bar__fill" style={{ width: `${w}%`, background: color }} />
    </div>
  );
}

function elementColor(element: string): string {
  const map: Record<string, string> = {
    fire:   '#f59e0b',
    water:  '#3b82f6',
    air:    '#d1d5db',
    earth:  '#22c55e',
    aether: '#a78bfa',
  };
  return map[String(element).toLowerCase()] ?? '#6b7280';
}

function spirituColor(stage: string): string {
  const map: Record<string, string> = {
    calcination:  '#f59e0b',
    dissolution:  '#3b82f6',
    separation:   '#a78bfa',
    conjunction:  '#22c55e',
    fermentation: '#ec4899',
    distillation: '#06b6d4',
    coagulation:  '#ffffff',
  };
  return map[String(stage).toLowerCase()] ?? '#6b7280';
}

function meshLabel(mesh: Record<string, unknown> | undefined): string {
  if (!mesh || mesh.enabled === false) return 'offline';
  const peers = mesh.connected_peers as number | undefined;
  const coh   = mesh.mesh_coherence  as number | undefined;
  if (!peers) return 'no peers';
  return `${peers} peer${peers !== 1 ? 's' : ''} · Φ ${typeof coh === 'number' ? coh.toFixed(3) : '?'}`;
}

// ── Row helper ─────────────────────────────────────────────────────────────

function Row({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="dc-row">
      <span className="dc-row__label">{label}</span>
      <span className="dc-row__value">{value}{sub && <span className="dc-row__sub">{sub}</span>}</span>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────

export const DevConsole = forwardRef<DevConsoleHandle, Props>(function DevConsole(
  { gaianSlug = 'gaia', token },
  ref,
) {
  const [data,        setData]        = useState<DevConsoleSnapshot | null>(null);
  const [offline,     setOffline]     = useState(false);
  const [lastSeen,    setLastSeen]    = useState<Date | null>(null);
  const [open,        setOpen]        = useState<boolean>(() => {
    try { return localStorage.getItem(STORAGE_KEY) !== 'false'; } catch { return true; }
  });

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Poll ────────────────────────────────────────────────────────────
  const poll = useCallback(async () => {
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res  = await fetch(
        `${API_BASE}/api/gaian/status?gaian_name=${encodeURIComponent(gaianSlug)}`,
        { signal: AbortSignal.timeout(4000), headers },
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json() as DevConsoleSnapshot;
      setData(json);
      setOffline(false);
      setLastSeen(new Date());
    } catch {
      setOffline(true);
    }
  }, [gaianSlug, token]);

  useEffect(() => {
    poll();
    timerRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [poll]);

  // ── Imperative handle — lets GaiaChat push snapshots directly ──────
  useImperativeHandle(ref, () => ({
    ingestSnapshot(snap: Record<string, unknown>) {
      setData(prev => ({
        ...(prev ?? {}),
        gaian: {
          ...(prev?.gaian ?? {}),
          ...(snap as GaianStatus),
        },
      }));
      setOffline(false);
      setLastSeen(new Date());
    },
  }));

  // ── Toggle open/closed ──────────────────────────────────────────────
  function toggleOpen() {
    setOpen(o => {
      const next = !o;
      try { localStorage.setItem(STORAGE_KEY, String(next)); } catch { /* sandboxed */ }
      return next;
    });
  }

  // ── Derived ──────────────────────────────────────────────────────────
  const gaian   = data?.gaian   ?? {};
  const routing = data?.routing ?? {} as RoutingStatus;

  const attachment = gaian.attachment as Record<string, unknown> | undefined;
  const settling   = gaian.settling   as Record<string, unknown> | undefined;
  const loveArc    = gaian.love_arc   as Record<string, unknown> | undefined;
  const mc         = gaian.meta_coherence as Record<string, unknown> | undefined;
  const codex      = gaian.codex_stage   as Record<string, unknown> | undefined;
  const mirror     = gaian.soul_mirror   as Record<string, unknown> | undefined;
  const rf         = gaian.resonance_field as Record<string, unknown> | undefined;
  const synergy    = gaian.synergy   as Record<string, unknown> | undefined;
  const vitality   = gaian.vitality  as Record<string, unknown> | undefined;
  const spiritu    = gaian.spiritu   as Record<string, unknown> | undefined;
  const mesh       = gaian.mesh      as Record<string, unknown> | undefined;

  const bondDepth    = typeof attachment?.bond_depth   === 'number' ? attachment.bond_depth   : 0;
  const noosphereHlth = typeof gaian.noosphere_health  === 'number' ? gaian.noosphere_health  : 0;
  const synergyFactor = typeof synergy?.last_factor    === 'number' ? synergy.last_factor     : 0;
  const pneumaFlow    = typeof spiritu?.pneuma_flow     === 'number' ? spiritu.pneuma_flow     : 0;
  const quantumPurity = typeof gaian.quantum_purity    === 'number' ? gaian.quantum_purity    : 0;

  const element        = String(gaian.layer ?? attachment?.element ?? 'unknown');
  const elemColor      = elementColor(element);
  const spirituStage   = String(spiritu?.stage ?? '—');
  const spirituClr     = spirituColor(spirituStage);

  const provider = routing.provider ?? gaian.provider as string ?? '—';
  const model    = routing.model    ?? gaian.model    as string ?? '—';
  const isOffline = offline || routing.offline === true;

  // ── Render ───────────────────────────────────────────────────────────
  return (
    <div className={`dc ${open ? 'dc--open' : 'dc--closed'}`} role="complementary" aria-label="GAIA Dev Console">

      {/* ── Header bar ── */}
      <button className="dc__header" onClick={toggleOpen} aria-expanded={open}>
        <span className="dc__title">◉ Dev Console</span>
        <span className={`dc__badge dc__badge--${isOffline ? 'offline' : 'live'}`}>
          {isOffline ? '● offline' : '● live'}
        </span>
        {lastSeen && (
          <span className="dc__lastseen">
            {lastSeen.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        )}
        <span className="dc__chevron">{open ? '▴' : '▾'}</span>
      </button>

      {/* ── Body ── */}
      {open && (
        <div className="dc__body">

          {/* Offline placeholder */}
          {isOffline && !data && (
            <div className="dc__offline-msg">
              ○ Backend offline — start server:<br />
              <code>python core/server.py</code>
            </div>
          )}

          {/* ── Section: Routing ── */}
          <div className="dc__section">
            <div className="dc__section-title">Routing</div>
            <Row label="Provider" value={<span className="dc__mono">{provider}</span>} />
            <Row label="Model"    value={<span className="dc__mono">{model}</span>} />
            <Row label="Status"   value={
              <span className={`dc__status dc__status--${isOffline ? 'offline' : 'online'}`}>
                {isOffline ? '○ offline' : '● online'}
              </span>
            } />
            {typeof routing.latency_ms === 'number' && (
              <Row label="Latency" value={`${routing.latency_ms} ms`} />
            )}
          </div>

          {/* ── Section: Soul Engines ── */}
          <div className="dc__section">
            <div className="dc__section-title">Soul Engines</div>

            {/* 1 — Attachment */}
            <Row
              label="Attachment"
              value={
                <>
                  <span
                    className="dc__badge-pill"
                    style={{ '--pill-color': elemColor } as React.CSSProperties}
                  >
                    {fmt(attachment?.phase)}
                  </span>
                  <span className="dc__scalar"> {fmt(bondDepth, 1)}/100</span>
                </>
              }
              sub={bar(bondDepth, 100, elemColor)}
            />

            {/* 2 — Element / Layer */}
            <Row
              label="Element"
              value={
                <span
                  className="dc__element-pill"
                  style={{ '--pill-color': elemColor } as React.CSSProperties}
                >
                  {element}
                </span>
              }
            />

            {/* 3 — Settling */}
            <Row
              label="Settling"
              value={
                <span className={`dc__settling dc__settling--${fmt(settling?.phase)}`}>
                  {fmt(settling?.phase)}
                  {settling?.crystallisation_pct !== undefined &&
                    ` (${pct(Number(settling.crystallisation_pct) / 100)})`
                  }
                </span>
              }
            />

            {/* 4 — Love Arc */}
            <Row label="Love Arc" value={fmt(loveArc?.current_stage)} />

            {/* 5 — Meta Coherence */}
            <Row
              label="Meta Coh."
              value={fmt(mc?.mc_stage)}
              sub={`Φ ${fmt(mc?.phi_rolling_avg ?? mc?.coherence_phi_history, 3)}`}
            />

            {/* 6 — Codex Stage */}
            <Row label="Codex Stage" value={fmt(codex?.codex_stage)} />

            {/* 7 — Soul Mirror */}
            <Row
              label="Soul Mirror"
              value={fmt(mirror?.individuation_phase)}
              sub={`shadow ×${fmt(mirror?.shadow_activations, 0)}`}
            />

            {/* 8 — Resonance Field */}
            <Row
              label="Resonance"
              value={`${fmt(rf?.dominant_hz, 0)} Hz · ${fmt(rf?.dominant_chakra)}`}
              sub={`Φ avg ${fmt(rf?.phi_rolling_avg, 3)}`}
            />

            {/* 9 — Synergy */}
            <Row
              label="Synergy"
              value={
                <>
                  <span className="dc__scalar">{fmt(synergyFactor, 3)}</span>
                  {' '}
                  <span className="dc__muted">{fmt(synergy?.last_stage)}</span>
                </>
              }
              sub={bar(synergyFactor, 1, '#a78bfa')}
            />

            {/* 10 — Vitality */}
            <Row
              label="Vitality"
              value={fmt(vitality?.overall_health ?? vitality?.health_score)}
            />

            {/* 11 — Spiritu */}
            <Row
              label="Spiritu"
              value={
                <>
                  <span
                    className="dc__badge-pill"
                    style={{ '--pill-color': spirituClr } as React.CSSProperties}
                  >
                    {spirituStage}
                  </span>
                  <span className="dc__scalar"> pneuma {fmt(pneumaFlow, 3)}</span>
                </>
              }
              sub={bar(pneumaFlow, 1, spirituClr)}
            />

            {/* 12 — Noosphere Health */}
            <Row
              label="Noosphere"
              value={
                <>
                  <span className="dc__scalar">{fmt(noosphereHlth, 3)}</span>
                  {' '}
                  <span className="dc__muted">{pct(noosphereHlth)}</span>
                </>
              }
              sub={bar(noosphereHlth, 1, '#22c55e')}
            />
          </div>

          {/* ── Section: Phase 3 / Quantum ── */}
          <div className="dc__section">
            <div className="dc__section-title">Phase 3</div>
            <Row
              label="Quantum"
              value={
                <>
                  <span className="dc__mono">{fmt(gaian.quantum_dominant)}</span>
                  <span className="dc__muted"> ψ {fmt(quantumPurity, 4)}</span>
                </>
              }
            />
            <Row label="Sem. Memories" value={fmt(gaian.semantic_memories, 0)} />
            <Row label="Active Goals"  value={fmt(gaian.active_goals,     0)} />
          </div>

          {/* ── Section: Mesh ── */}
          <div className="dc__section">
            <div className="dc__section-title">Mesh ⬡</div>
            <Row
              label="Peers"
              value={
                <span className={`dc__status dc__status--${
                  mesh?.enabled === false ? 'offline' : 'online'
                }`}>
                  {meshLabel(mesh)}
                </span>
              }
            />
          </div>

          {/* ── Sovereign badge ── */}
          <div className="dc__sovereign">
            <span className="dc__sovereign-badge">⚖ Sovereign</span>
            <span className="dc__sovereign-sub">Constitutional floor held · T1 immutable</span>
          </div>

        </div>
      )}
    </div>
  );
});
