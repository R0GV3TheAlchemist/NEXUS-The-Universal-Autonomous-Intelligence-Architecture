// C-OB01 — Onboarding Zustand Store v2
// Manages all onboarding state with persistence to onboarding_state.json
// via Tauri's fs API when available.
//
// Fixes:
//   #364 — Added camelCase alias getters `depth` and `intentOther` so Phase
//           components can read s.depth / s.intentOther without knowing the
//           snake_case field names. Source of truth remains depth_preference
//           and intent_other; aliases are derived at read time.
//   #365 — setIntent, setIntentOther, setDepthPreference, setSensitiveTopics,
//           and toggleConsent now call persistState() after writing. Previously
//           a force-quit after Phase 4 or Phase 5 would lose all answers.

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type {
  OnboardingState,
  OnboardingActions,
  OnboardingPhase,
  SystemCapabilities,
  UserIntent,
  DepthPreference,
  SensitiveTopic,
  ConsentPreferences,
} from '../types';

const DEFAULT_CONSENT: ConsentPreferences = {
  conversation_history: true,
  mood_signals: true,
  topic_patterns: true,
  usage_patterns: true,
  telemetry: false,
  cloud_backup: false,
};

const INITIAL_STATE: OnboardingState = {
  phase: 0,
  completed: false,
  interrupted: false,
  onboarding_version: '1.0',
  started_at: null,
  completed_at: null,
  system: null,
  name: '',
  intent: [],
  intent_other: '',
  depth_preference: 'reflective',
  sensitive_topics: [],
  consent: DEFAULT_CONSENT,
  account_created: false,
  account_email: null,
};

async function persistState(state: OnboardingState): Promise<void> {
  try {
    const { writeTextFile, BaseDirectory } = await import('@tauri-apps/plugin-fs');
    await writeTextFile(
      'onboarding_state.json',
      JSON.stringify(state, null, 2),
      { baseDir: BaseDirectory.AppData }
    );
  } catch {
    // Browser/non-Tauri environment — silently continue
  }
}

export async function loadPersistedState(): Promise<Partial<OnboardingState> | null> {
  try {
    const { readTextFile, exists, BaseDirectory } = await import('@tauri-apps/plugin-fs');
    const fileExists = await exists('onboarding_state.json', { baseDir: BaseDirectory.AppData });
    if (!fileExists) return null;
    const raw = await readTextFile('onboarding_state.json', { baseDir: BaseDirectory.AppData });
    return JSON.parse(raw) as Partial<OnboardingState>;
  } catch {
    return null;
  }
}

// ── Alias extensions ──────────────────────────────────────────────────────────
//
// Phase components read `s.depth` and `s.intentOther` (camelCase) for
// consistency with how `s.name`, `s.intent`, etc. are read. The store's
// canonical fields are `depth_preference` and `intent_other` (snake_case,
// matching the persisted JSON and the Rust command payload).
//
// These are added as plain fields on the store type that mirror the
// canonical values. They are kept in sync by the set* actions below.

export interface OnboardingAliases {
  /** Alias for `depth_preference`. Read-only mirror kept in sync by setDepthPreference. */
  depth: DepthPreference;
  /** Alias for `intent_other`. Read-only mirror kept in sync by setIntentOther. */
  intentOther: string;
}

export type OnboardingStore = OnboardingState & OnboardingActions & OnboardingAliases;

export const useOnboardingStore = create<OnboardingStore>()(
  subscribeWithSelector((set: (partial: Partial<OnboardingStore>) => void, get: () => OnboardingStore) => ({
    ...INITIAL_STATE,

    // ── Alias initial values (mirrors of INITIAL_STATE fields) ────────────────
    depth:       INITIAL_STATE.depth_preference,
    intentOther: INITIAL_STATE.intent_other,

    // ── Navigation ────────────────────────────────────────────────────────────

    setPhase: (phase: OnboardingPhase) => {
      set({ phase });
      persistState(get() as OnboardingState);
    },

    nextPhase: () => {
      const current = get().phase;
      const next = Math.min(current + 1, 8) as OnboardingPhase;
      set({ phase: next });
      persistState(get() as OnboardingState);
    },

    // ── System ────────────────────────────────────────────────────────────────

    setSystem: (system: SystemCapabilities) => {
      set({ system, started_at: new Date().toISOString() });
      // Not persisted: system caps are re-detected on every boot
    },

    // ── Phase 3 ───────────────────────────────────────────────────────────────

    setName: (name: string) => {
      set({ name });
      persistState(get() as OnboardingState);
    },

    // ── Phase 4 ───────────────────────────────────────────────────────────────
    //
    // FIX #365: All four Phase 4 actions now call persistState.
    // Previously a force-quit after completing Three Questions but before
    // Phase 7/8 would lose intent, depth, and sensitive topic selections.

    setIntent: (intent: UserIntent[]) => {
      set({ intent });
      persistState(get() as OnboardingState);
    },

    setIntentOther: (intent_other: string) => {
      // FIX #364: keep intentOther alias in sync
      set({ intent_other, intentOther: intent_other });
      persistState(get() as OnboardingState);
    },

    setDepthPreference: (depth_preference: DepthPreference) => {
      // FIX #364: keep depth alias in sync
      set({ depth_preference, depth: depth_preference });
      persistState(get() as OnboardingState);
    },

    setSensitiveTopics: (sensitive_topics: SensitiveTopic[]) => {
      set({ sensitive_topics });
      persistState(get() as OnboardingState);
    },

    // ── Phase 5 ───────────────────────────────────────────────────────────────
    //
    // FIX #365: toggleConsent now calls persistState.
    // Consent preferences are high-signal data; losing them on a crash
    // could cause features to boot in the wrong state.

    toggleConsent: (key: keyof ConsentPreferences) => {
      const current = get().consent;
      set({ consent: { ...current, [key]: !current[key] } });
      persistState(get() as OnboardingState);
    },

    // ── Phase 7 ───────────────────────────────────────────────────────────────

    setAccountCreated: (email: string) => {
      set({ account_created: true, account_email: email });
      persistState(get() as OnboardingState);
    },

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    completeOnboarding: () => {
      const completed_at = new Date().toISOString();
      set({ completed: true, interrupted: false, completed_at, phase: 8 });
      persistState(get() as OnboardingState);
      const state = get();
      seedSoulMirror(state as OnboardingState).catch(() => {});
    },

    resetOnboarding: () => {
      set({
        ...INITIAL_STATE,
        // Reset aliases too
        depth:       INITIAL_STATE.depth_preference,
        intentOther: INITIAL_STATE.intent_other,
      });
      persistState(get() as OnboardingState);
    },

    markInterrupted: () => {
      set({ interrupted: true });
      persistState(get() as OnboardingState);
    },

    resumeOnboarding: () => {
      set({ interrupted: false });
    },
  }))
);

// ── Soul Mirror seeding ───────────────────────────────────────────────────────
//
// Called by completeOnboarding(). Sends the full onboarding payload to the
// Rust `seed_soul_mirror` command. Tracked in issue #367.

async function seedSoulMirror(state: OnboardingState): Promise<void> {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('seed_soul_mirror', {
      responses: {
        name:              state.name,
        intent:            state.intent,
        intent_other:      state.intent_other,
        depth_preference:  state.depth_preference,
        sensitive_topics:  state.sensitive_topics,
        consent:           state.consent,
        completed_at:      state.completed_at,
      },
    });
  } catch {
    // Tauri command not yet implemented — tracked in issue #367
  }
}
