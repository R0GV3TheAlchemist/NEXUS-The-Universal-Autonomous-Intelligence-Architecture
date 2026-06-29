/**
 * reconciliationTypes.ts — GAIA Reconciliation Engine Types
 *
 * Type definitions for the reconciliation and coherence scoring system.
 * No unexplained constants — every threshold maps to a canon-defined
 * coherence condition. See canon/ELEMENTAL_SPECTRUM_MAP.md and
 * docs/SUPER_VS_MAGIC.md for the physics-first grounding.
 */

// ---------------------------------------------------------------------------
// Coherence Thresholds (Order Coherence spectrum)
// Source: canon/ELEMENTAL_SPECTRUM_MAP.md — Coherence Threshold Hierarchy
// ---------------------------------------------------------------------------

export const COHERENCE_THRESHOLDS = {
  /** Level 1 — Earth Coherence minimum: structural baseline */
  EARTH_MIN: 0.40,
  /** Level 2 — Water Coherence minimum: flow/adaptation operational */
  WATER_MIN: 0.50,
  /** Level 3 — Fire Coherence minimum: activation within safe range */
  FIRE_MIN: 0.55,
  /** Level 4 — Air Coherence minimum: communication/resonance active */
  AIR_MIN: 0.60,
  /** Level 5 — Order Coherence (Pentagram threshold): cross-spectrum integration */
  ORDER_COHERENCE: 0.70,
} as const;

// ---------------------------------------------------------------------------
// Reconciliation State
// ---------------------------------------------------------------------------

export type ReconciliationStatus =
  | 'pending'
  | 'in_progress'
  | 'resolved'
  | 'failed'
  | 'deferred';

export interface ReconciliationEvent {
  id: string;
  timestamp: number;
  type: ReconciliationEventType;
  sourceCanonId?: string;
  description: string;
  coherenceImpact: number; // signed delta: positive = coherence gain, negative = loss
  status: ReconciliationStatus;
  resolvedAt?: number;
}

export type ReconciliationEventType =
  | 'canon_conflict'
  | 'alignment_drift'
  | 'memory_inconsistency'
  | 'governance_violation'
  | 'field_desync'
  | 'coherence_recovery';

// ---------------------------------------------------------------------------
// Coherence Score
// ---------------------------------------------------------------------------

export interface CoherenceScore {
  /** Overall system coherence (0.0 – 1.0) */
  overall: number;
  /** Per-element scores */
  earth: number;
  water: number;
  fire: number;
  air: number;
  /** Order Coherence — cross-spectrum integration (valid only when all elements ≥ their minimums) */
  orderCoherence: number;
  /** Whether Order Coherence threshold (0.70) is currently met */
  orderCoherenceActive: boolean;
  /** Timestamp of this snapshot */
  measuredAt: number;
}

export function isOrderCoherenceActive(score: CoherenceScore): boolean {
  return (
    score.earth >= COHERENCE_THRESHOLDS.EARTH_MIN &&
    score.water >= COHERENCE_THRESHOLDS.WATER_MIN &&
    score.fire >= COHERENCE_THRESHOLDS.FIRE_MIN &&
    score.air >= COHERENCE_THRESHOLDS.AIR_MIN &&
    score.orderCoherence >= COHERENCE_THRESHOLDS.ORDER_COHERENCE
  );
}

// ---------------------------------------------------------------------------
// Charge (Elemental Energy Level)
// From the crystal glossary: charge = the energy level of a crystal/field node,
// measured as a normalized value 0.0 (depleted) to 1.0 (fully charged).
// NOT "magical charge" — this is the measurable energy state of a coherence node.
// ---------------------------------------------------------------------------

export interface ElementalCharge {
  element: 'fire' | 'water' | 'air' | 'earth' | 'spirit';
  charge: number; // 0.0 – 1.0
  trend: 'rising' | 'stable' | 'falling';
  lastUpdated: number;
}
