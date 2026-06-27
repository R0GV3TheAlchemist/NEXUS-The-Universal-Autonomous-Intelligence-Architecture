/**
 * ReconciliationEngine.ts
 * The central orchestrator of the GAIA-OS Integrity & Coherence Engine.
 * Wires all 9 reconciliation modules into a single, coherent run loop.
 *
 * Module dependency graph:
 *
 *   FragmentDetector ──▶ FragmentDiagnoser ──▶ BridgeStrategies
 *        │                                           │
 *        ▼                                           ▼
 *   WitnessProtocol                        IntegrationVerifier
 *        │                                           │
 *        └──────────────┬────────────────────────────┘
 *                       ▼
 *              ReconciliationMemory
 *                       │
 *              ┌────────┴─────────┐
 *              ▼                  ▼
 *        CallingIssuer      IntegrityIndex
 *                       │
 *                       ▼
 *                 EngineResult
 *
 * Run lifecycle:
 *   1. Detect active fragments (FragmentDetector)
 *   2. Witness each fragment (WitnessProtocol)
 *   3. Diagnose each fragment (FragmentDiagnoser)
 *   4. Select and apply bridge strategy (BridgeStrategies)
 *   5. Verify integration outcome (IntegrationVerifier)
 *   6. Seal cycle into memory (ReconciliationMemory)
 *   7. Issue or escalate CALLINGs (CallingIssuer)
 *   8. Tick CALLING escalation/expiry (CallingIssuer.tick)
 *   9. Compute IntegrityScore (IntegrityIndex)
 *
 * Architecture contract:
 *   - The engine never modifies inputs. All mutations go through adapters.
 *   - Each run is atomic per fragment. A failure on one fragment does not
 *     abort processing of other fragments. Errors are collected and returned.
 *   - The engine is stateless between runs. All state lives in adapters.
 *   - run() is safe to call concurrently for different principals.
 *     Do NOT call run() concurrently for the same principal.
 *
 * Canon layer : GAIA-OS Core — Integrity & Coherence Engine
 * Spec version : 1.0  (June 27 2026)
 * Depends on   : All 8 reconciliation modules.
 */

import {
  type Fragment,
  type ID,
  type ISOTimestamp,
  type SignalInput,
} from './reconciliationTypes';

import { FragmentDetector }     from './FragmentDetector';
import { WitnessProtocol }      from './WitnessProtocol';
import { FragmentDiagnoser }    from './FragmentDiagnoser';
import { BridgeStrategies }     from './BridgeStrategies';
import { IntegrationVerifier }  from './IntegrationVerifier';
import { ReconciliationMemory } from './ReconciliationMemory';
import { CallingIssuer }        from './CallingIssuer';
import { IntegrityIndex }       from './IntegrityIndex';

import type { WitnessRecord }        from './WitnessProtocol';
import type { DiagnosisResult }      from './FragmentDiagnoser';
import type { BridgeResult }         from './BridgeStrategies';
import type { VerificationResult }   from './IntegrationVerifier';
import type { CallingLevel }         from './CallingIssuer';
import type { IntegrityScore }       from './IntegrityIndex';

// ---------------------------------------------------------------------------
// 0. Engine result types
// ---------------------------------------------------------------------------

export type FragmentOutcome = 'integrated' | 're_entry' | 'calling' | 'error';

export interface FragmentRunResult {
  fragment_id:    ID;
  fragment_label: string;
  outcome:        FragmentOutcome;
  witness:        WitnessRecord | null;
  diagnosis:      DiagnosisResult | null;
  bridge:         BridgeResult | null;
  verification:   VerificationResult | null;
  calling_id:     ID | null;
  calling_level:  CallingLevel | null;
  error:          string | null;
  duration_ms:    number;
}

export interface EngineResult {
  principal_id:    ID;
  run_id:          ID;
  started_at:      ISOTimestamp;
  completed_at:    ISOTimestamp;
  duration_ms:     number;
  fragments_run:   number;
  integrated:      number;
  re_entries:      number;
  callings_issued: number;
  errors:          number;
  fragment_results: FragmentRunResult[];
  integrity_score: IntegrityScore;
  escalated_callings: ID[];
}

// ---------------------------------------------------------------------------
// 1. Engine configuration
// ---------------------------------------------------------------------------

export interface EngineConfig {
  /**
   * Maximum fragments to process per run.
   * Fragments are prioritised by charge (critical first).
   * Default: 20.
   */
  maxFragmentsPerRun?: number;

  /**
   * If true, the engine will issue a CALLING for any fragment that
   * re-enters without a CALLING already active.
   * Default: true.
   */
  autoIssueCallings?: boolean;

  /**
   * Minimum charge level that triggers a CALLING on first re-entry.
   * Fragments below this charge level receive additional bridge cycles
   * before a CALLING is issued.
   * Default: 'elevated'.
   */
  callingThresholdCharge?: Fragment['charge'];

  /**
   * How many re-entry cycles a fragment must accumulate before the
   * engine escalates its CALLING level.
   * Default: 3.
   */
  escalationAfterReEntries?: number;

  /**
   * Number of days of PatternEntry history to pass to IntegrityIndex.
   * Default: 90.
   */
  patternWindowDays?: number;
}

const ENGINE_DEFAULTS: Required<EngineConfig> = {
  maxFragmentsPerRun:       20,
  autoIssueCallings:        true,
  callingThresholdCharge:   'elevated',
  escalationAfterReEntries: 3,
  patternWindowDays:        90,
};

// ---------------------------------------------------------------------------
// 2. Module bundle type (constructor injection)
// ---------------------------------------------------------------------------

export interface EngineModules {
  detector:   FragmentDetector;
  witness:    WitnessProtocol;
  diagnoser:  FragmentDiagnoser;
  strategies: BridgeStrategies;
  verifier:   IntegrationVerifier;
  memory:     ReconciliationMemory;
  caller:     CallingIssuer;
  index:      IntegrityIndex;
}

// ---------------------------------------------------------------------------
// 3. ReconciliationEngine
// ---------------------------------------------------------------------------

export class ReconciliationEngine {
  private readonly mod: EngineModules;
  private readonly cfg: Required<EngineConfig>;

  constructor(modules: EngineModules, config: EngineConfig = {}) {
    this.mod = modules;
    this.cfg = { ...ENGINE_DEFAULTS, ...config };
  }

  // =========================================================================
  // PRIMARY ENTRY POINT
  // =========================================================================

  /**
   * Run a full reconciliation pass for a principal.
   *
   * @param principalId  The principal whose fragments are being reconciled.
   * @param signals      Raw signal inputs from the environment layer
   *                     (behaviour patterns, interaction data, system logs).
   *                     Passed to FragmentDetector to detect/update fragments.
   */
  async run(
    principalId: ID,
    signals:     SignalInput[],
  ): Promise<EngineResult> {
    const runId     = generateRunId();
    const startedAt = nowISO();
    const t0        = Date.now();

    // -----------------------------------------------------------------------
    // Step 1 — Detect active fragments
    // -----------------------------------------------------------------------
    const allFragments = await this.mod.detector.detect(principalId, signals);
    const fragments    = this._prioritise(allFragments).slice(
      0, this.cfg.maxFragmentsPerRun,
    );

    // -----------------------------------------------------------------------
    // Steps 2–6 — Process each fragment
    // -----------------------------------------------------------------------
    const fragmentResults: FragmentRunResult[] = [];
    for (const fragment of fragments) {
      const result = await this._processFragment(principalId, fragment);
      fragmentResults.push(result);
    }

    // -----------------------------------------------------------------------
    // Step 7/8 — CALLING tick (escalation + expiry)
    // -----------------------------------------------------------------------
    const escalated = await this.mod.caller.tick(principalId);

    // -----------------------------------------------------------------------
    // Step 9 — Compute IntegrityScore
    // -----------------------------------------------------------------------
    const recurrenceSummary = await this.mod.memory.recurrenceSummary(principalId);
    const callingSummary    = await this.mod.caller.summary(principalId);
    const patterns          = await this.mod.memory.recentPatterns(
      principalId,
      this.cfg.patternWindowDays,
    );

    const integrityScore = await this.mod.index.compute(
      principalId,
      allFragments,          // pass all fragments, not just the ones processed
      recurrenceSummary,
      callingSummary,
      patterns,
    );

    // -----------------------------------------------------------------------
    // Assemble result
    // -----------------------------------------------------------------------
    const completedAt = nowISO();
    return {
      principal_id:    principalId,
      run_id:          runId,
      started_at:      startedAt,
      completed_at:    completedAt,
      duration_ms:     Date.now() - t0,
      fragments_run:   fragmentResults.length,
      integrated:      fragmentResults.filter(r => r.outcome === 'integrated').length,
      re_entries:      fragmentResults.filter(r => r.outcome === 're_entry').length,
      callings_issued: fragmentResults.filter(r => r.outcome === 'calling').length,
      errors:          fragmentResults.filter(r => r.outcome === 'error').length,
      fragment_results: fragmentResults,
      integrity_score:  integrityScore,
      escalated_callings: escalated.map(c => c.id),
    };
  }

  // =========================================================================
  // PRINCIPAL ACTIONS (delegated to CallingIssuer)
  // =========================================================================

  /**
   * Acknowledge a CALLING on behalf of the principal.
   * Called by the UI layer when the principal taps "I hear this".
   */
  async acknowledge(callingId: ID, principalId: ID): Promise<void> {
    await this.mod.caller.acknowledge(callingId, principalId);
  }

  /**
   * Dismiss a non-CRITICAL CALLING on behalf of the principal.
   */
  async dismiss(callingId: ID): Promise<void> {
    await this.mod.caller.dismiss(callingId);
  }

  /**
   * Return the current IntegrityScore without running a full pass.
   * Uses the last saved snapshots + current active state.
   */
  async currentScore(principalId: ID): Promise<IntegrityScore> {
    const fragments        = await this.mod.detector.activeFragments(principalId);
    const recurrenceSummary = await this.mod.memory.recurrenceSummary(principalId);
    const callingSummary   = await this.mod.caller.summary(principalId);
    const patterns         = await this.mod.memory.recentPatterns(
      principalId,
      this.cfg.patternWindowDays,
    );
    return this.mod.index.compute(
      principalId, fragments, recurrenceSummary, callingSummary, patterns,
    );
  }

  // =========================================================================
  // FRAGMENT PROCESSING (internal)
  // =========================================================================

  private async _processFragment(
    principalId: ID,
    fragment:    Fragment,
  ): Promise<FragmentRunResult> {
    const t0 = Date.now();
    const base: Omit<FragmentRunResult, 'outcome' | 'duration_ms'> = {
      fragment_id:    fragment.id,
      fragment_label: fragment.label,
      witness:        null,
      diagnosis:      null,
      bridge:         null,
      verification:   null,
      calling_id:     null,
      calling_level:  null,
      error:          null,
    };

    try {
      // Step 2 — Witness
      const witness = await this.mod.witness.witness(fragment);

      // Step 3 — Diagnose
      const diagnosis = await this.mod.diagnoser.diagnose(fragment, witness);

      // Step 4 — Bridge strategy
      const recurrence = await this.mod.memory.recurrenceFor(
        principalId, fragment.id,
      );
      const bridge = await this.mod.strategies.apply(
        fragment, diagnosis, recurrence,
      );

      // Step 5 — Verify
      const verification = await this.mod.verifier.verify(
        fragment, bridge,
      );

      // Step 6 — Seal cycle
      this.mod.memory.openCycle(principalId, fragment.id);
      this.mod.memory.advancePhase(principalId, fragment.id, 'witness',   witness);
      this.mod.memory.advancePhase(principalId, fragment.id, 'diagnosis', diagnosis);
      this.mod.memory.advancePhase(principalId, fragment.id, 'bridge',    bridge);
      this.mod.memory.advancePhase(principalId, fragment.id, 'verify',    verification);
      await this.mod.memory.sealCycle(
        principalId, fragment.id, verification.outcome, bridge.strategy_used,
      );

      // Step 7 — CALLING decision
      let callingId: ID | null    = null;
      let callingLevel: CallingLevel | null = null;

      if (verification.outcome === 're_entry' && this.cfg.autoIssueCallings) {
        const shouldCall = this._shouldIssueCallling(fragment, recurrence);
        if (shouldCall) {
          const level    = this._callingLevel(fragment, recurrence);
          const calling  = await this.mod.caller.issue(
            principalId,
            fragment.id,
            fragment.label,
            fragment.domain,
            level,
            diagnosis.primary_tension,
            witness.witness_notes,
            recurrence?.re_entry_count ?? 0,
          );
          callingId    = calling.id;
          callingLevel = calling.level;
        }
      }

      const outcome: FragmentOutcome =
        verification.outcome === 'integrated' ? 'integrated' :
        callingId                             ? 'calling'    :
        're_entry';

      return {
        ...base,
        outcome,
        witness,
        diagnosis,
        bridge,
        verification,
        calling_id:    callingId,
        calling_level: callingLevel,
        duration_ms:   Date.now() - t0,
      };

    } catch (err: unknown) {
      return {
        ...base,
        outcome:     'error',
        error:       err instanceof Error ? err.message : String(err),
        duration_ms: Date.now() - t0,
      };
    }
  }

  // =========================================================================
  // INTERNAL HELPERS
  // =========================================================================

  /**
   * Sort fragments so the engine processes the most critical ones first.
   * Order: critical > severe > elevated > moderate > latent
   */
  private _prioritise(fragments: Fragment[]): Fragment[] {
    const order: Record<Fragment['charge'], number> = {
      critical: 0, severe: 1, elevated: 2, moderate: 3, latent: 4,
    };
    return [...fragments].sort(
      (a, b) => order[a.charge] - order[b.charge],
    );
  }

  /**
   * Decide whether the engine should issue a CALLING for a re-entering fragment.
   * Rules:
   *   1. Fragment charge must be >= callingThresholdCharge.
   *   2. No active CALLING already exists for this fragment (CallingIssuer
   *      deduplicates internally, but we avoid an unnecessary call).
   */
  private _shouldIssueCallling(
    fragment:   Fragment,
    recurrence: Awaited<ReturnType<ReconciliationMemory['recurrenceFor']>>,
  ): boolean {
    const chargeOrder: Record<Fragment['charge'], number> = {
      latent: 0, moderate: 1, elevated: 2, severe: 3, critical: 4,
    };
    const threshold = chargeOrder[this.cfg.callingThresholdCharge];
    return chargeOrder[fragment.charge] >= threshold;
  }

  /**
   * Map fragment charge and recurrence depth to an initial CALLING level.
   *
   * charge=critical                       → CRITICAL
   * charge=severe                         → SUMMONS
   * charge=elevated + re_entry >= 3       → SUMMONS
   * charge=elevated                       → PROMPT
   * charge=moderate + re_entry >= escalationAfterReEntries → PROMPT
   * default                               → NOTICE
   */
  private _callingLevel(
    fragment:   Fragment,
    recurrence: Awaited<ReturnType<ReconciliationMemory['recurrenceFor']>>,
  ): CallingLevel {
    const reEntries = recurrence?.re_entry_count ?? 0;
    const { charge } = fragment;

    if (charge === 'critical')  return 'CRITICAL';
    if (charge === 'severe')    return 'SUMMONS';
    if (charge === 'elevated' && reEntries >= this.cfg.escalationAfterReEntries)
      return 'SUMMONS';
    if (charge === 'elevated')  return 'PROMPT';
    if (charge === 'moderate' && reEntries >= this.cfg.escalationAfterReEntries)
      return 'PROMPT';
    return 'NOTICE';
  }
}

// ---------------------------------------------------------------------------
// 4. Factory — construct a fully-wired engine from adapter bundles
// ---------------------------------------------------------------------------

import type { FragmentStorageAdapter }     from './FragmentDetector';
import type { MemoryStorageAdapter }       from './ReconciliationMemory';
import type {
  CallingStorageAdapter,
  CallingDeliveryAdapter,
}                                          from './CallingIssuer';
import type { IndexStorageAdapter }        from './IntegrityIndex';
import type { EscalationConfig, ExpiryConfig } from './CallingIssuer';

export interface EngineAdapters {
  fragmentStore:  FragmentStorageAdapter;
  memoryStore:    MemoryStorageAdapter;
  callingStore:   CallingStorageAdapter;
  callingDelivery: CallingDeliveryAdapter;
  indexStore:     IndexStorageAdapter;
}

export interface EngineFactoryOptions {
  config?:     EngineConfig;
  escalation?: Partial<EscalationConfig>;
  expiry?:     Partial<ExpiryConfig>;
}

/**
 * Build a fully-wired ReconciliationEngine from adapter instances.
 * Use this in production. For tests, construct modules individually.
 */
export function createEngine(
  adapters: EngineAdapters,
  options:  EngineFactoryOptions = {},
): ReconciliationEngine {
  const detector   = new FragmentDetector(adapters.fragmentStore);
  const witness    = new WitnessProtocol();
  const diagnoser  = new FragmentDiagnoser();
  const strategies = new BridgeStrategies();
  const verifier   = new IntegrationVerifier();
  const memory     = new ReconciliationMemory(adapters.memoryStore);
  const caller     = new CallingIssuer(
    { store: adapters.callingStore, delivery: adapters.callingDelivery },
    { escalation: options.escalation, expiry: options.expiry },
  );
  const index      = new IntegrityIndex(adapters.indexStore);

  return new ReconciliationEngine(
    { detector, witness, diagnoser, strategies, verifier, memory, caller, index },
    options.config,
  );
}

// ---------------------------------------------------------------------------
// 5. In-memory engine factory (tests / development)
// ---------------------------------------------------------------------------

import { InMemoryFragmentStorage }  from './FragmentDetector';
import { InMemoryStorageAdapter }   from './ReconciliationMemory';
import { InMemoryCallingStorage }   from './CallingIssuer';
import { InMemoryIndexStorage }     from './IntegrityIndex';

/**
 * NoOp delivery adapter — discards all deliveries.
 * Useful for testing and server-side runs where UI delivery is not needed.
 */
export class NoOpDeliveryAdapter implements CallingDeliveryAdapter {
  async deliver()              { /* no-op */ }
  async deliverEscalation()   { /* no-op */ }
  async deliverAcknowledgement() { /* no-op */ }
}

/**
 * Create a fully in-memory engine for testing or local development.
 * Nothing is persisted to disk.
 */
export function createInMemoryEngine(
  config: EngineConfig = {},
): ReconciliationEngine {
  return createEngine(
    {
      fragmentStore:   new InMemoryFragmentStorage(),
      memoryStore:     new InMemoryStorageAdapter(),
      callingStore:    new InMemoryCallingStorage(),
      callingDelivery: new NoOpDeliveryAdapter(),
      indexStore:      new InMemoryIndexStorage(),
    },
    { config },
  );
}

// ---------------------------------------------------------------------------
// 6. Helpers
// ---------------------------------------------------------------------------

function nowISO(): ISOTimestamp {
  return new Date().toISOString();
}

function generateRunId(): ID {
  return `run-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
}

// ---------------------------------------------------------------------------
// 7. Exports
// ---------------------------------------------------------------------------

export default ReconciliationEngine;
