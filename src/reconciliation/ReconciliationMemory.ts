/**
 * ReconciliationMemory.ts
 * Persistence layer for the ARFP reconciliation engine.
 * Records every phase transition, stores cycle histories, tracks recurrence,
 * and surfaces pattern data for the IntegrityIndex and CallingIssuer.
 *
 * Architecture contract:
 *   - Memory is the single source of truth for what has happened to a fragment.
 *   - All writes are append-only within a cycle. Cycles are immutable once sealed.
 *   - ReconciliationMemory never modifies Fragment state. It observes and records.
 *   - The StorageAdapter is the only I/O surface. Everything else is pure logic.
 *   - Recurrence is computed from sealed cycles, not inferred from live state.
 *
 * Canon layer : GAIA-OS Core — Integrity & Coherence Engine
 * Spec version : 1.0  (June 27 2026)
 * Depends on   : reconciliationTypes.ts, IntegrationVerifier.ts
 */

import {
  type Fragment,
  type Diagnosis,
  type BridgeResult,
  type ReconciliationCycle,
  type ReconciliationPhase,
  type ID,
  type ISOTimestamp,
} from './reconciliationTypes';

import type { VerificationResult } from './IntegrationVerifier';

// ---------------------------------------------------------------------------
// 0. Storage adapter interface
// ---------------------------------------------------------------------------

/**
 * All persistence is delegated to a StorageAdapter.
 * The engine injects the appropriate implementation at runtime
 * (in-memory for tests, IndexedDB / remote API for production).
 */
export interface StorageAdapter {
  // Cycles
  saveCycle(cycle: ReconciliationCycle): Promise<void>;
  loadCycle(cycleId: ID): Promise<ReconciliationCycle | null>;
  loadCyclesForFragment(fragmentId: ID): Promise<ReconciliationCycle[]>;
  loadAllCycles(principalId: ID): Promise<ReconciliationCycle[]>;

  // Active phase tracking
  saveActivePhase(fragmentId: ID, phase: ActivePhaseRecord): Promise<void>;
  loadActivePhase(fragmentId: ID): Promise<ActivePhaseRecord | null>;
  clearActivePhase(fragmentId: ID): Promise<void>;

  // Recurrence index
  saveRecurrenceRecord(record: RecurrenceRecord): Promise<void>;
  loadRecurrenceRecord(fragmentId: ID): Promise<RecurrenceRecord | null>;

  // Pattern index
  savePatternEntry(entry: PatternEntry): Promise<void>;
  loadPatternEntries(principalId: ID): Promise<PatternEntry[]>;
}

// ---------------------------------------------------------------------------
// 1. Internal record types
// ---------------------------------------------------------------------------

/** Tracks which phase a fragment is currently in, and since when. */
export interface ActivePhaseRecord {
  fragment_id:     ID;
  principal_id:    ID;
  current_phase:   ReconciliationPhase;
  cycle_id:        ID;
  entered_at:      ISOTimestamp;
  previous_phase:  ReconciliationPhase | null;
}

/**
 * Tracks how many times a fragment has re-entered the cycle
 * and what patterns emerged across attempts.
 */
export interface RecurrenceRecord {
  fragment_id:          ID;
  principal_id:         ID;
  total_cycles:         number;
  integrated_count:     number;     // cycles that ended INTEGRATED
  re_entry_count:       number;     // cycles that ended RE_ENTRY
  calling_count:        number;     // cycles that issued a CALLING
  last_cycle_id:        ID | null;
  last_integrated_at:   ISOTimestamp | null;
  first_detected_at:    ISOTimestamp;
  strategies_attempted: string[];   // ordered list of strategies tried
  dominant_domain:      Fragment['domain'] | null;
}

/**
 * A distilled pattern entry written when a cycle completes.
 * Feeds the IntegrityIndex and long-term coherence tracking.
 */
export interface PatternEntry {
  id:              ID;
  principal_id:    ID;
  fragment_id:     ID;
  cycle_id:        ID;
  domain:          Fragment['domain'];
  category:        string;          // DiagnosisCategory as string
  strategy_used:   string;          // BridgeStrategyName as string
  outcome:         'integrated' | 're_entry' | 'calling' | 'deferred';
  charge_at_open:  string;          // ChargeLevel as string
  charge_at_close: string | null;
  duration_hours:  number;
  recorded_at:     ISOTimestamp;
}

// ---------------------------------------------------------------------------
// 2. Cycle builder — assembles a ReconciliationCycle from phase outputs
// ---------------------------------------------------------------------------

/**
 * Mutable cycle-in-progress. The engine hands this to Memory at each phase
 * transition; Memory updates and stores it. Only Memory seals cycles.
 */
export interface CycleInProgress {
  cycle_id:        ID;
  principal_id:    ID;
  fragment:        Fragment;
  detected_at:     ISOTimestamp;
  diagnosis:       Diagnosis | null;
  bridge_result:   BridgeResult | null;
  verification:    VerificationResult | null;
  current_phase:   ReconciliationPhase;
  sealed:          boolean;
}

// ---------------------------------------------------------------------------
// 3. ReconciliationMemory class
// ---------------------------------------------------------------------------

export class ReconciliationMemory {
  private readonly store: StorageAdapter;

  // In-memory cache of active cycles — avoids redundant adapter reads
  // during a single engine run. Cleared when a cycle is sealed.
  private readonly _activeCache = new Map<ID, CycleInProgress>();

  constructor(store: StorageAdapter) {
    this.store = store;
  }

  // =========================================================================
  // CYCLE LIFECYCLE
  // =========================================================================

  /**
   * Open a new cycle for a fragment.
   * Called by the engine at the start of DETECT.
   * Returns the new cycle_id.
   */
  async openCycle(
    principalId: ID,
    fragment:    Fragment,
  ): Promise<ID> {
    const cycleId  = generateId();
    const now      = nowISO();

    const inProgress: CycleInProgress = {
      cycle_id:      cycleId,
      principal_id:  principalId,
      fragment,
      detected_at:   now,
      diagnosis:     null,
      bridge_result: null,
      verification:  null,
      current_phase: 'DETECT',
      sealed:        false,
    };

    this._activeCache.set(fragment.id, inProgress);

    await this.store.saveActivePhase(fragment.id, {
      fragment_id:    fragment.id,
      principal_id:   principalId,
      current_phase:  'DETECT',
      cycle_id:       cycleId,
      entered_at:     now,
      previous_phase: null,
    });

    return cycleId;
  }

  /**
   * Advance the cycle to the next phase, recording the phase output.
   * The engine calls this after each phase completes.
   */
  async advancePhase(
    fragmentId:   ID,
    nextPhase:    ReconciliationPhase,
    phaseOutput:  Diagnosis | BridgeResult | VerificationResult | null,
  ): Promise<void> {
    const cycle = this._requireActive(fragmentId);

    // Store the phase output in the correct slot
    if (isdiagnosis(phaseOutput))    cycle.diagnosis      = phaseOutput;
    if (isBridgeResult(phaseOutput)) cycle.bridge_result  = phaseOutput;
    if (isVerification(phaseOutput)) cycle.verification   = phaseOutput;

    const previousPhase   = cycle.current_phase;
    cycle.current_phase   = nextPhase;

    await this.store.saveActivePhase(fragmentId, {
      fragment_id:    fragmentId,
      principal_id:   cycle.principal_id,
      current_phase:  nextPhase,
      cycle_id:       cycle.cycle_id,
      entered_at:     nowISO(),
      previous_phase: previousPhase,
    });
  }

  /**
   * Seal the current cycle for a fragment.
   * Called by the engine when the cycle reaches a terminal state:
   *   - VerificationResult.status === 'INTEGRATED'
   *   - VerificationResult.status === 'RE_ENTRY'  (before re-opening)
   *   - BridgeResult.strategy === 'calling_escalation'
   *   - BridgeResult.strategy === 'slow_witness'  (held indefinitely)
   *
   * Returns the sealed ReconciliationCycle.
   */
  async sealCycle(
    fragmentId: ID,
    outcome:    PatternEntry['outcome'],
  ): Promise<ReconciliationCycle> {
    const cycle = this._requireActive(fragmentId);
    cycle.sealed = true;

    const now         = nowISO();
    const durationHrs = hoursSince(cycle.detected_at);

    const sealed: ReconciliationCycle = {
      id:              cycle.cycle_id,
      principal_id:    cycle.principal_id,
      fragment_id:     fragmentId,
      fragment_label:  cycle.fragment.label,
      domain:          cycle.fragment.domain,
      opened_at:       cycle.detected_at,
      sealed_at:       now,
      duration_hours:  durationHrs,
      diagnosis:       cycle.diagnosis,
      bridge_result:   cycle.bridge_result,
      verification:    cycle.verification,
      outcome,
      charge_at_open:  cycle.fragment.charge,
      charge_at_close: cycle.verification
        ? (cycle.fragment.charge)  // engine updates fragment charge before sealing
        : null,
    };

    // Persist
    await this.store.saveCycle(sealed);
    await this.store.clearActivePhase(fragmentId);
    this._activeCache.delete(fragmentId);

    // Update recurrence record
    await this._updateRecurrence(cycle.principal_id, fragmentId, cycle, outcome);

    // Write pattern entry
    await this._writePatternEntry(cycle, sealed, outcome);

    return sealed;
  }

  // =========================================================================
  // QUERIES
  // =========================================================================

  /** Returns all cycles for a fragment, ordered oldest-first. */
  async cyclesForFragment(fragmentId: ID): Promise<ReconciliationCycle[]> {
    const cycles = await this.store.loadCyclesForFragment(fragmentId);
    return cycles.sort((a, b) =>
      new Date(a.opened_at).getTime() - new Date(b.opened_at).getTime(),
    );
  }

  /** Returns the recurrence record for a fragment (null if first cycle). */
  async recurrenceFor(fragmentId: ID): Promise<RecurrenceRecord | null> {
    return this.store.loadRecurrenceRecord(fragmentId);
  }

  /** Returns the current active phase for a fragment (null if no open cycle). */
  async activePhaseFor(fragmentId: ID): Promise<ActivePhaseRecord | null> {
    const cached = this._activeCache.get(fragmentId);
    if (cached) {
      return {
        fragment_id:    fragmentId,
        principal_id:   cached.principal_id,
        current_phase:  cached.current_phase,
        cycle_id:       cached.cycle_id,
        entered_at:     nowISO(),
        previous_phase: null,
      };
    }
    return this.store.loadActivePhase(fragmentId);
  }

  /**
   * Returns all pattern entries for a principal, ordered by recency.
   * Used by IntegrityIndex to compute coherence scores and trend lines.
   */
  async patternEntriesFor(principalId: ID): Promise<PatternEntry[]> {
    const entries = await this.store.loadPatternEntries(principalId);
    return entries.sort((a, b) =>
      new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime(),
    );
  }

  /**
   * Returns a summary of recurrence across all fragments for a principal.
   * Used by IntegrityIndex for global coherence assessment.
   */
  async recurrenceSummary(principalId: ID): Promise<RecurrenceSummary> {
    const cycles   = await this.store.loadAllCycles(principalId);
    const patterns = await this.store.loadPatternEntries(principalId);

    const totalCycles       = cycles.length;
    const integratedCycles  = cycles.filter(c => c.outcome === 'integrated').length;
    const reEntryCycles     = cycles.filter(c => c.outcome === 're_entry').length;
    const callingCycles     = cycles.filter(c => c.outcome === 'calling').length;
    const integrationRate   = totalCycles > 0 ? integratedCycles / totalCycles : 0;

    // Most common fragment domains in RE_ENTRY
    const domainCounts = { system: 0, psyche: 0, relational: 0 };
    cycles
      .filter(c => c.outcome === 're_entry')
      .forEach(c => { domainCounts[c.domain]++; });

    const dominantReEntryDomain = (Object.entries(domainCounts)
      .sort((a, b) => b[1] - a[1])[0]?.[0] ?? null) as Fragment['domain'] | null;

    // Longest unresolved streaks
    const streaks = this._computeUnresolvedStreaks(cycles);

    // Most frequently recurring categories
    const categoryCounts = new Map<string, number>();
    patterns.forEach(p => {
      categoryCounts.set(p.category, (categoryCounts.get(p.category) ?? 0) + 1);
    });
    const topCategories = [...categoryCounts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([category, count]) => ({ category, count }));

    return {
      principal_id:           principalId,
      total_cycles:           totalCycles,
      integrated_cycles:      integratedCycles,
      re_entry_cycles:        reEntryCycles,
      calling_cycles:         callingCycles,
      integration_rate:       integrationRate,
      dominant_re_entry_domain: dominantReEntryDomain,
      top_recurring_categories: topCategories,
      longest_unresolved_streaks: streaks,
      computed_at:            nowISO(),
    };
  }

  // =========================================================================
  // INTERNAL — recurrence + pattern tracking
  // =========================================================================

  private async _updateRecurrence(
    principalId: ID,
    fragmentId:  ID,
    cycle:       CycleInProgress,
    outcome:     PatternEntry['outcome'],
  ): Promise<void> {
    const existing = await this.store.loadRecurrenceRecord(fragmentId);
    const strategy = cycle.bridge_result?.strategy ?? 'none';

    const updated: RecurrenceRecord = existing
      ? {
          ...existing,
          total_cycles:         existing.total_cycles + 1,
          integrated_count:     existing.integrated_count + (outcome === 'integrated' ? 1 : 0),
          re_entry_count:       existing.re_entry_count   + (outcome === 're_entry'   ? 1 : 0),
          calling_count:        existing.calling_count    + (outcome === 'calling'    ? 1 : 0),
          last_cycle_id:        cycle.cycle_id,
          last_integrated_at:   outcome === 'integrated' ? nowISO() : existing.last_integrated_at,
          strategies_attempted: [...existing.strategies_attempted, strategy],
        }
      : {
          fragment_id:          fragmentId,
          principal_id:         principalId,
          total_cycles:         1,
          integrated_count:     outcome === 'integrated' ? 1 : 0,
          re_entry_count:       outcome === 're_entry'   ? 1 : 0,
          calling_count:        outcome === 'calling'    ? 1 : 0,
          last_cycle_id:        cycle.cycle_id,
          last_integrated_at:   outcome === 'integrated' ? nowISO() : null,
          first_detected_at:    cycle.detected_at,
          strategies_attempted: [strategy],
          dominant_domain:      cycle.fragment.domain,
        };

    await this.store.saveRecurrenceRecord(updated);
  }

  private async _writePatternEntry(
    cycle:  CycleInProgress,
    sealed: ReconciliationCycle,
    outcome: PatternEntry['outcome'],
  ): Promise<void> {
    const entry: PatternEntry = {
      id:              generateId(),
      principal_id:    cycle.principal_id,
      fragment_id:     cycle.fragment.id,
      cycle_id:        cycle.cycle_id,
      domain:          cycle.fragment.domain,
      category:        cycle.diagnosis?.category ?? 'unknown',
      strategy_used:   cycle.bridge_result?.strategy ?? 'none',
      outcome,
      charge_at_open:  sealed.charge_at_open,
      charge_at_close: sealed.charge_at_close,
      duration_hours:  sealed.duration_hours,
      recorded_at:     nowISO(),
    };
    await this.store.savePatternEntry(entry);
  }

  /**
   * Computes the top 3 longest unresolved fragment streaks:
   * fragments with the most consecutive RE_ENTRY outcomes.
   */
  private _computeUnresolvedStreaks(
    cycles: ReconciliationCycle[],
  ): UnresolvedStreak[] {
    // Group cycles by fragment_id, order by opened_at
    const byFragment = new Map<ID, ReconciliationCycle[]>();
    cycles.forEach(c => {
      if (!byFragment.has(c.fragment_id)) byFragment.set(c.fragment_id, []);
      byFragment.get(c.fragment_id)!.push(c);
    });

    const streaks: UnresolvedStreak[] = [];

    byFragment.forEach((fCycles, fragmentId) => {
      const sorted = fCycles.sort((a, b) =>
        new Date(a.opened_at).getTime() - new Date(b.opened_at).getTime(),
      );

      // Count consecutive trailing re_entry outcomes
      let streak = 0;
      for (let i = sorted.length - 1; i >= 0; i--) {
        if (sorted[i].outcome === 're_entry') streak++;
        else break;
      }

      if (streak > 0) {
        streaks.push({
          fragment_id:    fragmentId,
          fragment_label: sorted[0].fragment_label,
          domain:         sorted[0].domain,
          consecutive_re_entries: streak,
          first_re_entry_at: sorted[sorted.length - streak].opened_at,
        });
      }
    });

    return streaks
      .sort((a, b) => b.consecutive_re_entries - a.consecutive_re_entries)
      .slice(0, 3);
  }

  // =========================================================================
  // INTERNAL — cache helpers
  // =========================================================================

  private _requireActive(fragmentId: ID): CycleInProgress {
    const cycle = this._activeCache.get(fragmentId);
    if (!cycle) {
      throw new Error(
        `ReconciliationMemory: no active cycle for fragment '${fragmentId}'. ` +
        `Call openCycle() before advancing or sealing.`,
      );
    }
    if (cycle.sealed) {
      throw new Error(
        `ReconciliationMemory: cycle for fragment '${fragmentId}' is already sealed.`,
      );
    }
    return cycle;
  }
}

// ---------------------------------------------------------------------------
// 4. Summary type
// ---------------------------------------------------------------------------

export interface RecurrenceSummary {
  principal_id:               ID;
  total_cycles:               number;
  integrated_cycles:          number;
  re_entry_cycles:            number;
  calling_cycles:             number;
  integration_rate:           number;   // integrated / total
  dominant_re_entry_domain:   Fragment['domain'] | null;
  top_recurring_categories:   Array<{ category: string; count: number }>;
  longest_unresolved_streaks: UnresolvedStreak[];
  computed_at:                ISOTimestamp;
}

export interface UnresolvedStreak {
  fragment_id:             ID;
  fragment_label:          string;
  domain:                  Fragment['domain'];
  consecutive_re_entries:  number;
  first_re_entry_at:       ISOTimestamp;
}

// ---------------------------------------------------------------------------
// 5. In-memory StorageAdapter — for tests and local development
// ---------------------------------------------------------------------------

/**
 * A fully in-memory StorageAdapter.
 * Zero dependencies. Safe for unit tests and sandboxed environments.
 * Data does not persist across process restarts.
 */
export class InMemoryStorageAdapter implements StorageAdapter {
  private _cycles        = new Map<ID, ReconciliationCycle>();
  private _byFragment    = new Map<ID, Set<ID>>();           // fragmentId → cycleIds
  private _byPrincipal   = new Map<ID, Set<ID>>();           // principalId → cycleIds
  private _activePhases  = new Map<ID, ActivePhaseRecord>();
  private _recurrence    = new Map<ID, RecurrenceRecord>();
  private _patterns      = new Map<ID, PatternEntry>();
  private _patternsByP   = new Map<ID, Set<ID>>();           // principalId → patternIds

  async saveCycle(cycle: ReconciliationCycle): Promise<void> {
    this._cycles.set(cycle.id, cycle);
    if (!this._byFragment.has(cycle.fragment_id))
      this._byFragment.set(cycle.fragment_id, new Set());
    this._byFragment.get(cycle.fragment_id)!.add(cycle.id);
    if (!this._byPrincipal.has(cycle.principal_id))
      this._byPrincipal.set(cycle.principal_id, new Set());
    this._byPrincipal.get(cycle.principal_id)!.add(cycle.id);
  }

  async loadCycle(cycleId: ID): Promise<ReconciliationCycle | null> {
    return this._cycles.get(cycleId) ?? null;
  }

  async loadCyclesForFragment(fragmentId: ID): Promise<ReconciliationCycle[]> {
    const ids = this._byFragment.get(fragmentId) ?? new Set();
    return [...ids].map(id => this._cycles.get(id)!).filter(Boolean);
  }

  async loadAllCycles(principalId: ID): Promise<ReconciliationCycle[]> {
    const ids = this._byPrincipal.get(principalId) ?? new Set();
    return [...ids].map(id => this._cycles.get(id)!).filter(Boolean);
  }

  async saveActivePhase(fragmentId: ID, phase: ActivePhaseRecord): Promise<void> {
    this._activePhases.set(fragmentId, phase);
  }

  async loadActivePhase(fragmentId: ID): Promise<ActivePhaseRecord | null> {
    return this._activePhases.get(fragmentId) ?? null;
  }

  async clearActivePhase(fragmentId: ID): Promise<void> {
    this._activePhases.delete(fragmentId);
  }

  async saveRecurrenceRecord(record: RecurrenceRecord): Promise<void> {
    this._recurrence.set(record.fragment_id, record);
  }

  async loadRecurrenceRecord(fragmentId: ID): Promise<RecurrenceRecord | null> {
    return this._recurrence.get(fragmentId) ?? null;
  }

  async savePatternEntry(entry: PatternEntry): Promise<void> {
    this._patterns.set(entry.id, entry);
    if (!this._patternsByP.has(entry.principal_id))
      this._patternsByP.set(entry.principal_id, new Set());
    this._patternsByP.get(entry.principal_id)!.add(entry.id);
  }

  async loadPatternEntries(principalId: ID): Promise<PatternEntry[]> {
    const ids = this._patternsByP.get(principalId) ?? new Set();
    return [...ids].map(id => this._patterns.get(id)!).filter(Boolean);
  }

  /** Introspection helper for tests. */
  snapshot(): {
    cycles:       ReconciliationCycle[];
    activePhases: ActivePhaseRecord[];
    recurrence:   RecurrenceRecord[];
    patterns:     PatternEntry[];
  } {
    return {
      cycles:       [...this._cycles.values()],
      activePhases: [...this._activePhases.values()],
      recurrence:   [...this._recurrence.values()],
      patterns:     [...this._patterns.values()],
    };
  }
}

// ---------------------------------------------------------------------------
// 6. Internal helpers
// ---------------------------------------------------------------------------

function nowISO(): ISOTimestamp {
  return new Date().toISOString();
}

function hoursSince(iso: ISOTimestamp): number {
  return (Date.now() - new Date(iso).getTime()) / 3_600_000;
}

function generateId(): ID {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
}

// Type guards for phase output discrimination
function isdiagnosis(x: unknown): x is Diagnosis {
  return !!x && typeof x === 'object' && 'category' in x && 'confidence' in x;
}

function isBridgeResult(x: unknown): x is BridgeResult {
  return !!x && typeof x === 'object' && 'strategy' in x && 'success' in x;
}

function isVerification(x: unknown): x is VerificationResult {
  return !!x && typeof x === 'object' && 'status' in x && 'verdict' in x;
}

// ---------------------------------------------------------------------------
// 7. Exports
// ---------------------------------------------------------------------------

export default ReconciliationMemory;
