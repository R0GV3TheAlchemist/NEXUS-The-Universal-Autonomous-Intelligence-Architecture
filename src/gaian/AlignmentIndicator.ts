/**
 * AlignmentIndicator.ts — Viriditas UI Layer (Issue #68)
 *
 * Renders a small, always-visible ambient pill in the bottom-right corner
 * of the screen showing the live Schumann alignment score.  The pill
 * contains:
 *   • An SVG arc whose fill angle tracks the alignment score (0–1)
 *   • A numeric score (e.g. "0.72")
 *   • A coloured dot reflecting the disturbance_level
 *   • An LCI sparkline canvas (M2, Issue #756) — last N phi values
 *     drawn as a miniature line graph, colour-coded by lci_trend.
 *
 * Tapping the pill reveals a <details> tooltip with:
 *   fundamental_hz, geomagnetic_activity, confidence, last updated,
 *   lci_baseline, lci_trend (M2).
 *
 * Hidden entirely when confidence < 0.4 (advisory-only mode) or when
 * the sidecar has never responded.
 *
 * The element is appended to document.body (not the gaian-home container)
 * so it survives view transitions and stays above all other layers.
 *
 * M2 additions (Issue #756):
 *   setProfile(profile)  — loads lciHistory + lciTrend from GAIANProfile
 *                           and redraws the sparkline.
 *   _drawSparkline()     — internal Canvas 2D renderer for the sparkline.
 */

import type { AlignmentState } from './ViriditasTheme';
import type { GAIANProfile, LCIHistoryEntry } from './GAIANProfile';

const SVG_NS = 'http://www.w3.org/2000/svg';

/** Radius of the arc inside the 18×18 SVG viewport. */
const ARC_R  = 7;
const ARC_CX = 9;
const ARC_CY = 9;

/** Sparkline canvas dimensions (px, logical). */
const SPARK_W = 40;
const SPARK_H = 14;

/** Max history entries rendered in the sparkline. */
const SPARK_MAX_POINTS = 20;

/** Trend → stroke colour. */
const TREND_COLORS: Record<string, string> = {
  rising:   '#4caf50',   // green
  stable:   '#4f98a3',   // teal (primary)
  falling:  '#e57373',   // soft red
  volatile: '#ffb74d',   // amber
};

/** Build an SVG arc path for a normalised value in [0, 1]. */
function buildArcPath(value: number): string {
  const v = Math.max(0, Math.min(1, value));
  if (v >= 0.9999) {
    return [
      `M ${ARC_CX} ${ARC_CY - ARC_R}`,
      `A ${ARC_R} ${ARC_R} 0 1 1 ${ARC_CX - 0.001} ${ARC_CY - ARC_R}`,
      'Z',
    ].join(' ');
  }
  const angle  = v * 2 * Math.PI;
  const startX = ARC_CX;
  const startY = ARC_CY - ARC_R;
  const endX   = ARC_CX + ARC_R * Math.sin(angle);
  const endY   = ARC_CY - ARC_R * Math.cos(angle);
  const large  = angle > Math.PI ? 1 : 0;
  return [
    `M ${startX} ${startY}`,
    `A ${ARC_R} ${ARC_R} 0 ${large} 1 ${endX.toFixed(3)} ${endY.toFixed(3)}`,
  ].join(' ');
}

export class AlignmentIndicator {
  private _root:    HTMLElement;
  private _arc:     SVGPathElement;
  private _score:   HTMLElement;
  private _ttBody:  HTMLElement;

  // M2 — sparkline
  private _sparkCanvas:  HTMLCanvasElement;
  private _sparkCtx:     CanvasRenderingContext2D | null;
  private _lciHistory:   LCIHistoryEntry[] = [];
  private _lciTrend:     string = 'stable';
  private _lciBaseline:  number = 0;

  constructor() {
    // ── Build DOM ──────────────────────────────────────────────────────────
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

    // ── Sparkline canvas (M2) ───────────────────────────────────────────
    const spark = document.createElement('canvas');
    spark.className = 'viriditas-indicator__sparkline';
    spark.width  = SPARK_W * window.devicePixelRatio;
    spark.height = SPARK_H * window.devicePixelRatio;
    spark.style.width  = `${SPARK_W}px`;
    spark.style.height = `${SPARK_H}px`;
    spark.setAttribute('aria-hidden', 'true');
    spark.setAttribute('title', 'LCI history');
    this._sparkCanvas = spark;
    this._sparkCtx    = spark.getContext('2d');
    if (this._sparkCtx) {
      this._sparkCtx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }

    summary.appendChild(svg);
    summary.appendChild(score);
    summary.appendChild(dot);
    summary.appendChild(spark);   // sparkline sits after the dot
    details.appendChild(summary);

    // ── Tooltip ──────────────────────────────────────────────────────────────
    const tooltip = document.createElement('div');
    tooltip.className = 'viriditas-indicator__tooltip';
    tooltip.setAttribute('role', 'tooltip');
    tooltip.innerHTML = '<strong>Schumann Alignment</strong>';
    this._ttBody = tooltip;
    details.appendChild(tooltip);

    this._root = details;
    document.body.appendChild(details);
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * Update the indicator with the latest AlignmentState.
   * Hides when confidence < 0.4 (advisory-only, sidecar data unreliable).
   */
  update(state: AlignmentState): void {
    if (state.confidence < 0.4) {
      this._root.setAttribute('hidden', '');
      return;
    }

    this._root.removeAttribute('hidden');

    const score = state.alignment_score;
    const dist  = state.disturbance_level ?? 'unavailable';

    this._arc.setAttribute('d', buildArcPath(score));
    this._score.textContent = score.toFixed(2);
    this._root.setAttribute('data-disturbance', dist);

    const updated = new Date(state.timestamp).toLocaleTimeString([], {
      hour:   '2-digit',
      minute: '2-digit',
    });

    // Tooltip — extended with LCI data when profile is loaded (M2)
    const lciLines = this._lciBaseline > 0
      ? [
          `LCI Baseline: <b>${this._lciBaseline.toFixed(3)}</b>`,
          `LCI Trend:    <b>${this._lciTrend}</b>`,
        ]
      : [];

    this._ttBody.innerHTML = [
      '<strong>Schumann Alignment</strong>',
      `SR Frequency: <b>${state.fundamental_hz.toFixed(2)} Hz</b>`,
      `Geomagnetic:  <b>${(state.geomagnetic_activity * 100).toFixed(0)}%</b>`,
      `Confidence:   <b>${(state.confidence * 100).toFixed(0)}%</b>`,
      `Updated: ${updated}`,
      ...lciLines,
    ].join('<br>');
  }

  /**
   * Load profile data into the indicator (M2 — Issue #756).
   *
   * Extracts lciHistory, lciTrend, and lciBaseline from the architect's
   * GAIANProfile and redraws the sparkline.  Safe to call at any time;
   * re-calling with an updated profile re-renders immediately.
   *
   * @param profile  The loaded GAIANProfile for this architect.
   */
  setProfile(profile: GAIANProfile): void {
    this._lciHistory  = profile.lciHistory  ?? [];
    this._lciTrend    = profile.lciTrend    ?? 'stable';
    this._lciBaseline = profile.lciBaseline ?? 0;
    this._root.setAttribute('data-lci-trend', this._lciTrend);
    this._drawSparkline();
  }

  /** Force-hide (e.g. during onboarding or Schumann-disabled mode). */
  hide(): void {
    this._root.setAttribute('hidden', '');
  }

  dispose(): void {
    this._root.remove();
  }

  // ── Sparkline renderer (M2) ────────────────────────────────────────────────

  /**
   * Draws the LCI history sparkline on the canvas.
   *
   * Algorithm:
   *   1. Take the last SPARK_MAX_POINTS entries from lciHistory.
   *   2. Map phi values to canvas Y coordinates (phi=1 → top, phi=0 → bottom).
   *   3. Distribute X positions evenly across the canvas width.
   *   4. Draw a stroke-only polyline in the trend colour.
   *   5. Draw a horizontal baseline at lciBaseline in a dimmer tint.
   *   6. If history is empty, clear the canvas silently (no error state).
   *
   * The canvas is never left in an inconsistent state — clearRect is
   * always called before any draw operation.
   */
  private _drawSparkline(): void {
    const ctx = this._sparkCtx;
    if (!ctx) return;

    ctx.clearRect(0, 0, SPARK_W, SPARK_H);

    const points = this._lciHistory.slice(-SPARK_MAX_POINTS);
    if (points.length < 2) return;   // nothing to draw yet

    const color    = TREND_COLORS[this._lciTrend] ?? TREND_COLORS.stable;
    const padV     = 2;              // vertical padding in logical px
    const drawH    = SPARK_H - padV * 2;

    // Y coordinate: phi=1 → padV (top), phi=0 → padV+drawH (bottom)
    const toY = (phi: number) => padV + (1 - Math.max(0, Math.min(1, phi))) * drawH;
    // X coordinate: evenly distributed
    const toX = (i: number) => (i / (points.length - 1)) * SPARK_W;

    // ── Baseline marker ──
    if (this._lciBaseline > 0) {
      const baseY = toY(this._lciBaseline);
      ctx.beginPath();
      ctx.moveTo(0, baseY);
      ctx.lineTo(SPARK_W, baseY);
      ctx.strokeStyle = color;
      ctx.globalAlpha = 0.20;
      ctx.lineWidth   = 0.75;
      ctx.setLineDash([2, 3]);
      ctx.stroke();
      ctx.setLineDash([]);          // reset dash for main line
      ctx.globalAlpha = 1.0;
    }

    // ── Phi line ──
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(points[0].phi));
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(toX(i), toY(points[i].phi));
    }
    ctx.strokeStyle = color;
    ctx.lineWidth   = 1.5;
    ctx.lineJoin    = 'round';
    ctx.lineCap     = 'round';
    ctx.stroke();

    // ── Terminal dot (last known phi) ──
    const lastX = toX(points.length - 1);
    const lastY = toY(points[points.length - 1].phi);
    ctx.beginPath();
    ctx.arc(lastX, lastY, 1.5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }
}
