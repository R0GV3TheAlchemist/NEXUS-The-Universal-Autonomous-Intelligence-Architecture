/**
 * GAIA Onboarding Store
 * Canon: GAIAN_TWIN_DOCTRINE, C17, SLOW_PROTOCOL
 *
 * Zustand store for onboarding state.
 * Persists to localStorage so the human can return
 * to exactly where they left off.
 */

import { create } from 'zustand';

export type OnboardingPhase = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export interface OnboardingData {
  name: string;
  // Three Questions answers
  questionWhat: string;   // "What brought you here?"
  questionCarry: string;  // "What are you carrying right now?"
  questionHope: string;   // "What do you hope for?"
  // Consent
  consentGiven: boolean;
  consentTimestamp: string;
  // Account
  email: string;
  // Session
  humanId: string;
  sessionId: string;
}

export interface OnboardingStore {
  phase: OnboardingPhase;
  completed: boolean;
  interrupted: boolean;
  startedAt: string | null;
  completedAt: string | null;
  data: Partial<OnboardingData>;

  // Actions
  setPhase: (phase: OnboardingPhase) => void;
  nextPhase: () => void;
  setData: (data: Partial<OnboardingData>) => void;
  markCompleted: () => void;
  markInterrupted: () => void;
  resumeOnboarding: () => void;
  resetOnboarding: () => void;
}

const STORAGE_KEY = 'gaia_onboarding_state';

function generateId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export const useOnboardingStore = create<OnboardingStore>((set, get) => ({
  phase: 0,
  completed: false,
  interrupted: false,
  startedAt: null,
  completedAt: null,
  data: {},

  setPhase: (phase) => {
    set({ phase });
    persistState(get());
  },

  nextPhase: () => {
    const current = get().phase;
    const next = Math.min(current + 1, 8) as OnboardingPhase;
    set({ phase: next });
    persistState(get());
  },

  setData: (data) => {
    set((s) => ({ data: { ...s.data, ...data } }));
    persistState(get());
  },

  markCompleted: () => {
    const now = new Date().toISOString();
    set({ completed: true, completedAt: now, phase: 8 });
    persistState(get());
  },

  markInterrupted: () => {
    set({ interrupted: true });
    persistState(get());
  },

  resumeOnboarding: () => {
    set({ interrupted: false });
  },

  resetOnboarding: () => {
    const now = new Date().toISOString();
    set({
      phase: 0,
      completed: false,
      interrupted: false,
      startedAt: now,
      completedAt: null,
      data: {
        humanId: generateId('human'),
        sessionId: generateId('session'),
      },
    });
    localStorage.removeItem(STORAGE_KEY);
  },
}));

function persistState(state: OnboardingStore): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      phase: state.phase,
      completed: state.completed,
      data: state.data,
      startedAt: state.startedAt,
    }));
  } catch { /* storage not available */ }
}

export async function loadPersistedState(): Promise<Partial<OnboardingStore> | null> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}
