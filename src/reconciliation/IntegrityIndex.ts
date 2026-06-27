/**
 * IntegrityIndex.ts
 * Computes the principal's overall coherence score (0–100) and per-domain
 * subscores from reconciliation history, active fragment state, and
 * CALLING pressure. Feeds the GAIA-OS dashboard and engine scheduling.
 *
 * Architecture contract:
 *   - IntegrityIndex is read-only. It never modifies fragments, cycles,
 *     or CALLINGs. All inputs are passed in or read via adapters.
 *   - The score is deterministic given the same inputs. No randomness.
 *   - Each scoring component is independently computed and documented,
 *     so the principal can understand why their score is what it is.
 *   - Scores are honest. No floors or artificial boosts. A score of 12
 *     means the system sees significant incoherence across all domains.
 *   - Trend analysis requires at least 3 score snapshots to be meaningful.
 *     With fewer snapshots, trend is returned as 'insufficient_data'.
 *
 * Canon layer : GAIA-OS Core — Integrity & Coherence Engine
 * Spec version : 1.0  (June 27 2026)
 * Depends on   : reconciliationTypes.ts, ReconciliationMemory.ts,
 *                CallingIssuer.ts, FragmentDetector.ts
 */

import {
  type Fragment,
  type ID,
  type ISOTimestamp,
  CHARGE_WEIGHTS,
} from './reconciliationTypes';

import type { RecurrenceSummary, PatternEntry } from './ReconciliationMemory';
import type { CallingSummary, CallingLevel }     from './CallingIssuer';
import type { FragmentSummary }                  from './FragmentDetector';

// ---------------------------------------------------------------------------
// 0. Score types
// ---------------------------------------------------------------------------

export type TrendDirection =
  | 'rising'            // score improving
  | 'falling'           // score declining
  | 'stable'            // within ±3 points over window
  | 'volatile'          // large swings without clear direction
  | 'insufficient_data';

export interface DomainScore {
  domain:          Fragment['domain'];
  score:           number;           // [0, 100]
  weight:          number;           // contribution weight in overall score [0, 1]
  components:      ScoreComponent[];
  primary_drag:    string | null;    // most impactful negative factor
}

export interface ScoreComponent {
  label:       string;
  value:       number;   // [0, 100] — higher is better
  weight:      number;   // contribution to domain score [0, 1]
  explanation: string;
}

export interface IntegrityScore {
  principal_id:       ID;
  overall:            number;        // [0, 100]
  domain_scores:      DomainScore[];
  calling_pressure:   number;        // [0, 100] — lower is better; subtracted from overall
  trend:              TrendDirection;
  trend_delta:        number | null; // points change over trend window (null if insufficient)
  active_fragments:   number;
  critical_callings:  number;
  integration_rate:   number;        // [0, 1]
  top_drag_factors:   string[];      // up to 3 most impactful negative factors
  computed_at:        ISOTimestamp;
}

export interface ScoreSnapshot {
  principal_id: ID;
  overall:      number;
  recorded_at:  ISOTimestamp;
}

// ---------------------------------------------------------------------------
// 1. Storage adapter
// ---------------------------------------------------------------------------

export interface IndexStorageAdapter {
  saveSnapshot(snapshot: ScoreSnapshot): Promise<void>;
  loadSnapshots(principalId: ID, limit: number): Promise<ScoreSnapshot[]>;
}

// ---------------------------------------------------------------------------
// 2. Scoring weights
// ---------------------------------------------------------------------------

/**
 * Domain weights in the overall score.
 * Psyche carries the most weight because it is the foundation of coherence
 * across all other domains. System and relational are downstream expressions.
 */
const DOMAIN_WEIGHTS: Record<Fragment['domain'], number> = {
  psyche:     0.50,
  relational: 0.30,
  system:     0.20,
};

/**
 * CALLING pressure weights per level.
 * Each active CALLING at this level subtracts this many points from the
 * overall score before the domain score is applied.
 */
const CALLING_PRESSURE_PER_LEVEL: Record<CallingLevel, number> = {
  NOTICE:   2,
  PROMPT:   5,
  SUMMONS:  10,
  CRITICAL: 20,
};

/** Maximum calling pressure that can be subtracted (caps at this value). */
const MAX_CALLING_PRESSURE = 40;

/** Trend window: how many most-recent snapshots to use for trend analysis. */
const TREND_WINDOW = 7;

/** Volatility threshold: if max - min > this over the window, trend is volatile. */
const VOLATILITY_THRESHOLD = 15;

/** Stable band: if delta over window is within ±this, trend is stable. */
const STABLE_BAND = 3;

// ---------------------------------------------------------------------------
// 3. IntegrityIndex class
// ---------------------------------------------------------------------------

export class IntegrityIndex {
  private readonly store: IndexStorageAdapter;

  constructor(store: IndexStorageAdapter) {
    this.store = store;
  }

  /**
   * Compute the full IntegrityScore for a principal.
   * Saves a ScoreSnapshot after computing.
   *
   * @param principalId   The principal being scored.
   * @param fragments     All currently active fragments (from FragmentDetector).
   * @param recurrence    RecurrenceSummary from ReconciliationMemory.
   * @param callings      CallingSummary from CallingIssuer.
   * @param patterns      Recent PatternEntries from ReconciliationMemory (last 90 days).
   */
  async compute(
    principalId: ID,
    fragments:   Fragment[],
    recurrence:  RecurrenceSummary,
    callings:    CallingSummary,
    patterns:    PatternEntry[],
  ): Promise<IntegrityScore> {

    // 1. Compute per-domain scores
    const systemScore     = this._scoreSystem(fragments, recurrence, patterns);
    const psycheScore     = this._scorePsyche(fragments, recurrence, patterns);
    const relationalScore = this._scoreRelational(fragments, recurrence, patterns);

    const domainScores = [systemScore, psycheScore, relationalScore];

    // 2. Weighted domain aggregate
    const weightedAggregate =
      systemScore.score     * DOMAIN_WEIGHTS.system +
      psycheScore.score     * DOMAIN_WEIGHTS.psyche +
      relationalScore.score * DOMAIN_WEIGHTS.relational;

    // 3. CALLING pressure deduction
    const callingPressure = this._computeCallingPressure(callings);

    // 4. Overall score (floor at 0)
    const overall = Math.max(0, Math.round(weightedAggregate - callingPressure));

    // 5. Trend analysis
    const snapshots = await this.store.loadSnapshots(principalId, TREND_WINDOW);
    const { trend, trendDelta } = this._computeTrend(snapshots, overall);

    // 6. Top drag factors (up to 3)
    const allComponents = domainScores.flatMap(d => d.components);
    const topDrags = allComponents
      .filter(c => c.value < 60)
      .sort((a, b) => (a.value * a.weight) - (b.value * b.weight))
      .slice(0, 3)
      .map(c => c.explanation);

    if (callingPressure > 0) {
      topDrags.unshift(
        `${callings.active_count} active CALLING(s) applying ${callingPressure.toFixed(0)}pts pressure.`,
      );
    }

    const score: IntegrityScore = {
      principal_id:      principalId,
      overall,
      domain_scores:     domainScores,
      calling_pressure:  callingPressure,
      trend,
      trend_delta:       trendDelta,
      active_fragments:  fragments.length,
      critical_callings: callings.by_level.CRITICAL,
      integration_rate:  recurrence.integration_rate,
      top_drag_factors:  topDrags.slice(0, 3),
      computed_at:       nowISO(),
    };

    // 7. Persist snapshot
    await this.store.saveSnapshot({
      principal_id: principalId,
      overall,
      recorded_at:  score.computed_at,
    });

    return score;
  }

  // =========================================================================
  // SYSTEM DOMAIN SCORING
  // =========================================================================

  private _scoreSystem(
    fragments:  Fragment[],
    recurrence: RecurrenceSummary,
    patterns:   PatternEntry[],
  ): DomainScore {
    const sysFragments = fragments.filter(f => f.domain === 'system');
    const sysPatterns  = patterns.filter(p => p.domain === 'system');

    // Component 1: Active fragment charge load
    const chargeLoad = this._chargeLoadScore(sysFragments);

    // Component 2: Integration rate for system fragments
    const sysIntRate = this._domainIntegrationRate(sysPatterns);
    const intRateScore: ScoreComponent = {
      label:       'System integration rate',
      value:       Math.round(sysIntRate * 100),
      weight:      0.35,
      explanation: sysIntRate < 0.5
        ? `System fragments resolve successfully less than half the time ` +
          `(${(sysIntRate * 100).toFixed(0)}%). Recurring instability.`
        : `System integration rate healthy at ${(sysIntRate * 100).toFixed(0)}%.`,
    };

    // Component 3: Recurrence streak penalty
    const streakPenalty = this._streakPenalty(
      recurrence.longest_unresolved_streaks.filter(s => s.domain === 'system'),
    );

    const components = [chargeLoad, intRateScore, streakPenalty];
    const score      = weightedScore(components);

    return {
      domain:       'system',
      score:        Math.round(score),
      weight:       DOMAIN_WEIGHTS.system,
      components,
      primary_drag: primaryDrag(components),
    };
  }

  // =========================================================================
  // PSYCHE DOMAIN SCORING
  // =========================================================================

  private _scorePsyche(
    fragments:  Fragment[],
    recurrence: RecurrenceSummary,
    patterns:   PatternEntry[],
  ): DomainScore {
    const psyFragments = fragments.filter(f => f.domain === 'psyche');
    const psyPatterns  = patterns.filter(p => p.domain === 'psyche');

    // Component 1: Active fragment charge load
    const chargeLoad = this._chargeLoadScore(psyFragments);

    // Component 2: Reflection continuity
    // Proxy: how many recent psyche cycles had a 'reflection_prompt' or
    // 'shadow_dialogue' strategy that ended integrated?
    const reflectionCycles = psyPatterns.filter(p =>
      (p.strategy_used === 'reflection_prompt' ||
       p.strategy_used === 'shadow_dialogue') &&
      p.outcome === 'integrated',
    );
    const totalPsyCycles = psyPatterns.length;
    const reflectionRate = totalPsyCycles > 0
      ? reflectionCycles.length / totalPsyCycles
      : 1; // no history = neutral, not penalised
    const reflectionScore: ScoreComponent = {
      label:       'Reflection continuity',
      value:       Math.round(reflectionRate * 100),
      weight:      0.35,
      explanation: reflectionRate < 0.4
        ? `Fewer than 40% of psyche cycles have ended in integrated reflection. ` +
          `The inner world is being detected but not tended.`
        : `Reflection continuity at ${(reflectionRate * 100).toFixed(0)}% — ` +
          `psyche cycles are resolving.`,
    };

    // Component 3: Shadow recurrence (how often shadow_autonomous re-enters)
    const shadowEntries   = psyPatterns.filter(p => p.category === 'shadow_autonomous');
    const shadowReEntries = shadowEntries.filter(p => p.outcome === 're_entry');
    const shadowReEntryRate = shadowEntries.length > 0
      ? shadowReEntries.length / shadowEntries.length
      : 0;
    const shadowScore: ScoreComponent = {
      label:       'Shadow integration momentum',
      value:       Math.round((1 - shadowReEntryRate) * 100),
      weight:      0.30,
      explanation: shadowReEntryRate > 0.6
        ? `Shadow material is re-entering the cycle repeatedly ` +
          `(${(shadowReEntryRate * 100).toFixed(0)}% re-entry rate). ` +
          `Archetypes are active but not integrating.`
        : `Shadow integration momentum healthy — ` +
          `most encounters are progressing.`,
    };

    const components = [chargeLoad, reflectionScore, shadowScore];
    const score      = weightedScore(components);

    return {
      domain:       'psyche',
      score:        Math.round(score),
      weight:       DOMAIN_WEIGHTS.psyche,
      components,
      primary_drag: primaryDrag(components),
    };
  }

  // =========================================================================
  // RELATIONAL DOMAIN SCORING
  // =========================================================================

  private _scoreRelational(
    fragments:  Fragment[],
    recurrence: RecurrenceSummary,
    patterns:   PatternEntry[],
  ): DomainScore {
    const relFragments = fragments.filter(f => f.domain === 'relational');
    const relPatterns  = patterns.filter(p => p.domain === 'relational');

    // Component 1: Active fragment charge load
    const chargeLoad = this._chargeLoadScore(relFragments);

    // Component 2: Rupture repair rate
    const ruptureEntries  = relPatterns.filter(p => p.category === 'rupture_unrepaired');
    const ruptureRepaired = ruptureEntries.filter(p => p.outcome === 'integrated');
    const ruptureRate     = ruptureEntries.length > 0
      ? ruptureRepaired.length / ruptureEntries.length
      : 1;
    const ruptureScore: ScoreComponent = {
      label:       'Rupture repair rate',
      value:       Math.round(ruptureRate * 100),
      weight:      0.40,
      explanation: ruptureRate < 0.5
        ? `More than half of detected relational ruptures have not been repaired. ` +
          `Unrepaired ruptures compound over time.`
        : `Rupture repair rate at ${(ruptureRate * 100).toFixed(0)}% — ` +
          `relational repair is active.`,
    };

    // Component 3: Contact continuity
    const withdrawalEntries = relPatterns.filter(p => p.category === 'contact_withdrawal');
    const withdrawalResolved = withdrawalEntries.filter(p => p.outcome === 'integrated');
    const contactRate = withdrawalEntries.length > 0
      ? withdrawalResolved.length / withdrawalEntries.length
      : 1;
    const contactScore: ScoreComponent = {
      label:       'Contact continuity',
      value:       Math.round(contactRate * 100),
      weight:      0.25,
      explanation: contactRate < 0.5
        ? `Contact withdrawal is frequently detected and not being resolved. ` +
          `Relational distance is accumulating.`
        : `Contact continuity healthy — withdrawal signals are being addressed.`,
    };

    const components = [chargeLoad, ruptureScore, contactScore];
    const score      = weightedScore(components);

    return {
      domain:       'relational',
      score:        Math.round(score),
      weight:       DOMAIN_WEIGHTS.relational,
      components,
      primary_drag: primaryDrag(components),
    };
  }

  // =========================================================================
  // SHARED COMPONENT BUILDERS
  // =========================================================================

  /**
   * Converts active fragment charge levels into a 0–100 score.
   * No active fragments = 100. Each fragment subtracts based on charge weight.
   * Score floors at 0.
   */
  private _chargeLoadScore(fragments: Fragment[]): ScoreComponent {
    if (fragments.length === 0) {
      return {
        label:       'Active fragment charge load',
        value:       100,
        weight:      0.35,
        explanation: 'No active fragments in this domain.',
      };
    }

    // Total charge weight: sum of CHARGE_WEIGHTS[charge] for all fragments
    const totalWeight = fragments.reduce(
      (sum, f) => sum + CHARGE_WEIGHTS[f.charge], 0,
    );
    // Scale: 0 weight = 100, weight of 10 = 0 (10 critical fragments = floor)
    const value = Math.max(0, Math.round(100 - (totalWeight / 10) * 100));

    const heaviest = fragments
      .sort((a, b) => CHARGE_WEIGHTS[b.charge] - CHARGE_WEIGHTS[a.charge])[0];

    return {
      label:       'Active fragment charge load',
      value,
      weight:      0.35,
      explanation: value < 60
        ? `${fragments.length} active fragment(s) carrying significant charge ` +
          `(heaviest: '${heaviest.label}' at ${heaviest.charge}).`
        : `Fragment charge load manageable — ` +
          `${fragments.length} active fragment(s) at moderate charge.`,
    };
  }

  /** Integration rate for a specific domain's pattern entries. */
  private _domainIntegrationRate(patterns: PatternEntry[]): number {
    if (patterns.length === 0) return 1;
    const integrated = patterns.filter(p => p.outcome === 'integrated').length;
    return integrated / patterns.length;
  }

  /** Penalty component for unresolved recurrence streaks in a domain. */
  private _streakPenalty(
    streaks: RecurrenceSummary['longest_unresolved_streaks'],
  ): ScoreComponent {
    if (streaks.length === 0) {
      return {
        label:       'Recurrence streak',
        value:       100,
        weight:      0.30,
        explanation: 'No unresolved recurrence streaks in this domain.',
      };
    }
    const worst = streaks[0];
    // Each consecutive re-entry subtracts 15 points (floor at 0)
    const value = Math.max(0, 100 - worst.consecutive_re_entries * 15);
    return {
      label:       'Recurrence streak',
      value,
      weight:      0.30,
      explanation: `'${worst.fragment_label}' has re-entered the cycle ` +
        `${worst.consecutive_re_entries} consecutive time(s) without resolving.`,
    };
  }

  // =========================================================================
  // CALLING PRESSURE
  // =========================================================================

  /**
   * Computes the total CALLING pressure to subtract from the overall score.
   * Capped at MAX_CALLING_PRESSURE to prevent catastrophic underflow.
   */
  private _computeCallingPressure(callings: CallingSummary): number {
    const raw =
      callings.by_level.NOTICE   * CALLING_PRESSURE_PER_LEVEL.NOTICE   +
      callings.by_level.PROMPT   * CALLING_PRESSURE_PER_LEVEL.PROMPT   +
      callings.by_level.SUMMONS  * CALLING_PRESSURE_PER_LEVEL.SUMMONS  +
      callings.by_level.CRITICAL * CALLING_PRESSURE_PER_LEVEL.CRITICAL;
    return Math.min(raw, MAX_CALLING_PRESSURE);
  }

  // =========================================================================
  // TREND ANALYSIS
  // =========================================================================

  private _computeTrend(
    snapshots:    ScoreSnapshot[],
    currentScore: number,
  ): { trend: TrendDirection; trendDelta: number | null } {
    // Include the current (not-yet-saved) score
    const all = [
      ...snapshots.map(s => s.overall),
      currentScore,
    ];

    if (all.length < 3) {
      return { trend: 'insufficient_data', trendDelta: null };
    }

    const window = all.slice(-TREND_WINDOW);
    const first  = window[0];
    const last   = window[window.length - 1];
    const delta  = last - first;
    const range  = Math.max(...window) - Math.min(...window);

    if (range > VOLATILITY_THRESHOLD) {
      return { trend: 'volatile', trendDelta: delta };
    }
    if (Math.abs(delta) <= STABLE_BAND) {
      return { trend: 'stable', trendDelta: delta };
    }
    return {
      trend:      delta > 0 ? 'rising' : 'falling',
      trendDelta: delta,
    };
  }

  // =========================================================================
  // SNAPSHOT HISTORY
  // =========================================================================

  /**
   * Returns the last N score snapshots for a principal, oldest-first.
   * Used by the dashboard to render the trend line.
   */
  async snapshotHistory(
    principalId: ID,
    limit = 30,
  ): Promise<ScoreSnapshot[]> {
    const snapshots = await this.store.loadSnapshots(principalId, limit);
    return snapshots.sort(
      (a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime(),
    );
  }
}

// ---------------------------------------------------------------------------
// 4. In-memory storage adapter
// ---------------------------------------------------------------------------

export class InMemoryIndexStorage implements IndexStorageAdapter {
  private _snapshots = new Map<ID, ScoreSnapshot[]>();

  async saveSnapshot(snapshot: ScoreSnapshot): Promise<void> {
    if (!this._snapshots.has(snapshot.principal_id))
      this._snapshots.set(snapshot.principal_id, []);
    this._snapshots.get(snapshot.principal_id)!.push({ ...snapshot });
  }

  async loadSnapshots(principalId: ID, limit: number): Promise<ScoreSnapshot[]> {
    const all = this._snapshots.get(principalId) ?? [];
    // Return most recent `limit` snapshots
    return all
      .sort((a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime())
      .slice(0, limit);
  }

  snapshot(): ScoreSnapshot[] {
    return [...this._snapshots.values()].flat();
  }
}

// ---------------------------------------------------------------------------
// 5. Internal helpers
// ---------------------------------------------------------------------------

function weightedScore(components: ScoreComponent[]): number {
  const totalWeight = components.reduce((s, c) => s + c.weight, 0);
  if (totalWeight === 0) return 100;
  return components.reduce((s, c) => s + c.value * (c.weight / totalWeight), 0);
}

function primaryDrag(components: ScoreComponent[]): string | null {
  const worst = components
    .filter(c => c.value < 70)
    .sort((a, b) => (a.value * a.weight) - (b.value * b.weight))[0];
  return worst?.explanation ?? null;
}

function nowISO(): ISOTimestamp {
  return new Date().toISOString();
}

// ---------------------------------------------------------------------------
// 6. Exports
// ---------------------------------------------------------------------------

export default IntegrityIndex;
