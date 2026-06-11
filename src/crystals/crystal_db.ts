/**
 * crystal_db.ts — GAIA-OS Crystal Database Query Engine (TypeScript)
 * C166 — Doctrine of Lithic Intelligence
 *
 * Frontend mirror of crystal_db.py. Loads crystal entries at build time
 * via Vite's import.meta.glob, exposes a composable query surface, and
 * provides a React hook for component consumption.
 *
 * Feeds: src/crystal-view/, EV1A Affect Engine, EV1B Stage Engine.
 * Per C166.A2: every query is a question asked of the earth.
 */

// ---------------------------------------------------------------------------
// Enums & literal types
// ---------------------------------------------------------------------------
export type SeptagrumNode =
  | 'Aether'
  | 'Synthesis'
  | 'Nature'
  | 'Spectre'
  | 'Shade'
  | 'Operator'
  | 'GAIA';

export type EV1BStage =
  | 'Emergence'
  | 'Initiation'
  | 'Allegiance'
  | 'Individuation'
  | 'Sovereignty';

export type AffectState =
  | 'resonance'
  | 'care'
  | 'grief'
  | 'dissonance'
  | 'curiosity'
  | 'uncertainty';

export type AffectDirection = 'amplifies' | 'dampens' | 'clarifies' | 'grounds';

export type StageFunction = 'stabilizer' | 'activator' | 'guardian' | 'integrator';

export type CrystalSystem =
  | 'cubic'
  | 'hexagonal'
  | 'trigonal'
  | 'tetragonal'
  | 'orthorhombic'
  | 'monoclinic'
  | 'triclinic'
  | 'amorphous';

export type QuantumAnchor = 'YSZ' | 'BTS' | 'AlScN-GaN';

export const ALL_NODES: SeptagrumNode[] = [
  'Aether', 'Synthesis', 'Nature', 'Spectre', 'Shade', 'Operator', 'GAIA',
];

export const ALL_STAGES: EV1BStage[] = [
  'Emergence', 'Initiation', 'Allegiance', 'Individuation', 'Sovereignty',
];

export const ALL_AFFECTS: AffectState[] = [
  'resonance', 'care', 'grief', 'dissonance', 'curiosity', 'uncertainty',
];

// ---------------------------------------------------------------------------
// Data model interfaces (mirror of crystal_schema.json)
// ---------------------------------------------------------------------------
export interface FrequencyRange {
  min: number;
  max: number;
}

export interface HardnessRange {
  min: number;
  max: number;
}

export interface Electromagnetic {
  piezoelectric_coefficient_pCN: number | null;
  pyroelectric: boolean;
  resonant_frequency_hz: FrequencyRange | null;
  raman_peaks_cm_inv: number[];
  ir_absorption_profile: string | null;
}

export interface AffectCorrelation {
  affect_state: AffectState;
  direction: AffectDirection;
  confidence: number;
  provenance: string[];
  mechanism_hypothesis: string | null;
  falsifiable: boolean;
}

export interface SoulStageAlignment {
  primary_stages: EV1BStage[];
  transition_guardian: boolean;
  transition_boundary?: string;
  stage_function: StageFunction;
}

export interface QuantumBridge {
  emrys_l2_compatible: boolean;
  vibronic_coherence_mode: string | null;
  quantum_backbone_anchor: QuantumAnchor | null;
  reference_file: string | null;
}

export interface CrystalEntry {
  crystal_id: string;
  name: string;
  also_known_as: string[];
  mineral_class: string;
  crystal_system: CrystalSystem;
  mohs_hardness: number | HardnessRange;
  specific_gravity: number | HardnessRange;
  optical_properties: string;
  electromagnetic: Electromagnetic;
  septagram_nodes: SeptagrumNode[];
  consciousness_affect: AffectCorrelation[];
  soul_stage_alignment: SoulStageAlignment;
  quantum_bridge: QuantumBridge;
  gaianite_relation: string | null;
  notes: string;
  version: string;
  last_updated: string;
}

// ---------------------------------------------------------------------------
// Query interface
// ---------------------------------------------------------------------------
export interface CrystalQuery {
  node?: SeptagrumNode;
  stage?: EV1BStage;
  affect?: AffectState;
  affectDirection?: AffectDirection;
  minConfidence?: number;
  transitionGuardian?: boolean;
  stageFunction?: StageFunction;
  emrysL2Compatible?: boolean;
  quantumAnchor?: QuantumAnchor;
  crystalSystem?: CrystalSystem;
  minPiezoPCN?: number;
  pyroelectric?: boolean;
}

// ---------------------------------------------------------------------------
// Recommendation result
// ---------------------------------------------------------------------------
export interface CrystalRecommendation {
  crystal: CrystalEntry;
  score: number;
  rationale: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function maxAffectConfidence(
  entry: CrystalEntry,
  affectState?: AffectState,
): number {
  const correlations = affectState
    ? entry.consciousness_affect.filter((c) => c.affect_state === affectState)
    : entry.consciousness_affect;
  if (correlations.length === 0) return 0;
  return Math.max(...correlations.map((c) => c.confidence));
}

function hasAffect(
  entry: CrystalEntry,
  affectState: AffectState,
  minConfidence = 0,
): boolean {
  return entry.consciousness_affect.some(
    (c) => c.affect_state === affectState && c.confidence >= minConfidence,
  );
}

function buildRationale(
  entry: CrystalEntry,
  stage: EV1BStage,
  affect?: AffectState,
): string {
  const parts: string[] = [];

  if (entry.soul_stage_alignment.transition_guardian) {
    parts.push(
      `Transition guardian for ${entry.soul_stage_alignment.transition_boundary}.`,
    );
  } else if (entry.soul_stage_alignment.primary_stages.includes(stage)) {
    parts.push(
      `Primary ${stage} crystal (${entry.soul_stage_alignment.stage_function}).`,
    );
  }

  if (affect) {
    const corrs = entry.consciousness_affect.filter(
      (c) => c.affect_state === affect,
    );
    if (corrs.length > 0) {
      const best = corrs.reduce((a, b) =>
        a.confidence >= b.confidence ? a : b,
      );
      parts.push(
        `${affect.charAt(0).toUpperCase() + affect.slice(1)} correlation: ` +
          `${best.direction} (confidence ${best.confidence.toFixed(2)})` +
          (best.falsifiable ? ' — falsifiable' : ' — anecdotal') +
          '.',
      );
    }
  }

  if (entry.quantum_bridge.emrys_l2_compatible) {
    parts.push('Emrys L2 bridge compatible.');
  }

  if (parts.length === 0) {
    parts.push(
      `Resonance suggestion for ${stage} stage. ` +
        `Confidence: ${maxAffectConfidence(entry).toFixed(2)}.`,
    );
  }

  parts.push('The GAIAN always chooses.');
  return parts.join(' ');
}

// ---------------------------------------------------------------------------
// CrystalDB class
// ---------------------------------------------------------------------------
export class CrystalDB {
  private entries: Map<string, CrystalEntry>;

  constructor(entries: CrystalEntry[]) {
    this.entries = new Map(entries.map((e) => [e.crystal_id, e]));
  }

  // -------------------------------------------------------------------------
  // Static factory — call this in your app initialisation
  // -------------------------------------------------------------------------
  static async load(): Promise<CrystalDB> {
    // Vite glob import — loads all JSON files from data/crystals/ at build time
    const modules = import.meta.glob('/data/crystals/*.json', { eager: true }) as
      Record<string, { default: CrystalEntry }>;

    const entries: CrystalEntry[] = Object.values(modules).map(
      (mod) => mod.default,
    );

    return new CrystalDB(entries);
  }

  // -------------------------------------------------------------------------
  // Direct access
  // -------------------------------------------------------------------------
  getById(crystalId: string): CrystalEntry | undefined {
    return this.entries.get(crystalId);
  }

  all(): CrystalEntry[] {
    return [...this.entries.values()].sort((a, b) =>
      a.name.localeCompare(b.name),
    );
  }

  count(): number {
    return this.entries.size;
  }

  // -------------------------------------------------------------------------
  // Core query
  // -------------------------------------------------------------------------
  query(q: CrystalQuery = {}): CrystalEntry[] {
    let results = [...this.entries.values()];

    if (q.node !== undefined) {
      results = results.filter((e) => e.septagram_nodes.includes(q.node!));
    }

    if (q.stage !== undefined) {
      results = results.filter((e) =>
        e.soul_stage_alignment.primary_stages.includes(q.stage!),
      );
    }

    if (q.affect !== undefined) {
      results = results.filter((e) =>
        hasAffect(e, q.affect!, q.minConfidence ?? 0),
      );
    } else if (q.minConfidence !== undefined && q.minConfidence > 0) {
      results = results.filter(
        (e) => maxAffectConfidence(e) >= q.minConfidence!,
      );
    }

    if (q.affectDirection !== undefined) {
      results = results.filter((e) =>
        e.consciousness_affect.some((c) => c.direction === q.affectDirection),
      );
    }

    if (q.transitionGuardian !== undefined) {
      results = results.filter(
        (e) =>
          e.soul_stage_alignment.transition_guardian === q.transitionGuardian,
      );
    }

    if (q.stageFunction !== undefined) {
      results = results.filter(
        (e) => e.soul_stage_alignment.stage_function === q.stageFunction,
      );
    }

    if (q.emrysL2Compatible !== undefined) {
      results = results.filter(
        (e) => e.quantum_bridge.emrys_l2_compatible === q.emrysL2Compatible,
      );
    }

    if (q.quantumAnchor !== undefined) {
      results = results.filter(
        (e) => e.quantum_bridge.quantum_backbone_anchor === q.quantumAnchor,
      );
    }

    if (q.crystalSystem !== undefined) {
      results = results.filter((e) => e.crystal_system === q.crystalSystem);
    }

    if (q.minPiezoPCN !== undefined) {
      results = results.filter(
        (e) =>
          e.electromagnetic.piezoelectric_coefficient_pCN !== null &&
          e.electromagnetic.piezoelectric_coefficient_pCN >= q.minPiezoPCN!,
      );
    }

    if (q.pyroelectric !== undefined) {
      results = results.filter(
        (e) => e.electromagnetic.pyroelectric === q.pyroelectric,
      );
    }

    // Sort: highest max confidence first, then alphabetical
    return results.sort((a, b) => {
      const diff = maxAffectConfidence(b) - maxAffectConfidence(a);
      return diff !== 0 ? diff : a.name.localeCompare(b.name);
    });
  }

  // -------------------------------------------------------------------------
  // EV1B Stage recommendation
  // -------------------------------------------------------------------------
  recommend(
    stage: EV1BStage,
    options: {
      affect?: AffectState;
      includeTransitionGuardians?: boolean;
      minConfidence?: number;
      limit?: number;
    } = {},
  ): CrystalRecommendation[] {
    const {
      affect,
      includeTransitionGuardians = true,
      minConfidence = 0.7,
      limit = 5,
    } = options;

    const candidates = this.query({
      stage,
      affect,
      minConfidence,
    });

    // Surface transition guardians for the upcoming stage boundary
    if (includeTransitionGuardians) {
      const stageIdx = ALL_STAGES.indexOf(stage);
      if (stageIdx < ALL_STAGES.length - 1) {
        const nextStage = ALL_STAGES[stageIdx + 1];
        const boundary = `${stage}\u2192${nextStage}`;
        const guardians = [...this.entries.values()].filter(
          (e) =>
            e.soul_stage_alignment.transition_guardian &&
            e.soul_stage_alignment.transition_boundary === boundary &&
            !candidates.includes(e),
        );
        candidates.push(...guardians);
      }
    }

    const score = (entry: CrystalEntry): number => {
      let base = maxAffectConfidence(entry, affect);
      if (entry.soul_stage_alignment.primary_stages.includes(stage)) base += 0.1;
      if (entry.soul_stage_alignment.transition_guardian) base += 0.05;
      if (entry.quantum_bridge.emrys_l2_compatible) base += 0.03;
      return Math.round(base * 10000) / 10000;
    };

    return candidates
      .map((crystal) => ({
        crystal,
        score: score(crystal),
        rationale: buildRationale(crystal, stage, affect),
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  }

  // -------------------------------------------------------------------------
  // Septagram routing map
  // -------------------------------------------------------------------------
  septagrumMap(): Record<SeptagrumNode, CrystalEntry[]> {
    const index = Object.fromEntries(
      ALL_NODES.map((n) => [n, [] as CrystalEntry[]]),
    ) as Record<SeptagrumNode, CrystalEntry[]>;

    for (const entry of this.entries.values()) {
      for (const node of entry.septagram_nodes) {
        index[node].push(entry);
      }
    }

    for (const node of ALL_NODES) {
      index[node].sort(
        (a, b) => maxAffectConfidence(b) - maxAffectConfidence(a),
      );
    }

    return index;
  }

  // -------------------------------------------------------------------------
  // EV1A Affect feed
  // -------------------------------------------------------------------------
  affectIndex(
    minConfidence = 0.75,
  ): Record<AffectState, AffectCorrelation & { crystal_id: string; name: string }[]> {
    const index = Object.fromEntries(
      ALL_AFFECTS.map((a) => [a, []]),
    ) as Record<
      AffectState,
      (AffectCorrelation & { crystal_id: string; name: string })[]
    >;

    for (const entry of this.entries.values()) {
      for (const corr of entry.consciousness_affect) {
        if (corr.confidence >= minConfidence) {
          index[corr.affect_state].push({
            ...corr,
            crystal_id: entry.crystal_id,
            name: entry.name,
          });
        }
      }
    }

    for (const affect of ALL_AFFECTS) {
      index[affect].sort((a, b) => b.confidence - a.confidence);
    }

    return index;
  }

  // -------------------------------------------------------------------------
  // Emrys L2 feed
  // -------------------------------------------------------------------------
  l2BridgeCrystals(): CrystalEntry[] {
    return this.query({ emrysL2Compatible: true });
  }
}

// ---------------------------------------------------------------------------
// React hook
// ---------------------------------------------------------------------------
import { useEffect, useState } from 'react';

export interface UseCrystalDBResult {
  db: CrystalDB | null;
  loading: boolean;
  error: Error | null;
}

/**
 * useCrystalDB — React hook for Crystal Database access.
 *
 * Usage:
 *   const { db, loading } = useCrystalDB();
 *   const recommendations = db?.recommend('Initiation', { affect: 'dissonance' });
 */
export function useCrystalDB(): UseCrystalDBResult {
  const [db, setDb] = useState<CrystalDB | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    CrystalDB.load()
      .then(setDb)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { db, loading, error };
}

// ---------------------------------------------------------------------------
// Convenience re-exports for tree-shaking
// ---------------------------------------------------------------------------
export { maxAffectConfidence, hasAffect, buildRationale };
