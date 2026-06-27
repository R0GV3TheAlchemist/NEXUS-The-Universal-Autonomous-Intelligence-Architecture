/**
 * WitnessProtocol.ts
 * Mandatory read-only observation layer in the ARFP reconciliation lifecycle.
 *
 * Position in the ARFP phase sequence:
 *   DETECT → DIAGNOSE → [WITNESS] → BRIDGE → INTEGRATE
 *
 * The WITNESS phase enforces a minimum observation period before any bridge
 * strategy is executed. Its purpose is to preserve the diagnostic signal
 * that a fragment carries — the information encoded in *why* it split.
 * Forcing closure without witnessing destroys that signal. The fragment
 * re-emerges, usually with higher charge.
 *
 * Design constraints:
 *   - No state mutation of the fragment occurs here.
 *   - No bridge action is initiated here.
 *   - WitnessRecord is append-only; observations accumulate.
 *   - The protocol reads; it does not touch.
 *
 * Canon layer : GAIA-OS Core — Integrity & Coherence Engine
 * Spec version : 1.0  (June 27 2026)
 * Depends on   : reconciliationTypes.ts
 */

import {
  type Fragment,
  type WitnessRecord,
  type ARFPConfig,
  type ISOTimestamp,
  type ID,
  type ChargeLevel,
  DEFAULT_ARFP_CONFIG,
  CHARGE_WEIGHTS,
} from './reconciliationTypes';

// ---------------------------------------------------------------------------
// 0. Types
// ---------------------------------------------------------------------------

/** Result returned by WitnessProtocol.open(). */
export interface WitnessOpenResult {
  record:           WitnessRecord;
  minimum_hours:    number;
  ready_at:         ISOTimestamp;   // earliest timestamp at which BRIDGE is permitted
}

/** Result returned by WitnessProtocol.observe(). */
export interface WitnessObserveResult {
  record:           WitnessRecord;
  complete:         boolean;        // true when minimum duration has elapsed
  remaining_hours:  number;         // 0 when complete
}

/** Result returned by WitnessProtocol.close(). */
export interface WitnessCloseResult {
  record:           WitnessRecord;
  duration_hours:   number;         // actual elapsed witness time
  minimum_met:      boolean;        // false = closed early; triggers slow_witness escalation
}

/**
 * Observation categories — structured tags on a witness observation.
 * Observations are logged as freeform strings but each is tagged
 * with a category to enable pattern detection across fragments.
 */
export type ObservationCategory =
  | 'charge_shift'       // charge level changed during observation
  | 'pattern_recurrence' // same signal appeared more than once
  | 'intensity_peak'     // signal intensity spiked within window
  | 'context_link'       // fragment visibly linked to an external event
  | 'somatic'            // bodily / felt-sense quality noted (psyche domain)
  | 'relational_echo'    // fragment mirrors a relational pattern (psyche/relational)
  | 'narrative'          // principal has offered meaning-making about the fragment
  | 'system_correlation' // system metric movement correlates with fragment
  | 'general';           // unclassified

/** A single structured observation entry within a WitnessRecord. */
export interface ObservationEntry {
  id:          ID;
  category:    ObservationCategory;
  content:     string;
  observed_at: ISOTimestamp;
  charge_at_observation: ChargeLevel;
}

/**
 * Extended WitnessRecord that includes the structured observation log.
 * The base WitnessRecord (from types) stores observations as strings
 * for minimal overhead; this extension is used by the full protocol.
 */
export interface WitnessSession extends WitnessRecord {
  observation_log: ObservationEntry[];
  charge_trajectory: ChargeLevel[];   // ordered list of charge levels observed
  slow_witness:    boolean;           // true = canary path; bridge deferred indefinitely
}

// ---------------------------------------------------------------------------
// 1. Duration computation
// ---------------------------------------------------------------------------

/**
 * Computes the minimum witness duration in hours for a given charge level.
 *
 * Formula: base_hours × charge_weight
 *   low:      1 × 1  =  1 hour
 *   medium:   1 × 2  =  2 hours
 *   high:     1 × 4  =  4 hours
 *   critical: 1 × 8  =  8 hours
 *
 * The base_hours value comes from ARFPConfig.witness_base_hours (default 1.0).
 * Adjust it per-principal for slower or faster cadences without touching
 * the charge multiplier logic.
 */
export function computeMinimumWitnessDuration(
  charge:    ChargeLevel,
  baseHours: number = DEFAULT_ARFP_CONFIG.witness_base_hours,
): number {
  return baseHours * CHARGE_WEIGHTS[charge];
}

/**
 * Returns the earliest ISOTimestamp at which a BRIDGE is permitted
 * given the witness start time and minimum duration.
 */
export function computeReadyAt(
  startedAt:    ISOTimestamp,
  minimumHours: number,
): ISOTimestamp {
  const readyMs = new Date(startedAt).getTime() + minimumHours * 3_600_000;
  return new Date(readyMs).toISOString();
}

/**
 * Returns elapsed hours since a given ISO timestamp.
 */
export function elapsedHours(since: ISOTimestamp): number {
  return (Date.now() - new Date(since).getTime()) / 3_600_000;
}

// ---------------------------------------------------------------------------
// 2. WitnessProtocol class
// ---------------------------------------------------------------------------

export class WitnessProtocol {
  private readonly config: ARFPConfig;

  /**
   * In-memory session store.
   * Key: fragment_id. One active session per fragment at a time.
   * Completed sessions are flushed to ReconciliationMemory by the engine.
   */
  private readonly sessions: Map<ID, WitnessSession> = new Map();

  constructor(config: Partial<ARFPConfig> = {}) {
    this.config = { ...DEFAULT_ARFP_CONFIG, ...config };
  }

  // -------------------------------------------------------------------------
  // 2a. open() — begin a witness session for a fragment
  // -------------------------------------------------------------------------

  /**
   * Opens a new WitnessSession for the given fragment.
   * Called by the ReconciliationEngine after DIAGNOSE completes.
   *
   * If a session already exists for this fragment_id (e.g. a recurring
   * fragment re-entering the WITNESS phase), the prior session is closed
   * and a new one opened. This preserves the charge_trajectory across
   * the recurrence via the observation_log.
   *
   * @param fragment  The fragment entering the WITNESS phase.
   * @param slowWitness  If true, no minimum duration is enforced — the
   *                    session remains open until the principal explicitly
   *                    closes it. Used for high-recurrence fragments.
   */
  open(fragment: Fragment, slowWitness = false): WitnessOpenResult {
    const now = new Date().toISOString();
    const minimumHours = slowWitness
      ? Infinity
      : computeMinimumWitnessDuration(fragment.charge, this.config.witness_base_hours);
    const readyAt = slowWitness
      ? 'INDEFINITE'
      : computeReadyAt(now, minimumHours);

    const session: WitnessSession = {
      // WitnessRecord fields
      fragment_id:            fragment.id,
      observed_charge:        fragment.charge,
      observed_phase:         'WITNESS',
      minimum_duration_hours: slowWitness ? Infinity : minimumHours,
      observations:           [],
      started_at:             now,
      completed_at:           null,
      witness_complete:       false,
      // WitnessSession extensions
      observation_log:        [],
      charge_trajectory:      [fragment.charge],
      slow_witness:           slowWitness,
    };

    this.sessions.set(fragment.id, session);

    return {
      record:        session,
      minimum_hours: minimumHours,
      ready_at:      readyAt,
    };
  }

  // -------------------------------------------------------------------------
  // 2b. observe() — log an observation and check completion
  // -------------------------------------------------------------------------

  /**
   * Logs a structured observation to the active session and checks
   * whether the minimum witness duration has elapsed.
   *
   * This is the core read-only action of the WITNESS phase.
   * observe() may be called:
   *   - On a scheduled polling interval (e.g. every 15 minutes)
   *   - When a relevant signal change is detected in the fragment's domain
   *   - When the principal offers a reflection about the fragment
   *
   * @param fragmentId  The fragment being witnessed.
   * @param content     Freeform observation text.
   * @param category    Structured category tag.
   * @param currentCharge  Current charge level of the fragment (may differ
   *                       from observed_charge if it has shifted).
   */
  observe(
    fragmentId:    ID,
    content:       string,
    category:      ObservationCategory = 'general',
    currentCharge: ChargeLevel | null  = null,
  ): WitnessObserveResult {
    const session = this._requireSession(fragmentId);
    const now     = new Date().toISOString();

    // Determine effective charge for this observation
    const charge = currentCharge ?? session.observed_charge;

    // Track charge shifts
    const lastCharge = session.charge_trajectory[session.charge_trajectory.length - 1];
    if (charge !== lastCharge) {
      session.charge_trajectory.push(charge);
      // If charge escalated, update the session's observed_charge
      if (CHARGE_WEIGHTS[charge] > CHARGE_WEIGHTS[session.observed_charge]) {
        session.observed_charge = charge;
        // Recalculate minimum duration if charge escalated and not slow_witness
        if (!session.slow_witness) {
          const newMinimum = computeMinimumWitnessDuration(
            charge,
            this.config.witness_base_hours,
          );
          // Extend if the new minimum exceeds the original
          if (newMinimum > session.minimum_duration_hours) {
            session.minimum_duration_hours = newMinimum;
          }
        }
      }
    }

    // Build observation entry
    const entry: ObservationEntry = {
      id:                    this._makeId(),
      category,
      content,
      observed_at:           now,
      charge_at_observation: charge,
    };

    session.observation_log.push(entry);
    session.observations.push(content); // keep base WitnessRecord in sync

    // Check completion
    const elapsed = elapsedHours(session.started_at);
    const complete =
      !session.slow_witness &&
      elapsed >= session.minimum_duration_hours &&
      session.observation_log.length >= 1; // at least one observation required

    if (complete && !session.witness_complete) {
      session.witness_complete = true;
    }

    const remaining = session.slow_witness
      ? Infinity
      : Math.max(0, session.minimum_duration_hours - elapsed);

    return {
      record:          session,
      complete,
      remaining_hours: remaining,
    };
  }

  // -------------------------------------------------------------------------
  // 2c. poll() — check completion without adding an observation
  // -------------------------------------------------------------------------

  /**
   * Checks whether the minimum duration has elapsed without logging
   * a new observation. Used by the engine's scheduled reconciliation
   * tick to determine whether a fragment is ready to advance to BRIDGE.
   */
  poll(fragmentId: ID): WitnessObserveResult {
    const session = this._requireSession(fragmentId);
    const elapsed = elapsedHours(session.started_at);

    const complete =
      !session.slow_witness &&
      elapsed >= session.minimum_duration_hours &&
      session.observation_log.length >= 1;

    if (complete && !session.witness_complete) {
      session.witness_complete = true;
    }

    return {
      record:          session,
      complete,
      remaining_hours: session.slow_witness
        ? Infinity
        : Math.max(0, session.minimum_duration_hours - elapsed),
    };
  }

  // -------------------------------------------------------------------------
  // 2d. close() — end a witness session
  // -------------------------------------------------------------------------

  /**
   * Closes the active witness session for a fragment.
   * Called by the ReconciliationEngine when advancing to BRIDGE.
   *
   * If the minimum duration has not been met, `minimum_met` is false.
   * The engine uses this signal to route the fragment to the
   * `slow_witness` bridge strategy rather than the diagnosed strategy,
   * preserving the witnessing intent.
   *
   * After close(), the session is removed from the in-memory store.
   * The engine is responsible for persisting the returned WitnessSession
   * to ReconciliationMemory before discarding the reference.
   */
  close(fragmentId: ID): WitnessCloseResult {
    const session      = this._requireSession(fragmentId);
    const now          = new Date().toISOString();
    const elapsed      = elapsedHours(session.started_at);
    const minimumMet   = session.slow_witness || elapsed >= session.minimum_duration_hours;

    session.completed_at    = now;
    session.witness_complete = minimumMet;

    this.sessions.delete(fragmentId);

    return {
      record:         session,
      duration_hours: elapsed,
      minimum_met:    minimumMet,
    };
  }

  // -------------------------------------------------------------------------
  // 2e. escalateToSlowWitness() — convert an active session to slow_witness
  // -------------------------------------------------------------------------

  /**
   * Converts an active session to slow_witness mode.
   * Called by the engine when:
   *   - Fragment recurrence_count exceeds config.recurrence_calling_threshold
   *   - A CALLING has been issued and the principal has not yet acknowledged
   *   - The fragment charge escalated to 'critical' during observation
   *     and the diagnosed strategy is insufficient
   *
   * slow_witness mode removes the minimum duration constraint and keeps
   * the fragment in WITNESS until the principal explicitly advances it.
   * The engine continues logging observations but will not auto-advance
   * to BRIDGE.
   */
  escalateToSlowWitness(fragmentId: ID): WitnessSession {
    const session = this._requireSession(fragmentId);
    session.slow_witness           = true;
    session.minimum_duration_hours = Infinity;
    session.witness_complete       = false;
    this._logSystemObservation(
      session,
      'Escalated to slow_witness mode. Bridge deferred until principal engagement.',
      'charge_shift',
    );
    return session;
  }

  // -------------------------------------------------------------------------
  // 2f. synthesise() — generate a witness summary for the BRIDGE phase
  // -------------------------------------------------------------------------

  /**
   * Produces a human-readable and machine-structured summary of the
   * witness session, passed to BridgeStrategies as context.
   *
   * The summary includes:
   *   - Charge trajectory (did it escalate or de-escalate during witnessing?)
   *   - Dominant observation categories (what patterns appeared most?)
   *   - Notable observations (highest-signal entries by category)
   *   - Slow witness flag
   */
  synthesise(fragmentId: ID): WitnessSummary {
    const session = this._requireSession(fragmentId);
    return buildWitnessSummary(session);
  }

  /**
   * Synthesises from a closed session (after close() has been called).
   * The engine calls this after closing a session before routing to BRIDGE.
   */
  synthesiseFromRecord(session: WitnessSession): WitnessSummary {
    return buildWitnessSummary(session);
  }

  // -------------------------------------------------------------------------
  // 2g. Query helpers
  // -------------------------------------------------------------------------

  /** Returns true if an active session exists for this fragment. */
  hasSession(fragmentId: ID): boolean {
    return this.sessions.has(fragmentId);
  }

  /** Returns the active session for a fragment, or null. */
  getSession(fragmentId: ID): WitnessSession | null {
    return this.sessions.get(fragmentId) ?? null;
  }

  /** Returns all active sessions (engine uses this for scheduled polls). */
  getAllSessions(): WitnessSession[] {
    return Array.from(this.sessions.values());
  }

  /** Returns sessions where minimum duration has elapsed and bridge is ready. */
  getReadySessions(): WitnessSession[] {
    return this.getAllSessions().filter(s => {
      if (s.slow_witness) return false;
      return elapsedHours(s.started_at) >= s.minimum_duration_hours
        && s.observation_log.length >= 1;
    });
  }

  // -------------------------------------------------------------------------
  // 3. Internal helpers
  // -------------------------------------------------------------------------

  private _requireSession(fragmentId: ID): WitnessSession {
    const session = this.sessions.get(fragmentId);
    if (!session) {
      throw new Error(
        `WitnessProtocol: no active session for fragment '${fragmentId}'. ` +
        `Call open() before observe(), poll(), or close().`,
      );
    }
    return session;
  }

  private _logSystemObservation(
    session:  WitnessSession,
    content:  string,
    category: ObservationCategory,
  ): void {
    const entry: ObservationEntry = {
      id:                    this._makeId(),
      category,
      content,
      observed_at:           new Date().toISOString(),
      charge_at_observation: session.observed_charge,
    };
    session.observation_log.push(entry);
    session.observations.push(content);
  }

  private _makeId(): ID {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = (Math.random() * 16) | 0;
      return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
    });
  }
}

// ---------------------------------------------------------------------------
// 4. WitnessSummary — output of synthesise()
// ---------------------------------------------------------------------------

export interface WitnessSummary {
  fragment_id:          ID;
  duration_hours:       number;
  charge_trajectory:    ChargeLevel[];
  charge_escalated:     boolean;   // true if final charge > initial charge
  charge_de_escalated:  boolean;   // true if final charge < initial charge
  charge_stable:        boolean;   // true if trajectory never changed
  dominant_categories:  ObservationCategory[];
  observation_count:    number;
  notable_observations: string[];  // top 3 by category signal strength
  slow_witness:         boolean;
  synthesis_at:         ISOTimestamp;
}

function buildWitnessSummary(session: WitnessSession): WitnessSummary {
  const trajectory    = session.charge_trajectory;
  const initial       = trajectory[0];
  const final_charge  = trajectory[trajectory.length - 1];
  const elapsed       = elapsedHours(session.started_at);

  // Category frequency map
  const categoryCount = new Map<ObservationCategory, number>();
  for (const entry of session.observation_log) {
    categoryCount.set(entry.category, (categoryCount.get(entry.category) ?? 0) + 1);
  }
  const dominantCategories = [...categoryCount.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([cat]) => cat);

  // Notable observations: one per dominant category
  const notable: string[] = [];
  for (const cat of dominantCategories) {
    const entry = session.observation_log.find(e => e.category === cat);
    if (entry) notable.push(entry.content);
  }

  return {
    fragment_id:          session.fragment_id,
    duration_hours:       elapsed,
    charge_trajectory:    trajectory,
    charge_escalated:     CHARGE_WEIGHTS[final_charge] > CHARGE_WEIGHTS[initial],
    charge_de_escalated:  CHARGE_WEIGHTS[final_charge] < CHARGE_WEIGHTS[initial],
    charge_stable:        trajectory.length === 1,
    dominant_categories:  dominantCategories,
    observation_count:    session.observation_log.length,
    notable_observations: notable,
    slow_witness:         session.slow_witness,
    synthesis_at:         new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// 5. Exports
// ---------------------------------------------------------------------------

export default WitnessProtocol;
