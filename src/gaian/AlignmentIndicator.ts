/**
 * AlignmentIndicator.ts — Viriditas UI Layer (Issue #68)
 *
 * Renders a small, always-visible ambient pill in the bottom-right corner
 * of the screen showing the live Schumann alignment score.  The pill
 * contains:
 *   • An SVG arc whose fill angle tracks the alignment score (0–1)
 *   • A numeric score (e.g. "0.72")
 *   • A coloured dot reflecting the disturbance_level
 *
 * Tapping the pill reveals a <details> tooltip with:
 *   fundamental_hz, geomagnetic_activity, confidence, last updated.
 *
 * Hidden entirely when confidence < 0.4 (advisory-only mode) or when
 * the sidecar has never responded.
 *
 * The element is appended to document.body (not the gaian-home container)
 * so it survives view transitions and stays above all other layers.
 */

import type { AlignmentState } from './ViriditasTheme';

const SVG_NS = 'http://www.w3.org/2000/svg';

/** Radius of the arc inside the 18×18 SVG viewport. */
const ARC_R = 7;
const ARC_CX = 9;
const ARC_CY = 9;

/** Build an SVG arc path for a normalised value in [0, 1]. */
function buildArcPath(value: number): string {
  const v = Math.max(0, Math.min(1, value));
  if (v >= 0.9999) {
    // Full circle — two arcs to avoid degenerate SVG
    return [
      `M ${ARC_CX} ${ARC_CY - ARC_R}`,
      `A ${ARC_R} ${ARC_R} 0 1 1 ${ARC_CX - 0.001} ${ARC_CY - ARC_R}`,
      'Z',
    ].join(' ');
  }
  const angle   = v * 2 * Math.PI;
  const startX  = ARC_CX;
  const startY  = ARC_CY - ARC_R;
  const endX    = ARC_CX + ARC_R * Math.sin(angle);
  const endY    = ARC_CY - ARC_R * Math.cos(angle);
  const large   = angle > Math.PI ? 1 : 0;
  return [
    `M ${startX} ${startY}`,
    `A ${ARC_R} ${ARC_R} 0 ${large} 1 ${endX.toFixed(3)} ${endY.toFixed(3)}`,
  ].join(' ');
}

export class AlignmentIndicator {
  private _root:    HTMLElement;
  private _arc:     SVGPathElement;
  private _score:   HTMLElement;
  private _dot:     HTMLElement;
  private _ttBody:  HTMLElement;
  private _lastState: AlignmentState | null = null;

  constructor() {
    // ── Build DOM ────────────────────────────────────────────────────────
    const details = document.createElement('details');
    details.className = 'viriditas-indicator';
    details.setAttribute('hidden', '');
    details.setAttribute('aria-label', 'Schumann alignment score');

    // Summary — the always-visible pill
    const summary = document.createElement('summary');

    // Arc SVG
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 18 18');
    svg.setAttribute('width', '18');
    svg.setAttribute('height', '18');
    svg.setAttribute('aria-hidden', 'true');
    svg.classList.add('viriditas-indicator__arc');

    // Track circle
    const track = document.createElementNS(SVG_NS, 'circle');
    track.setAttribute('cx', String(ARC_CX));
    track.setAttribute('cy', String(ARC_CY));
    track.setAttribute('r',  String(ARC_R));
    track.setAttribute('fill', 'none');
    track.setAttribute('stroke', 'currentColor');
    track.setAttribute('stroke-opacity', '0.12');
    track.setAttribute('stroke-width', '1.5');
    svg.appendChild(track);

    // Arc fill
    const arc = document.createElementNS(SVG_NS, 'path');
    arc.setAttribute('fill', 'none');
    arc.setAttribute('stroke', 'var(--color-primary, #4f98a3)');
    arc.setAttribute('stroke-width', '1.5');
    arc.setAttribute('stroke-linecap', 'round');
    svg.appendChild(arc);
    this._arc = arc;

    // Score text
    const score = document.createElement('span');
    score.className = 'viriditas-indicator__score';
    score.textContent = '—';
    this._score = score;

    // Disturbance dot
    const dot = document.createElement('span');
    dot.className = 'viriditas-indicator__dot';
    dot.setAttribute('aria-hidden', 'true');
    this._dot = dot;

    summary.appendChild(svg);
    summary.appendChild(score);
    summary.appendChild(dot);
    details.appendChild(summary);

    // Tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'viriditas-indicator__tooltip';
    tooltip.setAttribute('role', 'tooltip');
    tooltip.innerHTML = '<strong>Schumann Alignment</strong>';
    this._ttBody = tooltip;
    details.appendChild(tooltip);

    this._root = details;
    document.body.appendChild(details);
  }

  /**
   * Update the indicator with the latest AlignmentState.
   * Hides when confidence < 0.4 (advisory-only, sidecar data unreliable).
   */
  update(state: AlignmentState): void {
    this._lastState = state;

    if (state.confidence < 0.4) {
      this._root.setAttribute('hidden', '');
      return;
    }

    this._root.removeAttribute('hidden');

    const score = state.alignment_score;
    const dist  = state.disturbance_level ?? 'unavailable';

    // Arc
    this._arc.setAttribute('d', buildArcPath(score));

    // Score label
    this._score.textContent = score.toFixed(2);

    // Disturbance dot via data attribute (CSS handles colour)
    this._root.setAttribute('data-disturbance', dist);

    // Tooltip body
    const updated = new Date(state.timestamp).toLocaleTimeString([], {
      hour:   '2-digit',
      minute: '2-digit',
    });
    this._ttBody.innerHTML = [
      '<strong>Schumann Alignment</strong>',
      `SR Frequency: <b>${state.fundamental_hz.toFixed(2)} Hz</b>`,
      `Geomagnetic:  <b>${(state.geomagnetic_activity * 100).toFixed(0)}%</b>`,
      `Confidence:   <b>${(state.confidence * 100).toFixed(0)}%</b>`,
      `Updated: ${updated}`,
    ].join('<br>');
  }

  /** Force-hide (e.g. during onboarding or Schumann-disabled mode). */
  hide(): void {
    this._root.setAttribute('hidden', '');
  }

  dispose(): void {
    this._root.remove();
  }
}
