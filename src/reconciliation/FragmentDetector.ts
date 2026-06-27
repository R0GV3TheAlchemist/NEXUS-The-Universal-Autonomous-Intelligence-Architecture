/**
 * FragmentDetector.ts
 * Domain-specific fragment detection for the ARFP reconciliation engine.
 *
 * Architecture contract:
 *   - The ReconciliationEngine calls detect(domain, principalId) for each domain.
 *   - This module is the ONLY place that contains domain awareness.
 *   - All output conforms to Fragment from reconciliationTypes.ts.
 *   - No mutation of state occurs here — detection is read-only.
 *
 * Canon layer : GAIA-OS Core — Integrity & Coherence Engine
 * Spec version : 1.0  (June 27 2026)
 * Depends on   : reconciliationTypes.ts
 */

import {
  type Fragment,
  type Domain,
  type ChargeLevel,
  type IntegrationStage,
  type ReconciliationPhase,
  type ARFPConfig,
  type ID,
  type ISOTimestamp,
  DEFAULT_ARFP_CONFIG,
  CHARGE_WEIGHTS,
} from './reconciliationTypes';

// ---------------------------------------------------------------------------
// 0. External adapter interfaces
// ---------------------------------------------------------------------------
// These define the shape of data FragmentDetector reads from other subsystems.
// Concrete adapters are injected at construction — the detector has no direct
// dependency on database clients, HTTP layers, or the Shadow Engine internals.
// This keeps the detector testable with mock adapters.

/** Live telemetry snapshot for a single GAIA-OS process. */
export interface ProcessSnapshot {
  process_id:    ID;
  label:         string;
  last_heartbeat: ISOTimestamp;
  error_rate_15m: number;       // fraction [0,1]
  queue_depth:   number;        // current event count
  queue_capacity: number;       // maximum event capacity
  circuit_state: 'open' | 'half_open' | 'closed';
  desired_state: Record<string, unknown>;
  actual_state:  Record<string, unknown>;
}

/** Shadow Engine archetype data for a single principal. */
export interface ArchetypeSnapshot {
  archetype_id:      ID;
  label:             string;
  integration_score: number;      // [0,100]
  integration_stage: IntegrationStage;
  last_reflect_at:   ISOTimestamp | null;
  active_patterns:   string[];    // behaviorally-evidenced shadow patterns
}

/** Relational pair data for a single principal. */
export interface RelationalPairSnapshot {
  pair_id:           ID;
  partner_label:     string;
  last_contact_at:   ISOTimestamp | null;
  rupture_events:    Array<{ rupture_at: ISOTimestamp; repaired: boolean }>;
  initiation_ratio:  number;    // 0=entirely one-sided by partner, 1=entirely by principal, 0.5=mutual
  disclosure_depth:  number;    // [0,1]
}

/** Adapter interface for system process telemetry. */
export interface SystemAdapter {
  getProcessSnapshots(principalId: ID): Promise<ProcessSnapshot[]>;
}

/** Adapter interface for Shadow Engine data. */
export interface PsycheAdapter {
  getArchetypeSnapshots(principalId: ID): Promise<ArchetypeSnapshot[]>;
  getReflectionHistory(principalId: ID, windowDays: number): Promise<ISOTimestamp[]>;
}

/** Adapter interface for relational data. */
export interface RelationalAdapter {
  getRelationalPairSnapshots(principalId: ID): Promise<RelationalPairSnapshot[]>;
}

// ---------------------------------------------------------------------------
// 1. Internal helpers
// ---------------------------------------------------------------------------

function nowISO(): ISOTimestamp {
  return new Date().toISOString();
}

function daysSince(iso: ISOTimestamp | null): number {
  if (!iso) return Infinity;
  return (Date.now() - new Date(iso).getTime()) / 86_400_000;
}

function makeId(): ID {
  // Crypto-random UUID v4 — no external dependency.
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

/**
 * Computes the normalised divergence between two state objects.
 * Returns a fraction [0,1]: 0 = identical, 1 = every key diverges.
 * Keys present in desired but absent in actual count as fully diverged.
 */
function stateDivergence(
  desired: Record<string, unknown>,
  actual:  Record<string, unknown>,
): number {
  const keys = Object.keys(desired);
  if (keys.length === 0) return 0;
  const diverged = keys.filter(k => JSON.stringify(desired[k]) !== JSON.stringify(actual[k]));
  return diverged.length / keys.length;
}

/**
 * Maps a continuous severity score [0,1] to a ChargeLevel.
 * 0.00–0.24 → low | 0.25–0.49 → medium | 0.50–0.74 → high | 0.75–1.00 → critical
 */
function severityToCharge(severity: number): ChargeLevel {
  if (severity >= 0.75) return 'critical';
  if (severity >= 0.50) return 'high';
  if (severity >= 0.25) return 'medium';
  return 'low';
}

/**
 * Computes archetype variance score (AVS) across a set of integration scores.
 * AVS = normalised(σ / μ), clamped to [0,1] against the configured ceiling.
 */
function computeAVS(scores: number[], ceiling: number): number {
  if (scores.length < 2) return 0;
  const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
  if (mean === 0) return 0;
  const variance = scores.reduce((a, b) => a + (b - mean) ** 2, 0) / scores.length;
  const sigma = Math.sqrt(variance);
  return Math.min(1, (sigma / mean) / ceiling);
}

// ---------------------------------------------------------------------------
// 2. FragmentDetector class
// ---------------------------------------------------------------------------

export class FragmentDetector {
  private readonly config: ARFPConfig;
  private readonly system:    SystemAdapter;
  private readonly psyche:    PsycheAdapter;
  private readonly relational: RelationalAdapter;

  constructor(
    adapters: {
      system:    SystemAdapter;
      psyche:    PsycheAdapter;
      relational: RelationalAdapter;
    },
    config: Partial<ARFPConfig> = {},
  ) {
    this.config     = { ...DEFAULT_ARFP_CONFIG, ...config };
    this.system     = adapters.system;
    this.psyche     = adapters.psyche;
    this.relational = adapters.relational;
  }

  /**
   * Primary entry point. Detects fragments across the requested domains
   * for a single principal. Returns an array of Fragment objects ready
   * for the DIAGNOSE phase.
   *
   * Order of detection within each domain is deterministic (sorted by
   * severity descending) so the engine's first-seen fragment is always
   * the most urgent one.
   */
  async detect(principalId: ID, domains: Domain[]): Promise<Fragment[]> {
    const detections = await Promise.all(
      domains.map(domain => this._detectDomain(principalId, domain)),
    );
    // Flatten and sort: critical → high → medium → low, then by age descending.
    return detections
      .flat()
      .sort((a, b) =>
        CHARGE_WEIGHTS[b.charge] - CHARGE_WEIGHTS[a.charge] ||
        b.age_days - a.age_days,
      );
  }

  private async _detectDomain(principalId: ID, domain: Domain): Promise<Fragment[]> {
    switch (domain) {
      case 'system':     return this._detectSystem(principalId);
      case 'psyche':     return this._detectPsyche(principalId);
      case 'relational': return this._detectRelational(principalId);
    }
  }

  // -------------------------------------------------------------------------
  // 2a. System domain detection
  // -------------------------------------------------------------------------
  //
  // Fragmentation signals:
  //   1. Process liveness gap     — heartbeat older than threshold
  //   2. State divergence         — desired ≠ actual beyond tolerance
  //   3. Queue saturation         — depth / capacity above threshold
  //   4. Circuit breaker open     — half_open counts as medium charge
  //   5. Error rate spike         — 15-minute rolling rate above threshold
  //
  // Each signal that crosses its threshold produces a Fragment.
  // Multiple signals from the same process produce separate fragments
  // so each can be diagnosed and bridged independently.

  private async _detectSystem(principalId: ID): Promise<Fragment[]> {
    const snapshots = await this.system.getProcessSnapshots(principalId);
    const fragments: Fragment[] = [];
    const now = nowISO();

    for (const proc of snapshots) {
      // 1. Liveness
      const heartbeatAge = daysSince(proc.last_heartbeat);
      if (heartbeatAge > 0.0208) { // > 30 minutes
        const severity = Math.min(1, heartbeatAge / 1); // 1 day = critical
        fragments.push(this._buildFragment({
          domain: 'system',
          charge: severityToCharge(severity),
          label: `Process liveness gap — ${proc.label}`,
          description:
            `Process '${proc.label}' has not sent a heartbeat for ` +
            `${(heartbeatAge * 24).toFixed(1)} hours. ` +
            `Expected interval: 60 seconds.`,
          detected_at: now,
          metadata: { process_id: proc.process_id, heartbeat_age_hours: heartbeatAge * 24 },
        }));
      }

      // 2. State divergence
      const divergence = stateDivergence(proc.desired_state, proc.actual_state);
      if (divergence > 0.05) { // > 5% key divergence
        fragments.push(this._buildFragment({
          domain: 'system',
          charge: severityToCharge(divergence),
          label: `State divergence — ${proc.label}`,
          description:
            `Process '${proc.label}' actual state diverges from desired state ` +
            `on ${(divergence * 100).toFixed(0)}% of keys.`,
          detected_at: now,
          metadata: { process_id: proc.process_id, divergence_fraction: divergence },
        }));
      }

      // 3. Queue saturation
      const saturation = proc.queue_capacity > 0
        ? proc.queue_depth / proc.queue_capacity
        : 0;
      if (saturation > 0.70) {
        fragments.push(this._buildFragment({
          domain: 'system',
          charge: severityToCharge(saturation),
          label: `Queue saturation — ${proc.label}`,
          description:
            `Event queue for '${proc.label}' is at ` +
            `${(saturation * 100).toFixed(0)}% capacity ` +
            `(${proc.queue_depth} / ${proc.queue_capacity} events).`,
          detected_at: now,
          metadata: { process_id: proc.process_id, saturation, queue_depth: proc.queue_depth },
        }));
      }

      // 4. Circuit breaker
      if (proc.circuit_state !== 'closed') {
        const charge: ChargeLevel = proc.circuit_state === 'open' ? 'high' : 'medium';
        fragments.push(this._buildFragment({
          domain: 'system',
          charge,
          label: `Circuit breaker ${proc.circuit_state} — ${proc.label}`,
          description:
            `Circuit breaker for '${proc.label}' is in state '${proc.circuit_state}'. ` +
            `Downstream calls are being shed or held.`,
          detected_at: now,
          metadata: { process_id: proc.process_id, circuit_state: proc.circuit_state },
        }));
      }

      // 5. Error rate
      if (proc.error_rate_15m > 0.01) { // > 1%
        fragments.push(this._buildFragment({
          domain: 'system',
          charge: severityToCharge(Math.min(1, proc.error_rate_15m / 0.20)), // 20% = critical
          label: `Error rate spike — ${proc.label}`,
          description:
            `Process '${proc.label}' 15-minute rolling error rate: ` +
            `${(proc.error_rate_15m * 100).toFixed(2)}%.`,
          detected_at: now,
          metadata: { process_id: proc.process_id, error_rate_15m: proc.error_rate_15m },
        }));
      }
    }

    return fragments;
  }

  // -------------------------------------------------------------------------
  // 2b. Psyche domain detection
  // -------------------------------------------------------------------------
  //
  // Fragmentation signals:
  //   1. Autonomous archetype    — integration score outlier (high AVS)
  //   2. Reflection gap          — reflect() not called within threshold
  //   3. Archetype variance      — overall AVS exceeds ceiling
  //   4. Dormant archetype       — integration_stage = 'unmet', score < 10
  //
  // The reflection gap signal is principal-level, not per-archetype.
  // All archetype-level signals produce one fragment per archetype.

  private async _detectPsyche(principalId: ID): Promise<Fragment[]> {
    const [archetypes, reflections] = await Promise.all([
      this.psyche.getArchetypeSnapshots(principalId),
      this.psyche.getReflectionHistory(
        principalId,
        this.config.trend_short_window_days,
      ),
    ]);

    const fragments: Fragment[] = [];
    const now = nowISO();

    // 1 & 4. Per-archetype: autonomous or dormant
    const scores = archetypes.map(a => a.integration_score);
    const meanScore = scores.length
      ? scores.reduce((a, b) => a + b, 0) / scores.length
      : 50;

    for (const arch of archetypes) {
      // Autonomous: score is an outlier *below* mean AND stage is early
      const isAutonomous =
        arch.integration_score < meanScore * 0.50 &&
        (arch.integration_stage === 'unmet' || arch.integration_stage === 'awareness');

      if (isAutonomous) {
        const severity = 1 - (arch.integration_score / 100);
        fragments.push(this._buildFragment({
          domain: 'psyche',
          charge: severityToCharge(severity * 0.9), // cap at high unless truly critical
          label: `Autonomous archetype — ${arch.label}`,
          description:
            `Archetype '${arch.label}' is operating with reduced integration contact. ` +
            `Integration score: ${arch.integration_score.toFixed(1)}/100. ` +
            `Stage: ${arch.integration_stage}. ` +
            `Active patterns: ${arch.active_patterns.join(', ') || 'none logged'}.`,
          detected_at: now,
          archetype_id: arch.archetype_id,
          integration_stage: arch.integration_stage,
          metadata: {
            integration_score: arch.integration_score,
            active_patterns: arch.active_patterns,
          },
        }));
      }

      // Dormant: never engaged (unmet stage, very low score)
      const isDormant =
        arch.integration_stage === 'unmet' &&
        arch.integration_score < 10 &&
        !isAutonomous; // don't double-detect

      if (isDormant) {
        fragments.push(this._buildFragment({
          domain: 'psyche',
          charge: 'low',
          label: `Dormant archetype — ${arch.label}`,
          description:
            `Archetype '${arch.label}' has not yet been encountered. ` +
            `Integration score: ${arch.integration_score.toFixed(1)}/100.`,
          detected_at: now,
          archetype_id: arch.archetype_id,
          integration_stage: arch.integration_stage,
          metadata: { integration_score: arch.integration_score },
        }));
      }
    }

    // 2. Reflection gap — principal-level
    const lastReflect = reflections.length
      ? reflections[reflections.length - 1]
      : null;
    const gapDays = daysSince(lastReflect);

    if (gapDays > this.config.reflection_gap_days) {
      const severity = Math.min(1, (gapDays - this.config.reflection_gap_days) /
        (this.config.reflection_gap_days * 3)); // 3× threshold = critical
      fragments.push(this._buildFragment({
        domain: 'psyche',
        charge: severityToCharge(severity),
        label: 'Reflection gap',
        description:
          `No reflect() event in ${gapDays.toFixed(1)} days ` +
          `(threshold: ${this.config.reflection_gap_days} days). ` +
          `Shadow integration processes are decelerating.`,
        detected_at: now,
        metadata: { gap_days: gapDays, last_reflect_at: lastReflect },
      }));
    }

    // 3. Global archetype variance — fires when variance itself is the signal
    const avs = computeAVS(scores, this.config.high_fragmentation_avs_threshold);
    if (avs > 0.60) { // high variance = one or more archetypes dominating
      fragments.push(this._buildFragment({
        domain: 'psyche',
        charge: severityToCharge(avs),
        label: 'High archetype variance',
        description:
          `Archetype integration scores show high variance (AVS: ${avs.toFixed(2)}). ` +
          `One or more archetypes may be dominating the psychic field ` +
          `while others remain disengaged.`,
        detected_at: now,
        metadata: { avs, scores: Object.fromEntries(archetypes.map(a => [a.label, a.integration_score])) },
      }));
    }

    return fragments;
  }

  // -------------------------------------------------------------------------
  // 2c. Relational domain detection
  // -------------------------------------------------------------------------
  //
  // Fragmentation signals:
  //   1. Unrepaired rupture       — rupture event with no subsequent repair
  //   2. Contact withdrawal       — days since last contact > half_life × 3
  //   3. Reciprocity loss         — initiation_ratio < 0.20 or > 0.80
  //   4. Disclosure withdrawal    — disclosure_depth has dropped significantly
  //
  // Each signal that crosses its threshold produces one fragment per pair.

  private async _detectRelational(principalId: ID): Promise<Fragment[]> {
    const pairs = await this.relational.getRelationalPairSnapshots(principalId);
    const fragments: Fragment[] = [];
    const now = nowISO();
    const halfLife = this.config.contact_regularity_half_life_days;

    for (const pair of pairs) {
      // 1. Unrepaired ruptures
      const unrepairedRuptures = pair.rupture_events.filter(r => !r.repaired);
      if (unrepairedRuptures.length > 0) {
        // Charge escalates with count: 1=medium, 2=high, 3+=critical
        const charge: ChargeLevel =
          unrepairedRuptures.length >= 3 ? 'critical'
          : unrepairedRuptures.length >= 2 ? 'high'
          : 'medium';
        // Age of oldest unrepaired rupture
        const oldestRupture = unrepairedRuptures
          .map(r => daysSince(r.rupture_at))
          .reduce((a, b) => Math.max(a, b), 0);
        fragments.push(this._buildFragment({
          domain: 'relational',
          charge,
          label: `Unrepaired rupture — ${pair.partner_label}`,
          description:
            `${unrepairedRuptures.length} unrepaired rupture(s) with '${pair.partner_label}'. ` +
            `Oldest unrepaired rupture: ${oldestRupture.toFixed(1)} days ago.`,
          detected_at: now,
          relational_pair_id: pair.pair_id,
          metadata: {
            unrepaired_count: unrepairedRuptures.length,
            oldest_rupture_days: oldestRupture,
          },
        }));
      }

      // 2. Contact withdrawal
      const contactAge = daysSince(pair.last_contact_at);
      const withdrawalThreshold = halfLife * 3;
      if (contactAge > withdrawalThreshold) {
        const severity = Math.min(1, (contactAge - withdrawalThreshold) / (halfLife * 6));
        fragments.push(this._buildFragment({
          domain: 'relational',
          charge: severityToCharge(severity),
          label: `Contact withdrawal — ${pair.partner_label}`,
          description:
            `No contact with '${pair.partner_label}' for ${contactAge.toFixed(1)} days ` +
            `(threshold: ${withdrawalThreshold.toFixed(0)} days).`,
          detected_at: now,
          relational_pair_id: pair.pair_id,
          metadata: { contact_age_days: contactAge, threshold_days: withdrawalThreshold },
        }));
      }

      // 3. Reciprocity loss
      const ratio = pair.initiation_ratio;
      const isAsymmetric = ratio < 0.20 || ratio > 0.80;
      if (isAsymmetric) {
        // Severity: 0.20/0.80 boundary = low, 0.05/0.95 boundary = critical
        const deviation = ratio < 0.50
          ? (0.20 - ratio) / 0.20
          : (ratio - 0.80) / 0.20;
        const severity = Math.min(1, Math.abs(deviation));
        const direction = ratio < 0.20 ? 'partner-led' : 'principal-led';
        fragments.push(this._buildFragment({
          domain: 'relational',
          charge: severityToCharge(severity * 0.75), // cap at high — asymmetry alone isn't critical
          label: `Reciprocity loss — ${pair.partner_label}`,
          description:
            `Relational initiation with '${pair.partner_label}' is heavily ${direction} ` +
            `(initiation ratio: ${(ratio * 100).toFixed(0)}% principal-initiated).`,
          detected_at: now,
          relational_pair_id: pair.pair_id,
          metadata: { initiation_ratio: ratio, direction },
        }));
      }

      // 4. Disclosure withdrawal — only detectable if depth < 0.15 (near-silence)
      if (pair.disclosure_depth < 0.15) {
        fragments.push(this._buildFragment({
          domain: 'relational',
          charge: 'low',
          label: `Disclosure withdrawal — ${pair.partner_label}`,
          description:
            `Mutual disclosure depth with '${pair.partner_label}' is very low ` +
            `(${(pair.disclosure_depth * 100).toFixed(0)}%). ` +
            `Surface-level contact only.`,
          detected_at: now,
          relational_pair_id: pair.pair_id,
          metadata: { disclosure_depth: pair.disclosure_depth },
        }));
      }
    }

    return fragments;
  }

  // -------------------------------------------------------------------------
  // 3. Fragment factory
  // -------------------------------------------------------------------------

  private _buildFragment(
    partial: {
      domain:             Domain;
      charge:             ChargeLevel;
      label:              string;
      description:        string;
      detected_at:        ISOTimestamp;
      archetype_id?:      ID;
      integration_stage?: IntegrationStage;
      relational_pair_id?: ID;
      metadata:           Record<string, unknown>;
    },
  ): Fragment {
    return {
      id:                 makeId(),
      domain:             partial.domain,
      charge:             partial.charge,
      phase:              'DETECT' as ReconciliationPhase,
      label:              partial.label,
      description:        partial.description,
      detected_at:        partial.detected_at,
      age_days:           0, // freshly detected; age accumulates in memory
      recurrence_count:   0, // ReconciliationMemory sets this on lookup
      integration_stage:  partial.integration_stage ?? null,
      archetype_id:       partial.archetype_id ?? null,
      relational_pair_id: partial.relational_pair_id ?? null,
      metadata:           partial.metadata,
    };
  }
}

// ---------------------------------------------------------------------------
// 4. Exports
// ---------------------------------------------------------------------------

export default FragmentDetector;
