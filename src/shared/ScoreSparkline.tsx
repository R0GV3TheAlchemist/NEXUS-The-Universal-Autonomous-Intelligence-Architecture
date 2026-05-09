/**
 * src/shared/ScoreSparkline.tsx
 * GAIA-OS — Score History Sparkline
 * Issue #68 Phase 5
 *
 * Pure SVG sparkline — no canvas, no charting library.
 * Renders a smooth cubic-Bezier path from a number[] (0-100).
 * Gradient fill below the line uses --crystal-primary as the
 * stop colour, automatically responding to the current tier.
 *
 * On mount the path animates in via GSAP strokeDashoffset.
 * Reduced-motion: full path is visible immediately.
 *
 * Props:
 *   scores    — number[]  (0-100, newest last, min 2 values)
 *   height    — number    SVG height in px (default 48)
 *   className — string    optional extra class names
 *   showDots  — boolean   show min/max dots (default true)
 */

import React, { useEffect, useRef, useMemo } from 'react';
import gsap from 'gsap';

interface SparklineProps {
  scores:    number[];
  height?:   number;
  className?: string;
  showDots?:  boolean;
}

const PAD_X   = 4;   // horizontal padding in SVG units
const PAD_Y   = 6;   // vertical padding in SVG units
const VIEW_W  = 200; // viewBox width (scales with container)

function prefersReducedMotion(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

/**
 * Converts a scores array into a smooth SVG cubic-Bezier path string.
 * Uses cardinal spline tension 0.4 for a relaxed, organic curve.
 */
function buildPath(scores: number[], vw: number, vh: number): string {
  if (scores.length < 2) return '';
  const n   = scores.length;
  const xStep = (vw - PAD_X * 2) / (n - 1);
  const yRange = vh - PAD_Y * 2;

  const pts: [number, number][] = scores.map((s, i) => [
    PAD_X + i * xStep,
    PAD_Y + (1 - s / 100) * yRange,
  ]);

  // Build cubic bezier: each segment uses control points derived from
  // the slope between neighbours (cardinal spline tension = 0.4)
  const tension = 0.4;
  let d = `M ${pts[0][0].toFixed(2)} ${pts[0][1].toFixed(2)}`;

  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];

    const cp1x = p1[0] + (p2[0] - p0[0]) * tension;
    const cp1y = p1[1] + (p2[1] - p0[1]) * tension;
    const cp2x = p2[0] - (p3[0] - p1[0]) * tension;
    const cp2y = p2[1] - (p3[1] - p1[1]) * tension;

    d += ` C ${cp1x.toFixed(2)} ${cp1y.toFixed(2)},`
       +     ` ${cp2x.toFixed(2)} ${cp2y.toFixed(2)},`
       +     ` ${p2[0].toFixed(2)} ${p2[1].toFixed(2)}`;
  }
  return d;
}

export const ScoreSparkline: React.FC<SparklineProps> = ({
  scores,
  height    = 48,
  className = '',
  showDots  = true,
}) => {
  const pathRef      = useRef<SVGPathElement>(null);
  const gradientId   = useRef(`spark-grad-${Math.random().toString(36).slice(2)}`);
  const prevScores   = useRef<number[]>([]);

  const viewH = height;

  const pathD = useMemo(
    () => buildPath(scores, VIEW_W, viewH),
    [scores, viewH],
  );

  // Fill area path: close the path to the bottom
  const fillD = useMemo(() => {
    if (!pathD || scores.length < 2) return '';
    const n     = scores.length;
    const xLast = PAD_X + (n - 1) * ((VIEW_W - PAD_X * 2) / (n - 1));
    return `${pathD} L ${xLast.toFixed(2)} ${viewH} L ${PAD_X} ${viewH} Z`;
  }, [pathD, scores.length, viewH]);

  // Min/max dot positions
  const { minDot, maxDot } = useMemo(() => {
    if (scores.length < 2) return { minDot: null, maxDot: null };
    const n      = scores.length;
    const xStep  = (VIEW_W - PAD_X * 2) / (n - 1);
    const yRange = viewH - PAD_Y * 2;
    let minI = 0, maxI = 0;
    scores.forEach((s, i) => {
      if (s < scores[minI]) minI = i;
      if (s > scores[maxI]) maxI = i;
    });
    const dot = (i: number) => ({
      x: PAD_X + i * xStep,
      y: PAD_Y + (1 - scores[i] / 100) * yRange,
    });
    return { minDot: dot(minI), maxDot: dot(maxI) };
  }, [scores, viewH]);

  // GSAP draw-on animation when scores change meaningfully
  useEffect(() => {
    const el = pathRef.current;
    if (!el || scores.length < 2) return;
    if (prefersReducedMotion()) return;
    // Only animate on first render or when buffer size changes
    if (prevScores.current.length === scores.length) return;
    prevScores.current = scores;

    const len = el.getTotalLength();
    gsap.fromTo(
      el,
      { strokeDasharray: len, strokeDashoffset: len },
      { strokeDashoffset: 0, duration: 1.2, ease: 'power2.out' },
    );
  }, [scores]);

  if (scores.length < 2) {
    return (
      <div className={`score-sparkline score-sparkline--empty ${className}`}>
        <span className="score-sparkline__empty-label">Collecting data…</span>
      </div>
    );
  }

  return (
    <svg
      className={`score-sparkline ${className}`}
      viewBox={`0 0 ${VIEW_W} ${viewH}`}
      preserveAspectRatio="none"
      aria-hidden="true"
      style={{ width: '100%', height }}
    >
      <defs>
        <linearGradient id={gradientId.current} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"  stopColor="var(--crystal-primary, #a78bfa)" stopOpacity="0.30" />
          <stop offset="100%" stopColor="var(--crystal-primary, #a78bfa)" stopOpacity="0.02" />
        </linearGradient>
      </defs>

      {/* Gradient fill area */}
      {fillD && (
        <path
          d={fillD}
          fill={`url(#${gradientId.current})`}
          stroke="none"
        />
      )}

      {/* Sparkline path */}
      <path
        ref={pathRef}
        d={pathD}
        fill="none"
        stroke="var(--crystal-primary, #a78bfa)"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Min dot */}
      {showDots && minDot && (
        <circle
          cx={minDot.x} cy={minDot.y} r="3"
          fill="var(--crystal-primary, #a78bfa)"
          opacity="0.70"
        />
      )}

      {/* Max dot */}
      {showDots && maxDot && (
        <circle
          cx={maxDot.x} cy={maxDot.y} r="3.5"
          fill="var(--crystal-primary, #a78bfa)"
          opacity="1"
          stroke="rgba(255,255,255,0.4)"
          strokeWidth="1"
        />
      )}
    </svg>
  );
};

export default ScoreSparkline;
