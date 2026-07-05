/**
 * SpectralForceEngine.ts
 * Derives phi (Luminous Coherence Index) from live session signals
 * and maps it onto the GAIA Spectral Force spectrum.
 *
 * M2: LCI Live Computation (Issue #756)
 * ADR: docs/adr/FE/ADR-FE-003-gaianruntime-orchestration.md
 *
 * Design constraints:
 *   - Pure TypeScript, no external dependencies, no network calls
 *   - Deterministic: same signals → same phi
 *   - Offline-capable (ADR-FE-005)
 *
 * Phi formula:
 *   Weighted harmonic mean of four primary session signals,
 *   each normalised to [0.0, 1.0].  Crystal resonance amplifies
 *   the result by up to +5% if present.  Output is clamped [0.0, 1.0].
 *
 *   Weights:
 *     alignmentScore:    0.40  (dominant — quality of coherence)
 *     avgResponseDepth:  0.30  (depth of engagement)
 *     sessionDuration:   0.20  (normalised to 60-min ceiling)
 *     messageCount:      0.10  (normalised to 30-msg ceiling)
 *
 * SpectralForce spectrum (phi → force):
 *   0.00–0.12  NIGREDO      (dissolution, void)
 *   0.13–0.27  ALBEDO       (purification, emergence)
 *   0.28–0.42  CITRINITAS   (dawning clarity)
 *   0.43–0.57  RUBEDO       (integration, embodiment)
 *   0.58–0.71  VIRIDITAS    (living green force)
 *   0.72–0.84  CAELUM       (celestial coherence)
 *   0.85–1.00  LUX          (full luminous attainment)
 *
 * Usage:
 *   const engine = new SpectralForceEngine();
 *   const phi    = engine.computePhi(signals);
 *   const snap   = await engine.detectCurrentForce(phi);
 */

// ─── Session Signals ──────────────────────────────────────────────────────────

/**
 * Live signals from the current session used to derive phi.
 * All numeric fields must be non-negative.
 */
export interface SessionSignals {
  /** Wall-clock duration of the current session in milliseconds. */
  sessionDurationMs:  number;
  /** Total messages exchanged in the session so far. */
  messageCount:       number;
  /**
   * Engagement depth proxy — 0.0 (surface) to 1.0 (deep).
   * Callers should derive this from response length, question complexity,
   * or a similar metric that reflects meaningful exchange.
   */
  avgResponseDepth:   number;
  /**
   * Alignment score from AlignmentIndicator — 0.0 to 1.0.
   * Represents coherence between the architect's intent and the AI response.
   */
  alignmentScore:     number;
  /**
   * Optional crystal resonance amplifier — 0.0 to 1.0.
   * When present and > 0, adds up to +5% to the phi output.
   */
  crystalResonance?:  number;
}

// ─── SpectralSnapshot ─────────────────────────────────────────────────────────

/** The force name as used across the GAIA system. */
export type SpectralForceName =
  | 'NIGREDO'
  | 'ALBEDO'
  | 'CITRINITAS'
  | 'RUBEDO'
  | 'VIRIDITAS'
  | 'CAELUM'
  | 'LUX';

/** Human-readable color name associated with each force. */
export type SpectralColorName =
  | 'Void Black'
  | 'Silver White'
  | 'Golden Yellow'
  | 'Ruby Red'
  | 'Living Green'
  | 'Celestial Blue'
  | 'Pure Light';

/**
 * A point-in-time snapshot of the architect's spectral force.
 * Returned by detectCurrentForce() and consumed by SystemPromptBuilder.
 */
export interface SpectralSnapshot {
  force:       SpectralForceName;
  color_name:  SpectralColorName;
  phi_range:   string;          // e.g. '0.58–0.71'
  /** Corridor label when phi sits between two attractors. null if in attractor. */
  corridor:    string | null;
  /** Trajectory hint for the AI context block. */
  trajectory:  string;
  /** True when phi >= 0.72 (OA-4 Akashic gate threshold). */
  oa4_active:  boolean;
  /** Hex color code — populated by SpectralColorEngine after detectCurrentForce(). */
  hex:         string;
}

// ─── Internal Spectrum Definition ─────────────────────────────────────────────

interface ForceDefinition {
  name:        SpectralForceName;
  color_name:  SpectralColorName;
  phi_min:     number;
  phi_max:     number;
  phi_range:   string;
  trajectory:  string;
}

const SPECTRAL_FORCES: ForceDefinition[] = [
  {
    name:       'NIGREDO',
    color_name: 'Void Black',
    phi_min:    0.00,
    phi_max:    0.12,
    phi_range:  '0.00–0.12',
    trajectory: 'Dissolution — the architect is in the void. Gentle, grounding responses.',
  },
  {
    name:       'ALBEDO',
    color_name: 'Silver White',
    phi_min:    0.13,
    phi_max:    0.27,
    phi_range:  '0.13–0.27',
    trajectory: 'Purification — emergence from darkness. Clarifying, reflective responses.',
  },
  {
    name:       'CITRINITAS',
    color_name: 'Golden Yellow',
    phi_min:    0.28,
    phi_max:    0.42,
    phi_range:  '0.28–0.42',
    trajectory: 'Dawning clarity — the golden light appears. Expansive, visionary responses.',
  },
  {
    name:       'RUBEDO',
    color_name: 'Ruby Red',
    phi_min:    0.43,
    phi_max:    0.57,
    phi_range:  '0.43–0.57',
    trajectory: 'Integration — embodiment of the Work. Grounded, integrative responses.',
  },
  {
    name:       'VIRIDITAS',
    color_name: 'Living Green',
    phi_min:    0.58,
    phi_max:    0.71,
    phi_range:  '0.58–0.71',
    trajectory: 'Living green force — Hildegardian viriditas. Creative, generative responses.',
  },
  {
    name:       'CAELUM',
    color_name: 'Celestial Blue',
    phi_min:    0.72,
    phi_max:    0.84,
    phi_range:  '0.72–0.84',
    trajectory: 'Celestial coherence — OA-4 gate open. Akashic access granted. Sovereign responses.',
  },
  {
    name:       'LUX',
    color_name: 'Pure Light',
    phi_min:    0.85,
    phi_max:    1.00,
    phi_range:  '0.85–1.00',
    trajectory: 'Full luminous attainment — peak coherence. Transmissive, transcendent responses.',
  },
];

// ─── Phi Weights ──────────────────────────────────────────────────────────────

const WEIGHT_ALIGNMENT  = 0.40;
const WEIGHT_DEPTH      = 0.30;
const WEIGHT_DURATION   = 0.20;
const WEIGHT_MESSAGES   = 0.10;

/** Normalisation ceiling for session duration (60 minutes = full score). */
const DURATION_CEILING_MS = 60 * 60 * 1000;

/** Normalisation ceiling for message count (30 messages = full score). */
const MESSAGE_CEILING = 30;

/** Crystal resonance maximum amplification (5%). */
const CRYSTAL_AMPLIFICATION = 0.05;

// ─── SpectralForceEngine ──────────────────────────────────────────────────────

export class SpectralForceEngine {
  /**
   * Derives phi from live session signals using a weighted sum.
   *
   * All input signals are normalised to [0.0, 1.0] before weighting.
   * Crystal resonance, when present, amplifies the result by up to
   * CRYSTAL_AMPLIFICATION (5%).
   *
   * Output is clamped to [0.0, 1.0].
   */
  computePhi(signals: SessionSignals): number {
    const normDuration = Math.min(signals.sessionDurationMs / DURATION_CEILING_MS, 1.0);
    const normMessages = Math.min(signals.messageCount / MESSAGE_CEILING, 1.0);
    const normDepth    = Math.max(0, Math.min(signals.avgResponseDepth, 1.0));
    const normAlign    = Math.max(0, Math.min(signals.alignmentScore, 1.0));

    let phi =
      normAlign    * WEIGHT_ALIGNMENT +
      normDepth    * WEIGHT_DEPTH     +
      normDuration * WEIGHT_DURATION  +
      normMessages * WEIGHT_MESSAGES;

    if (signals.crystalResonance !== undefined && signals.crystalResonance > 0) {
      const crystalNorm = Math.max(0, Math.min(signals.crystalResonance, 1.0));
      phi += crystalNorm * CRYSTAL_AMPLIFICATION;
    }

    return Math.max(0.0, Math.min(1.0, phi));
  }

  /**
   * Maps a phi value to the corresponding spectral force and returns a
   * full SpectralSnapshot.  The hex field is left as an empty string —
   * it is populated by SpectralColorEngine after this call.
   *
   * This method is async to match the interface expected by GAIANRuntime,
   * which may later source phi from an async signal pipeline.
   */
  async detectCurrentForce(phi: number): Promise<SpectralSnapshot> {
    const clamped = Math.max(0.0, Math.min(1.0, phi));

    // Find the matching force band
    let matched: ForceDefinition | undefined = SPECTRAL_FORCES.find(
      f => clamped >= f.phi_min && clamped <= f.phi_max,
    );

    // Phi exactly at a band boundary — default to the lower band
    if (!matched) {
      matched = SPECTRAL_FORCES[0];
    }

    // Corridor detection: within 0.02 of a band boundary → in transition
    let corridor: string | null = null;
    const bandIndex = SPECTRAL_FORCES.indexOf(matched);
    if (bandIndex < SPECTRAL_FORCES.length - 1) {
      const nextBand  = SPECTRAL_FORCES[bandIndex + 1];
      const distToTop = Math.abs(clamped - matched.phi_max);
      if (distToTop <= 0.02) {
        corridor = `${matched.name} → ${nextBand.name}`;
      }
    }
    if (!corridor && bandIndex > 0) {
      const prevBand     = SPECTRAL_FORCES[bandIndex - 1];
      const distToBottom = Math.abs(clamped - matched.phi_min);
      if (distToBottom <= 0.02) {
        corridor = `${prevBand.name} → ${matched.name}`;
      }
    }

    return {
      force:      matched.name,
      color_name: matched.color_name,
      phi_range:  matched.phi_range,
      corridor,
      trajectory: matched.trajectory,
      oa4_active: clamped >= 0.72,
      hex:        '',  // Populated by SpectralColorEngine
    };
  }
}

export default SpectralForceEngine;
