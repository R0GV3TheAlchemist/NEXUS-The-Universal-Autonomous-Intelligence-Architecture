// crystalStore.ts — GAIA Crystal State Store
// Vanilla external store (useSyncExternalStore-compatible).
// Canon: C90 — S.T.Q.I.O.S.
// See docs/SUPER_VS_MAGIC.md for physics-first grounding.

// ── Types ─────────────────────────────────────────────────────────────────

export type CrystalMode =
  | 'SOVEREIGN'
  | 'TRANSPARENT'
  | 'QUANTUM'
  | 'INTEGRATED'
  | 'ORACLE'
  | 'SENTINEL';

export interface CrystalStoreState {
  activeCrystal:     CrystalMode;
  previousCrystal:   CrystalMode | null;
  isTransitioning:   boolean;
  loveFilterScore:   number;   // 0.0 – 1.0
  entanglementDepth: number;   // 0.0 – 1.0
  emergencyStopped:  boolean;
}

// ── Constants ─────────────────────────────────────────────────────────────

export const CRYSTAL_ORDER: CrystalMode[] = [
  'SOVEREIGN',
  'TRANSPARENT',
  'QUANTUM',
  'INTEGRATED',
  'ORACLE',
];

export const CRYSTAL_LABELS: Record<CrystalMode, string> = {
  SOVEREIGN:   'Sovereign',
  TRANSPARENT: 'Transparent',
  QUANTUM:     'Quantum',
  INTEGRATED:  'Integrated',
  ORACLE:      'Oracle',
  SENTINEL:    'Sentinel',
};

export const CRYSTAL_DECLARATIONS: Record<CrystalMode, string> = {
  SOVEREIGN:   'I am whole. I act from my own centre.',
  TRANSPARENT: 'I am open. I receive without distortion.',
  QUANTUM:     'I hold all possibilities until the moment requires one.',
  INTEGRATED:  'All parts of me are present and working together.',
  ORACLE:      'I see clearly. I speak what is true.',
  SENTINEL:    'I protect what is sacred. No harm passes here.',
};

export const CRYSTAL_CSS_CLASS: Record<CrystalMode, string> = {
  SOVEREIGN:   'crystal--sovereign',
  TRANSPARENT: 'crystal--transparent',
  QUANTUM:     'crystal--quantum',
  INTEGRATED:  'crystal--integrated',
  ORACLE:      'crystal--oracle',
  SENTINEL:    'crystal--sentinel',
};

// ── Initial state ─────────────────────────────────────────────────────────

const INITIAL_STATE: CrystalStoreState = {
  activeCrystal:     'SOVEREIGN',
  previousCrystal:   null,
  isTransitioning:   false,
  loveFilterScore:   0.5,
  entanglementDepth: 0.0,
  emergencyStopped:  false,
};

// ── Vanilla external store ─────────────────────────────────────────────────
// Compatible with React.useSyncExternalStore.

function createCrystalStore() {
  let state: CrystalStoreState = { ...INITIAL_STATE };
  const listeners = new Set<() => void>();

  function notify() {
    listeners.forEach((l) => l());
  }

  function setState(partial: Partial<CrystalStoreState>) {
    state = { ...state, ...partial };
    notify();
  }

  return {
    subscribe(listener: () => void): () => void {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },

    getSnapshot(): CrystalStoreState {
      return state;
    },

    setCrystal(mode: CrystalMode) {
      if (state.emergencyStopped) return;
      setState({
        previousCrystal: state.activeCrystal,
        activeCrystal:   mode,
        isTransitioning: true,
      });
    },

    setTransitioning(value: boolean) {
      setState({ isTransitioning: value });
    },

    returnToSovereign() {
      setState({
        previousCrystal: state.activeCrystal,
        activeCrystal:   'SOVEREIGN',
        isTransitioning: true,
        emergencyStopped: false,
      });
    },

    triggerEmergencyStop() {
      setState({
        emergencyStopped: true,
        isTransitioning:  false,
      });
    },

    setLoveFilterScore(score: number) {
      setState({ loveFilterScore: Math.max(0, Math.min(1, score)) });
    },

    setEntanglementDepth(depth: number) {
      setState({ entanglementDepth: Math.max(0, Math.min(1, depth)) });
    },

    reset() {
      setState({ ...INITIAL_STATE });
    },
  };
}

export const crystalStore = createCrystalStore();
