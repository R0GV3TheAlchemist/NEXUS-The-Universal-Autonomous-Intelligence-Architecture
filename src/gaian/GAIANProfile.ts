/**
 * GAIANProfile.ts — Persistent Identity Layer for the GAIAN Console
 *
 * M1: Core Runtime Identity (Issue #756)
 * M2: LCI Live Computation — updateLCIBaseline() (Issue #756)
 * ADR: docs/adr/FE/ADR-FE-004-state-management.md
 *
 * State hierarchy:
 *   Tauri Store (persistent, across sessions)
 *     └── GAIANProfile (loaded at sessionInit, saved at session end)
 *           └── RuntimeContext (ephemeral, per-session)
 *
 * Migration note: runtimetypes.py in src/gaian/ is misplaced per ADR-FE-001.
 * Python type definitions belong in core/. Migration tracked in issue #756.
 */

import { Store } from '@tauri-apps/plugin-store';

// ─── Crystal Resonance ────────────────────────────────────────────────────────

/** The 9 crystals available in the Meta Control Console (ADR-FE-006). */
export type CrystalResonance =
  | 'amethyst'          // Violet spectral force — default at birth
  | 'clear-quartz'      // Full-spectrum clarity
  | 'citrine'           // Solar / generative
  | 'obsidian'          // Protection / grounding
  | 'labradorite'       // Transformation / liminal
  | 'rose-quartz'       // Heart / coherence
  | 'selenite'          // Crown / access
  | 'black-tourmaline'  // Containment / shielding
  | 'lapis-lazuli';     // Truth / sovereignty

// ─── Module Types ─────────────────────────────────────────────────────────────

/** Ability Selection categories from the MCC (ADR-FE-006). */
export type GAIANModuleCategory = 'core' | 'mission' | 'emergency' | 'experimental';

export interface GAIANModule {
  id:          string;
  name:        string;
  category:    GAIANModuleCategory;
  active:      boolean;
  activatedAt: string | null;  // ISO 8601, null if never activated
}

// ─── LCI Trend ────────────────────────────────────────────────────────────────

/**
 * The trend direction of the Luminous Coherence Index over the session.
 * 'volatile' triggers Recovery Mode in the MCC (ADR-FE-006).
 */
export type LCITrend = 'rising' | 'stable' | 'falling' | 'volatile';

// ─── Constitutional Layer ─────────────────────────────────────────────────────

/**
 * World Service Mode — routes all power invocations through an intent filter.
 * IMPORTANT: The Ethical Guardrail is always active. It cannot be set to false
 * through any user action. Any code attempting to set ethicalGuardrailActive = false
 * must be rejected at PR review. (ADR-FE-006)
 */
export type ServiceMode = 'healing' | 'protection' | 'clarity' | 'balance';

export interface ConstitutionalLayer {
  readonly ethicalGuardrailActive: true;   // Hard constraint. Always true. Never configurable.
  activationLocked:    boolean;             // Sigil Lock ON/OFF
  serviceMode:         ServiceMode;         // World Service Mode
  humanModeActive:     boolean;             // Human Mode toggle
  superhumanModeReady: boolean;             // Superhuman Mode readiness (not active until phi threshold)
  sequenceLockActive:  boolean;             // Sequence Lock — init cannot be interrupted
  fullAccessActive:    boolean;             // All registered modules available
  experimentalAccess:  boolean;             // Experimental modules available
}

// ─── LCI History Entry ────────────────────────────────────────────────────────

export interface LCIHistoryEntry {
  phi:       number;    // LCI value at this point, 0.0–1.0
  timestamp: string;    // ISO 8601
  sessionId: string;
}

// ─── GAIANProfile ─────────────────────────────────────────────────────────────

/**
 * The complete persistent identity of a GAIAN architect.
 * Created once at birth (GaianBirth.ts) and loaded at every subsequent sessionInit.
 */
export interface GAIANProfile {
  // Identity (from GaianBirthResult)
  architectId:         string;      // Unique identifier (birth result id)
  name:                string;      // GAIAN name
  slug:                string;      // URL-safe identifier
  baseFormId:          string;      // Base Form chosen at birth
  avatarColor:         string;      // Hex color
  avatarStyle:         string;
  jungianRole:         string;      // Jungian archetype
  pronouns:            string;
  did:                 string;      // Decentralized identifier
  firstWords:          string;      // What the architect said at birth
  bornAt:              string;      // ISO 8601 birth timestamp

  // LCI state
  lciBaseline:         number;      // Architect's baseline phi (0.0–1.0)
  lciHistory:          LCIHistoryEntry[];
  lciTrend:            LCITrend;

  // Crystal state
  preferredCrystal:    CrystalResonance;   // Active crystal (Amethyst at birth)

  // Module state
  activeModules:       GAIANModule[];

  // Constitutional layer
  constitutional:      ConstitutionalLayer;

  // Session metadata
  lastSessionId:       string | null;
  lastSessionAt:       string | null;      // ISO 8601
  totalSessions:       number;

  // Profile version (for future migrations)
  profileVersion:      number;             // Increment when shape changes. Current: 1.
}

// ─── Profile Factory ──────────────────────────────────────────────────────────

/**
 * Creates a new GAIANProfile from a GaianBirthResult.
 * Called once at birth. Never called again for the same architectId.
 */
export function createProfileFromBirth(birth: {
  id:            string;
  name:          string;
  slug:          string;
  base_form_id:  string;
  avatar_color:  string;
  avatar_style:  string;
  jungian_role:  string;
  pronouns:      string;
  did:           string;
  first_words:   string;
  born_at:       string;
}): GAIANProfile {
  return {
    architectId:      birth.id,
    name:             birth.name,
    slug:             birth.slug,
    baseFormId:       birth.base_form_id,
    avatarColor:      birth.avatar_color,
    avatarStyle:      birth.avatar_style,
    jungianRole:      birth.jungian_role,
    pronouns:         birth.pronouns,
    did:              birth.did,
    firstWords:       birth.first_words,
    bornAt:           birth.born_at,

    lciBaseline:      0.0,
    lciHistory:       [],
    lciTrend:         'stable',

    preferredCrystal: 'amethyst',   // Default crystal at birth per ADR-FE-006

    activeModules:    [],

    constitutional: {
      ethicalGuardrailActive: true,   // Always true. This is a type-enforced invariant.
      activationLocked:       true,   // Sigil locked until phi >= 0.30
      serviceMode:            'healing',
      humanModeActive:        true,
      superhumanModeReady:    false,
      sequenceLockActive:     true,
      fullAccessActive:       false,
      experimentalAccess:     false,
    },

    lastSessionId:   null,
    lastSessionAt:   null,
    totalSessions:   0,

    profileVersion:  1,
  };
}

// ─── GAIANProfileManager ──────────────────────────────────────────────────────

const PROFILE_STORE_NAME = 'gaian-profiles.dat';
const PROFILE_KEY_PREFIX  = 'profile:';

/**
 * Default rolling window size for lciBaseline computation.
 * Uses the last 10 LCI history entries to compute the baseline.
 */
const DEFAULT_BASELINE_WINDOW = 10;

/**
 * GAIANProfileManager
 *
 * Handles load, save, and update of GAIANProfile records via @tauri-apps/plugin-store.
 * All operations are offline-capable (ADR-FE-005) — the store is local.
 *
 * Usage:
 *   const manager = new GAIANProfileManager();
 *   const profile  = await manager.load(architectId);
 *   await manager.save(profile);
 */
export class GAIANProfileManager {
  private store: Store;

  constructor() {
    this.store = new Store(PROFILE_STORE_NAME);
  }

  /** Load a profile by architectId. Returns null if not found. */
  async load(architectId: string): Promise<GAIANProfile | null> {
    const key = `${PROFILE_KEY_PREFIX}${architectId}`;
    const raw = await this.store.get<GAIANProfile>(key);
    return raw ?? null;
  }

  /** Save (create or overwrite) a profile. */
  async save(profile: GAIANProfile): Promise<void> {
    const key = `${PROFILE_KEY_PREFIX}${profile.architectId}`;
    await this.store.set(key, profile);
    await this.store.save();
  }

  /**
   * Update a profile with a partial patch.
   * Note: ethicalGuardrailActive cannot be changed — the type enforces this.
   */
  async update(architectId: string, patch: Partial<Omit<GAIANProfile, 'architectId' | 'bornAt'>>): Promise<GAIANProfile | null> {
    const existing = await this.load(architectId);
    if (!existing) return null;
    const updated: GAIANProfile = {
      ...existing,
      ...patch,
      constitutional: {
        ...existing.constitutional,
        ...(patch.constitutional ?? {}),
        ethicalGuardrailActive: true,  // Invariant: cannot be overwritten.
      },
    };
    await this.save(updated);
    return updated;
  }

  /**
   * Record a session open event.
   * Called by GAIANRuntime.sessionInit() immediately after profile load.
   */
  async recordSessionOpen(architectId: string, sessionId: string, phi: number, timestamp: string): Promise<void> {
    const profile = await this.load(architectId);
    if (!profile) return;

    const lciEntry: LCIHistoryEntry = { phi, timestamp, sessionId };
    const newHistory = [...profile.lciHistory, lciEntry].slice(-100);  // Keep last 100 entries

    const trend = computeLCITrend(profile.lciHistory, phi);

    await this.save({
      ...profile,
      lastSessionId:  sessionId,
      lastSessionAt:  timestamp,
      totalSessions:  profile.totalSessions + 1,
      lciHistory:     newHistory,
      lciTrend:       trend,
      constitutional: {
        ...profile.constitutional,
        ethicalGuardrailActive: true,
        // Unlock Sigil if phi meets the 30% threshold (0.30)
        activationLocked: phi < 0.30,
        // Superhuman mode becomes ready at phi >= 0.72 (matches Akashic gate)
        superhumanModeReady: phi >= 0.72,
      },
    });
  }

  /**
   * updateLCIBaseline — M2: LCI Live Computation
   *
   * Recomputes lciBaseline as the rolling arithmetic mean of the last
   * `windowSize` entries in the provided LCI history, then writes it
   * back to the persisted profile.
   *
   * Call this at session close (after all LCI history entries for the
   * session have been appended) so the baseline reflects real usage.
   *
   * If history is empty, lciBaseline is left unchanged.
   * If history has fewer entries than windowSize, all entries are used.
   *
   * @param architectId  The architect whose profile to update.
   * @param entries      The full LCI history array (profile.lciHistory).
   * @param windowSize   Number of recent entries to average (default: 10).
   */
  async updateLCIBaseline(
    architectId: string,
    entries:     LCIHistoryEntry[],
    windowSize = DEFAULT_BASELINE_WINDOW,
  ): Promise<void> {
    if (entries.length === 0) return;

    const window = entries.slice(-Math.abs(windowSize));
    const mean   = window.reduce((sum, e) => sum + e.phi, 0) / window.length;
    const baseline = Math.max(0.0, Math.min(1.0, mean));

    const profile = await this.load(architectId);
    if (!profile) return;

    await this.save({
      ...profile,
      lciBaseline: baseline,
      constitutional: {
        ...profile.constitutional,
        ethicalGuardrailActive: true,  // Invariant
      },
    });
  }

  /** Returns the list of all stored architectIds. */
  async listArchitectIds(): Promise<string[]> {
    const keys = await this.store.keys();
    return keys
      .filter(k => k.startsWith(PROFILE_KEY_PREFIX))
      .map(k => k.slice(PROFILE_KEY_PREFIX.length));
  }

  /** Delete a profile. Irreversible. */
  async delete(architectId: string): Promise<void> {
    const key = `${PROFILE_KEY_PREFIX}${architectId}`;
    await this.store.delete(key);
    await this.store.save();
  }
}

// ─── LCI Trend Computation ────────────────────────────────────────────────────

/**
 * Computes the LCI trend from the last 5 history entries + the current phi.
 * 'volatile' is set when the last 3 entries show a standard deviation > 0.15.
 */
export function computeLCITrend(history: LCIHistoryEntry[], currentPhi: number): LCITrend {
  const recent = [...history.slice(-4).map(h => h.phi), currentPhi];
  if (recent.length < 2) return 'stable';

  const mean = recent.reduce((a, b) => a + b, 0) / recent.length;
  const stdDev = Math.sqrt(
    recent.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / recent.length
  );

  if (stdDev > 0.15) return 'volatile';

  const last = recent[recent.length - 1];
  const first = recent[0];
  const delta = last - first;

  if (delta > 0.05) return 'rising';
  if (delta < -0.05) return 'falling';
  return 'stable';
}
