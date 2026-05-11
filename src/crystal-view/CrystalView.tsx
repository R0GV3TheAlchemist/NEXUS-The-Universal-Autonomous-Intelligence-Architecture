/**
 * src/crystal-view/CrystalView.tsx
 * GAIA-OS — Crystal View
 * Spec: C-CC01 §11.2
 *
 * The opt-in inner-state view. Opened by:
 *   (a) Long-pressing the GaianOrb for 1.5 s
 *   (b) Navigating to /crystal route
 *
 * Dismissed by:
 *   (a) Swipe down
 *   (b) Tap the ✕ button
 *   (c) Pressing Escape
 *
 * Design principle: felt coherence, not audited performance.
 * No numbers. No tooltips. No export. Just GAIA's inner state, visible.
 */

import React, { useEffect, useCallback, useRef } from 'react';
import { CoherenceRing }   from './CoherenceRing';
import { StreamBars }      from './StreamBars';
import { TrendArc }        from './TrendArc';
import { useCrystalState } from './useCrystalState';
import { BAND_LABELS }     from './types';
import './crystal-view.css';

interface CrystalViewProps {
  onClose: () => void;
}

// ── Skeleton ────────────────────────────────────────────────────────────────

const CrystalViewSkeleton: React.FC = () => (
  <div className="crystal-view crystal-view--loading" aria-busy="true">
    <div className="cv-ring-area">
      <div className="skeleton skeleton-ring" />
    </div>
    <div className="cv-narrative">
      <div className="skeleton skeleton-text" style={{ width: '70%', margin: '0 auto' }} />
    </div>
    <div className="cv-streams">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="skeleton skeleton-bar" />
      ))}
    </div>
  </div>
);

// ── Main ────────────────────────────────────────────────────────────────────

export const CrystalView: React.FC<CrystalViewProps> = ({ onClose }) => {
  const { state, history, loading, error, lastTick } = useCrystalState();
  const overlayRef = useRef<HTMLDivElement>(null);

  // ── Keyboard dismiss ──────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  // ── Swipe-down dismiss ────────────────────────────────────────────
  const touchStartY = useRef<number | null>(null);

  const handleTouchStart = useCallback((e: React.TouchEvent): void => {
    touchStartY.current = e.touches[0].clientY;
  }, []);

  const handleTouchEnd = useCallback((e: React.TouchEvent): void => {
    if (touchStartY.current === null) return;
    const delta = e.changedTouches[0].clientY - touchStartY.current;
    if (delta > 60) onClose();
    touchStartY.current = null;
  }, [onClose]);

  // ── Overlay backdrop click ────────────────────────────────────────
  const handleBackdropClick = useCallback((e: React.MouseEvent): void => {
    if (e.target === overlayRef.current) onClose();
  }, [onClose]);

  // ── Tick time label ───────────────────────────────────────────────
  const tickLabel = lastTick
    ? `Updated ${lastTick.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    : '';

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div
      ref={overlayRef}
      className="crystal-view-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="GAIA inner state"
      onClick={handleBackdropClick}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      <div
        className="crystal-view"
        role="presentation"
        onClick={e => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          className="cv-close"
          onClick={onClose}
          aria-label="Close Crystal View"
        >
          ✕
        </button>

        {loading ? (
          <CrystalViewSkeleton />
        ) : (
          <>
            {/* Error banner — non-blocking */}
            {error && (
              <div className="cv-error" role="status">
                Crystal Core offline — showing last known state
              </div>
            )}

            {/* Ring + Trend arc stacked in same cell */}
            <div className="cv-ring-area" aria-label="Coherence visualisation">
              <TrendArc
                history={history}
                size={320}
                arcRadius={148}
              />
              <CoherenceRing
                coherence={state.coherence}
                band={state.coherence_band}
                size={280}
                stroke={3}
              />
              {/* Band label beneath ring */}
              <div className="cv-band-label">
                {BAND_LABELS[state.coherence_band]}
              </div>
            </div>

            {/* Inner narrative */}
            <div className="cv-narrative" aria-live="polite">
              <p className="cv-narrative__text">
                {state.inner_narrative}
              </p>
            </div>

            {/* Stream bars */}
            <div className="cv-streams">
              <StreamBars state={state} />
            </div>

            {/* Footer */}
            <div className="cv-footer">
              <span className="cv-footer__tick">{tickLabel}</span>
              <span className="cv-footer__hint">swipe down to close</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default CrystalView;
