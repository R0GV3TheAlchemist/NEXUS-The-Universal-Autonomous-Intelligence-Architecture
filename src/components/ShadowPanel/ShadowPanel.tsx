/**
 * src/components/ShadowPanel/ShadowPanel.tsx
 * GAIA-OS — Shadow Archetype Panel
 *
 * Visualises the Shadow Engine state for one principal.
 * Designed to drop into any panel grid — provides its own sizing.
 *
 * Usage:
 *   <ShadowPanel principalId="user_abc" />
 *
 * Optional props:
 *   pollMs           — live-refresh interval (default: none)
 *   onArchetypeClick — called with archetype name on bar click (e.g. open detail drawer)
 *
 * When onArchetypeClick is omitted the panel manages its own ArchetypeDrawer
 *   internally so it works standalone with zero wiring in the parent.
 *
 * ReflectDialog is always managed internally — it is not a concern of the parent.
 *
 * Canon: Shadow Engine — 7-Archetype Integration Layer
 */

import React, { useCallback, useState } from 'react';
import { useShadow } from '../../hooks/useShadow';
import {
  type ShadowArchetypeName,
  ALL_SHADOW_ARCHETYPES,
  ACTIVATION_THRESHOLD,
} from '../../shared/shadowTypes';
import { ArchetypeDrawer } from './ArchetypeDrawer';
import { ReflectDialog }  from './ReflectDialog';
import './shadow-panel.css';

// ── Archetype metadata ─────────────────────────────────────────────────────

const ARCHETYPE_GLYPHS: Record<ShadowArchetypeName, string> = {
  Orphan:    '◯',
  Warrior:   '⚔',
  Wanderer:  '↯',
  Caregiver: '❧',
  Seeker:    '◎',
  Destroyer: '⬙',
  Creator:   '✶',
};

const ARCHETYPE_HUES: Record<ShadowArchetypeName, string> = {
  Orphan:    '#7c9ef5',
  Warrior:   '#f55c5c',
  Wanderer:  '#f5c842',
  Caregiver: '#5cf592',
  Seeker:    '#42e8d5',
  Destroyer: '#e07b39',
  Creator:   '#b28aff',
};

const INTENSITY_LABELS: Record<string, string> = {
  dormant:   'Dormant',
  stirring:  'Stirring',
  active:    'Active',
  dominant:  'Dominant',
  consuming: 'Consuming',
};

const STAGE_DESCRIPTIONS: Record<string, string> = {
  unmet:       'Shadow unmet — no reflection begun',
  awareness:   'Awareness — patterns recognised',
  engagement:  'Engagement — actively working with shadow',
  embodiment:  'Embodiment — integrating into self',
  integrated:  'Integrated — shadow becomes ally',
};

// ── Sub-components ───────────────────────────────────────────────────────

interface ArchetypeBarProps {
  name:       ShadowArchetypeName;
  score:      number;
  isDominant: boolean;
  onClick?:   (name: ShadowArchetypeName) => void;
}

function ArchetypeBar({ name, score, isDominant, onClick }: ArchetypeBarProps) {
  const pct   = Math.round(score * 100);
  const color = ARCHETYPE_HUES[name];
  const glyph = ARCHETYPE_GLYPHS[name];

  return (
    <li
      className={`shadow-panel__archetype-row${
        isDominant ? ' shadow-panel__archetype-row--dominant' : ''
      }${onClick ? ' shadow-panel__archetype-row--clickable' : ''}`}
      style={{ '--sp-hue': color } as React.CSSProperties}
      onClick={() => onClick?.(name)}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick(name);
        }
      }}
      aria-label={`${name}: ${pct}%${
        isDominant ? ' — dominant archetype' : ''
      }${onClick ? '. Press to view details.' : ''}`}
    >
      <span className="shadow-panel__archetype-glyph" aria-hidden>{glyph}</span>
      <span className="shadow-panel__archetype-name">{name}</span>
      <div className="shadow-panel__bar-track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div
          className="shadow-panel__bar-fill"
          style={{ '--sp-pct': `${pct}%` } as React.CSSProperties}
        />
        {score >= ACTIVATION_THRESHOLD && (
          <span className="shadow-panel__bar-threshold" aria-hidden title="Activation threshold" />
        )}
      </div>
      <span className="shadow-panel__archetype-score">{pct}%</span>
      {onClick && (
        <span className="shadow-panel__archetype-chevron" aria-hidden>›</span>
      )}
    </li>
  );
}

function SkeletonLoader() {
  return (
    <div className="shadow-panel shadow-panel--skeleton" aria-busy aria-label="Loading shadow data">
      <div className="shadow-panel__header">
        <div className="skeleton shadow-panel__skel-title" />
        <div className="skeleton shadow-panel__skel-badge" />
      </div>
      <ul className="shadow-panel__archetype-list">
        {ALL_SHADOW_ARCHETYPES.map((a) => (
          <li key={a} className="shadow-panel__archetype-row">
            <span className="shadow-panel__archetype-glyph" style={{ opacity: 0.3 }}>
              {ARCHETYPE_GLYPHS[a]}
            </span>
            <span className="skeleton shadow-panel__skel-name" />
            <div className="shadow-panel__bar-track">
              <div className="skeleton" style={{ width: '100%', height: '100%', borderRadius: 'var(--radius-sm)' }} />
            </div>
            <span className="skeleton shadow-panel__skel-score" />
          </li>
        ))}
      </ul>
      <div className="shadow-panel__integration">
        <div className="skeleton shadow-panel__skel-integration-bar" />
      </div>
    </div>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────

export interface ShadowPanelProps {
  principalId:       string;
  pollMs?:           number;
  onArchetypeClick?: (name: ShadowArchetypeName) => void;
}

// ── Component ────────────────────────────────────────────────────────────

export function ShadowPanel({
  principalId,
  pollMs,
  onArchetypeClick,
}: ShadowPanelProps) {
  const shadow = useShadow(principalId, { pollMs });

  // ── Drawer state (self-managed when parent has not taken control) ────────
  const [internalSelected, setInternalSelected] = useState<ShadowArchetypeName | null>(null);
  const isExternallyControlled = Boolean(onArchetypeClick);

  const handleBarClick = useCallback(
    (name: ShadowArchetypeName) => {
      if (isExternallyControlled) onArchetypeClick!(name);
      else setInternalSelected(name);
    },
    [isExternallyControlled, onArchetypeClick],
  );

  // ── Reflect dialog state (always internal — parent never owns this) ─────
  const [reflectOpen, setReflectOpen] = useState(false);

  // ── Loading ────────────────────────────────────────────────────────

  if (shadow.loading && !shadow.record) return <SkeletonLoader />;

  // ── Empty state ───────────────────────────────────────────────────

  if (!shadow.record && !shadow.error) {
    return (
      <div className="shadow-panel shadow-panel--empty">
        <div className="shadow-panel__empty-glyph" aria-hidden>◯</div>
        <h3 className="shadow-panel__empty-title">Shadow not yet mapped</h3>
        <p className="shadow-panel__empty-body">
          Run an evaluation to reveal the archetype pattern underlying your current state.
        </p>
        <button
          className="shadow-panel__evaluate-btn"
          onClick={() => shadow.evaluate()}
          disabled={shadow.loading}
        >
          {shadow.loading ? 'Evaluating…' : 'Begin Shadow Evaluation'}
        </button>
      </div>
    );
  }

  // ── Main render ─────────────────────────────────────────────────────

  const {
    record,
    isActivated,
    intensityLevel,
    integrationStage,
    dominantArchetype,
    scores,
    intensityPct,
    integrationPct,
    error,
  } = shadow;

  const dominantColor = dominantArchetype
    ? ARCHETYPE_HUES[dominantArchetype]
    : 'var(--color-text-faint)';

  return (
    <>
      <section
        className="shadow-panel"
        data-level={intensityLevel}
        data-activated={isActivated ? 'true' : 'false'}
        style={{ '--sp-dominant': dominantColor } as React.CSSProperties}
        aria-label="Shadow Archetype Panel"
      >

        {/* ── Error banner ── */}
        {error && (
          <div className="shadow-panel__error-banner" role="alert">
            <span>⚠ {error}</span>
            <button
              className="shadow-panel__error-dismiss"
              onClick={shadow.clearError}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        {/* ── Header ── */}
        <header className="shadow-panel__header">
          <div className="shadow-panel__identity">
            <span
              className="shadow-panel__dominant-glyph"
              style={{ color: dominantColor }}
              aria-hidden
            >
              {dominantArchetype ? ARCHETYPE_GLYPHS[dominantArchetype] : '◯'}
            </span>
            <div className="shadow-panel__title-group">
              <h3 className="shadow-panel__title">
                {dominantArchetype ?? 'No Dominant Archetype'}
              </h3>
              <span className="shadow-panel__subtitle" aria-label="Principal ID">
                {principalId}
              </span>
            </div>
          </div>

          <div className="shadow-panel__badges">
            <span
              className={`shadow-panel__intensity-badge shadow-panel__intensity-badge--${intensityLevel}`}
              title={`Shadow intensity: ${intensityPct}%`}
            >
              {INTENSITY_LABELS[intensityLevel]}
            </span>
            {isActivated && (
              <span className="shadow-panel__activated-badge" title="Activation threshold exceeded">
                ▲ Active
              </span>
            )}
          </div>
        </header>

        {/* ── Intensity track ── */}
        <div className="shadow-panel__intensity-track-row">
          <span className="shadow-panel__track-label">Intensity</span>
          <div
            className="shadow-panel__intensity-track"
            role="progressbar"
            aria-label="Shadow intensity"
            aria-valuenow={intensityPct}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="shadow-panel__intensity-fill"
              style={{ '--sp-pct': `${intensityPct}%` } as React.CSSProperties}
            />
            <span
              className="shadow-panel__threshold-marker"
              style={{ left: `${ACTIVATION_THRESHOLD * 100}%` }}
              title="Activation threshold (35%)"
              aria-hidden
            />
          </div>
          <span className="shadow-panel__track-value">{intensityPct}%</span>
        </div>

        {/* ── Archetype score bars ── */}
        <ul className="shadow-panel__archetype-list" aria-label="Archetype scores">
          {ALL_SHADOW_ARCHETYPES.map((name) => (
            <ArchetypeBar
              key={name}
              name={name}
              score={scores?.[name] ?? 0}
              isDominant={name === dominantArchetype}
              onClick={handleBarClick}
            />
          ))}
        </ul>

        {/* ── Integration progress ── */}
        <div className="shadow-panel__integration">
          <div className="shadow-panel__integration-header">
            <span className="shadow-panel__track-label">Integration</span>
            <span className="shadow-panel__integration-stage">
              {STAGE_DESCRIPTIONS[integrationStage]}
            </span>
            <span className="shadow-panel__track-value">{integrationPct}%</span>
          </div>
          <div
            className="shadow-panel__integration-track"
            role="progressbar"
            aria-label="Integration progress"
            aria-valuenow={integrationPct}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className="shadow-panel__integration-fill"
              style={{ '--sp-pct': `${integrationPct}%` } as React.CSSProperties}
            />
            {[20, 45, 70, 90].map((pct) => (
              <span
                key={pct}
                className="shadow-panel__milestone-marker"
                style={{ left: `${pct}%` }}
                aria-hidden
              />
            ))}
          </div>
        </div>

        {/* ── Metadata row ── */}
        {record && (
          <div className="shadow-panel__meta">
            <span className="shadow-panel__meta-item">
              {record.days_active} day{record.days_active !== 1 ? 's' : ''} active
            </span>
            {record.recorded_at && (
              <span className="shadow-panel__meta-item shadow-panel__meta-item--right">
                Updated {new Date(record.recorded_at).toLocaleTimeString([], {
                  hour: '2-digit', minute: '2-digit',
                })}
              </span>
            )}
          </div>
        )}

        {/* ── Actions ── */}
        <div className="shadow-panel__actions">
          {/* Reflect now opens the confirmation dialog instead of firing directly */}
          <button
            className="shadow-panel__reflect-btn"
            onClick={() => setReflectOpen(true)}
            disabled={shadow.loading || !record}
            title="Record a reflection session (+5% integration)"
          >
            ◎&ensp;Reflect
          </button>
          <button
            className="shadow-panel__evaluate-btn shadow-panel__evaluate-btn--secondary"
            onClick={() => shadow.evaluate()}
            disabled={shadow.loading}
            title="Re-run full archetype evaluation"
          >
            {shadow.loading ? '⋯' : '⟳ Evaluate'}
          </button>
        </div>

      </section>

      {/* ── ArchetypeDrawer (self-managed when parent has not taken control) ── */}
      {!isExternallyControlled && (
        <ArchetypeDrawer
          archetype={internalSelected}
          record={record ?? null}
          onClose={() => setInternalSelected(null)}
        />
      )}

      {/* ── ReflectDialog (always internal) ── */}
      <ReflectDialog
        open={reflectOpen}
        integrationPct={integrationPct}
        dominantArchetype={dominantArchetype}
        onConfirm={shadow.reflect}
        onClose={() => setReflectOpen(false)}
      />
    </>
  );
}

export default ShadowPanel;
