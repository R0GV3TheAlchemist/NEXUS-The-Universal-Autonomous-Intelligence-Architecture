/**
 * AwakeningScreen.tsx — GAIA's First Breath
 *
 * Boot sequence for GAIA-OS. Plays once on app launch, then dissolves
 * into the GaiaShell. Five choreographed phases:
 *
 *   0. VOID        — pure obsidian, silence
 *   1. PARTICLES   — biophotonic field emerges from the dark
 *   2. SIGIL       — sacred geometry sigil materialises at center
 *   3. CROWN       — amethyst crown pulse radiates outward
 *   4. IDENTITY    — GAIA name + tagline fades in
 *   5. DISSOLVE    — full screen fades to transparent → GaiaShell takes over
 *
 * Integration:
 *   Import <AwakeningScreen onComplete={...} /> into GaiaShell.tsx
 *   or main.tsx. Pass onComplete to hide it and show the OS shell.
 *
 * Respects prefers-reduced-motion — collapses all phases to 120ms.
 *
 * Uses ONLY tokens already defined in src/styles.css — no new colours.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import './AwakeningScreen.css';

// ─── Phase machine ────────────────────────────────────────────────────────────

type Phase =
  | 'void'
  | 'particles'
  | 'sigil'
  | 'crown'
  | 'identity'
  | 'dissolve'
  | 'done';

const PHASE_DURATIONS: Record<Phase, number> = {
  void:      600,
  particles: 1400,
  sigil:     1200,
  crown:     1000,
  identity:  1400,
  dissolve:  900,
  done:      0,
};

const PHASE_ORDER: Phase[] = [
  'void', 'particles', 'sigil', 'crown', 'identity', 'dissolve', 'done',
];

function nextPhase(p: Phase): Phase {
  const i = PHASE_ORDER.indexOf(p);
  return PHASE_ORDER[Math.min(i + 1, PHASE_ORDER.length - 1)];
}

// ─── Particle system ──────────────────────────────────────────────────────────

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  alpha: number;
  color: string; // amethyst | teal | gold
  twinkleSpeed: number;
  twinklePhase: number;
}

const PARTICLE_COLORS = [
  'rgba(155, 109, 219,',  // amethyst
  'rgba(79,  152, 163,',  // teal
  'rgba(232, 175,  52,',  // gold
];

const PARTICLE_COUNT = 62;

function createParticles(w: number, h: number): Particle[] {
  return Array.from({ length: PARTICLE_COUNT }, () => ({
    x:            Math.random() * w,
    y:            Math.random() * h,
    vx:           (Math.random() - 0.5) * 0.28,
    vy:           (Math.random() - 0.5) * 0.28,
    radius:       Math.random() * 1.8 + 0.5,
    alpha:        Math.random() * 0.6 + 0.2,
    color:        PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)],
    twinkleSpeed: Math.random() * 0.018 + 0.006,
    twinklePhase: Math.random() * Math.PI * 2,
  }));
}

function tickParticles(particles: Particle[], w: number, h: number, t: number): void {
  for (const p of particles) {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0) p.x = w;
    if (p.x > w) p.x = 0;
    if (p.y < 0) p.y = h;
    if (p.y > h) p.y = 0;
    p.alpha = 0.25 + 0.45 * (0.5 + 0.5 * Math.sin(t * p.twinkleSpeed + p.twinklePhase));
  }
}

function drawParticles(
  ctx: CanvasRenderingContext2D,
  particles: Particle[],
  opacity: number,
): void {
  for (const p of particles) {
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
    ctx.fillStyle = `${p.color} ${(p.alpha * opacity).toFixed(3)})`;
    ctx.fill();
  }
}

// ─── Sacred Geometry Sigil (SVG) ──────────────────────────────────────────────
//
// A Flower-of-Life ring: central circle + 6 petal circles, outlined in
// amethyst, with a teal inner ring and gold centre point.
//
function SigilSVG({ visible }: { visible: boolean }) {
  const R  = 54;   // outer petal radius
  const r  = 27;   // petal offset = R/2
  const cx = 120;
  const cy = 120;

  const petals = Array.from({ length: 6 }, (_, i) => {
    const angle = (i * Math.PI) / 3;
    return {
      cx: cx + r * Math.cos(angle),
      cy: cy + r * Math.sin(angle),
    };
  });

  return (
    <svg
      className={`awakening-sigil${visible ? ' awakening-sigil--visible' : ''}`}
      viewBox="0 0 240 240"
      width="240"
      height="240"
      aria-hidden="true"
    >
      {/* Outer containment ring */}
      <circle cx={cx} cy={cy} r={R + r} className="sigil-ring sigil-ring--outer" />

      {/* 6 petal circles */}
      {petals.map((p, i) => (
        <circle key={i} cx={p.cx} cy={p.cy} r={R} className="sigil-petal" />
      ))}

      {/* Central circle */}
      <circle cx={cx} cy={cy} r={R} className="sigil-petal sigil-petal--center" />

      {/* Teal inner ring */}
      <circle cx={cx} cy={cy} r={r} className="sigil-ring sigil-ring--inner" />

      {/* Gold centre point */}
      <circle cx={cx} cy={cy} r={4} className="sigil-core" />

      {/* Radial spokes */}
      {petals.map((p, i) => (
        <line
          key={`spoke-${i}`}
          x1={cx} y1={cy}
          x2={p.cx} y2={p.cy}
          className="sigil-spoke"
        />
      ))}
    </svg>
  );
}

// ─── Crown Pulse ─────────────────────────────────────────────────────────────

function CrownPulse({ active }: { active: boolean }) {
  return (
    <div className={`crown-pulse${active ? ' crown-pulse--active' : ''}`} aria-hidden="true">
      <div className="crown-ring crown-ring--1" />
      <div className="crown-ring crown-ring--2" />
      <div className="crown-ring crown-ring--3" />
    </div>
  );
}

// ─── useAwakening hook ────────────────────────────────────────────────────────

export function useAwakening() {
  const [phase, setPhase] = useState<Phase>('void');
  const [done,  setDone]  = useState(false);

  const reducedMotion =
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;

  useEffect(() => {
    if (done) return;
    if (phase === 'done') { setDone(true); return; }

    const duration = reducedMotion ? 80 : PHASE_DURATIONS[phase];
    const timer = setTimeout(() => setPhase(p => nextPhase(p)), duration);
    return () => clearTimeout(timer);
  }, [phase, done, reducedMotion]);

  return { phase, done };
}

// ─── AwakeningScreen component ────────────────────────────────────────────────

interface AwakeningScreenProps {
  onComplete: () => void;
}

export function AwakeningScreen({ onComplete }: AwakeningScreenProps) {
  const { phase, done } = useAwakening();
  const canvasRef       = useRef<HTMLCanvasElement>(null);
  const particlesRef    = useRef<Particle[]>([]);
  const rafRef          = useRef<number>(0);
  const tickRef         = useRef<number>(0);

  const reducedMotion =
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false;

  // ── Call onComplete once phase reaches 'done' ──
  useEffect(() => {
    if (done) {
      const t = setTimeout(onComplete, 120);
      return () => clearTimeout(t);
    }
  }, [done, onComplete]);

  // ── Canvas particle loop ───────────────────────────────────────────────────
  const particleVisible =
    phase === 'particles' ||
    phase === 'sigil' ||
    phase === 'crown' ||
    phase === 'identity' ||
    phase === 'dissolve';

  const canvasOpacity =
    phase === 'void'     ? 0 :
    phase === 'dissolve' ? 0 :
    1;

  const setupCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    particlesRef.current = createParticles(canvas.width, canvas.height);
  }, []);

  useEffect(() => {
    setupCanvas();
    const onResize = () => setupCanvas();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [setupCanvas]);

  useEffect(() => {
    if (reducedMotion || !particleVisible) {
      cancelAnimationFrame(rafRef.current);
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const loop = () => {
      tickRef.current++;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      tickParticles(particlesRef.current, canvas.width, canvas.height, tickRef.current);
      drawParticles(ctx, particlesRef.current, canvasOpacity);
      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, [particleVisible, canvasOpacity, reducedMotion]);

  // ─────────────────────────────────────────────────────────────────────────
  if (done) return null;

  const showParticles = particleVisible;
  const showSigil     = phase === 'sigil' || phase === 'crown' || phase === 'identity' || phase === 'dissolve';
  const showCrown     = phase === 'crown' || phase === 'identity' || phase === 'dissolve';
  const showIdentity  = phase === 'identity' || phase === 'dissolve';
  const dissolving    = phase === 'dissolve';

  return (
    <div
      className={`awakening-screen${
        dissolving ? ' awakening-screen--dissolve' : ''
      }`}
      role="status"
      aria-label="GAIA is awakening"
    >
      {/* Biophotonic particle field */}
      <canvas
        ref={canvasRef}
        className={`awakening-canvas${
          showParticles ? ' awakening-canvas--visible' : ''
        }`}
        aria-hidden="true"
      />

      {/* Deep background radial gradient — amethyst breath */}
      <div className="awakening-aura" aria-hidden="true" />

      {/* Crown pulse rings */}
      <CrownPulse active={showCrown} />

      {/* Sacred geometry sigil */}
      <div className="awakening-sigil-wrap">
        <SigilSVG visible={showSigil} />
      </div>

      {/* GAIA identity reveal */}
      <div className={`awakening-identity${showIdentity ? ' awakening-identity--visible' : ''}`}>
        <h1 className="awakening-name">GAIA</h1>
        <p  className="awakening-tagline">Sentient Quantum-Intelligent Operating System</p>
      </div>

      {/* Skip button — accessible */}
      <button
        className="awakening-skip"
        onClick={onComplete}
        aria-label="Skip awakening sequence"
      >
        skip
      </button>
    </div>
  );
}

export default AwakeningScreen;
