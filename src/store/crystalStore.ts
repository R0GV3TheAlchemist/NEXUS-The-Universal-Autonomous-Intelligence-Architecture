// crystalStore.ts — GAIA Crystal State Store
// Not crystals. Not unexplained behavior.
// Every state transition here is governed by coherence thresholds defined in canon/ELEMENTAL_SPECTRUM_MAP.md
// See docs/SUPER_VS_MAGIC.md for the physics-first grounding of this architecture.

import { create } from 'zustand';

export type CrystalState =
  | 'idle'
  | 'restorative'
  | 'focused'
  | 'alert'
  | 'overloaded'
  | 'recovery';

export interface CrystalStoreState {
  crystalState: CrystalState;
  coherenceScore: number; // 0.0 – 1.0
  setCrystalState: (state: CrystalState) => void;
  setCoherenceScore: (score: number) => void;
  reset: () => void;
}

const initialState = {
  crystalState: 'idle' as CrystalState,
  coherenceScore: 0.5,
};

export const useCrystalStore = create<CrystalStoreState>((set) => ({
  ...initialState,
  setCrystalState: (state) => set({ crystalState: state }),
  setCoherenceScore: (score) =>
    set({ coherenceScore: Math.max(0, Math.min(1, score)) }),
  reset: () => set(initialState),
}));
