/**
 * metaphysical.data.ts
 * GAIA-OS Crystal Intelligence Engine — Metaphysical Reference Tables
 *
 * Provides three lookup structures used across the crystal layer:
 *
 *   GAIA_MODULES       — canonical module registry with metadata
 *   CHAKRA_MODULE_MAP  — maps each ChakraPoint to its primary GAIAModule
 *   ANGEL_NUMBER_MAP   — maps each AngelNumber to its GAIA module + name
 *
 * ─────────────────────────────────────────────────────────────────────────────
 */

import type { GAIAModule, AngelNumber } from './crystal.schema';
import { ChakraPoint }                  from './crystal.schema';

// ─────────────────────────────────────────────────────────────────────────────
// GAIA_MODULES
// ─────────────────────────────────────────────────────────────────────────────

export interface GAIAModuleDefinition {
  id:          GAIAModule;
  name:        string;
  description: string;
  chakra:      string;
  element:     string;
}

export const GAIA_MODULES: GAIAModuleDefinition[] = [
  {
    id:          'AnchorPrism',
    name:        'Anchor Prism',
    description: 'Grounding, stability, and protective anchoring of the physical plane.',
    chakra:      'Root',
    element:     'Earth',
  },
  {
    id:          'ViriditasHeart',
    name:        'Viriditas Heart',
    description: 'Heart-centred healing, growth, compassion, and natural resonance.',
    chakra:      'Heart',
    element:     'Water',
  },
  {
    id:          'SovereignCore',
    name:        'Sovereign Core',
    description: 'Personal power, will, solar confidence, and inner authority.',
    chakra:      'Solar Plexus',
    element:     'Fire',
  },
  {
    id:          'ClarusLens',
    name:        'Clarus Lens',
    description: 'Clarity, vision, insight, truth perception, and third-eye illumination.',
    chakra:      'Third Eye',
    element:     'Light',
  },
  {
    id:          'Noosphere',
    name:        'Noosphere',
    description: 'Mind, intellect, communication, and the collective field of thought.',
    chakra:      'Throat',
    element:     'Air',
  },
  {
    id:          'QuantumNexus',
    name:        'Quantum Nexus',
    description: 'Transformation, transmutation, alchemical change, and quantum bridging.',
    chakra:      'Sacral',
    element:     'Storm',
  },
  {
    id:          'SpiritusEngine',
    name:        'Spiritus Engine',
    description: 'Spiritual transcendence, crown connection, divine alignment, and cosmic awareness.',
    chakra:      'Crown',
    element:     'Aether',
  },
  {
    id:          'ChronoWeave',
    name:        'Chrono Weave',
    description: 'Time perception, akashic records, ancestral memory, and temporal weaving.',
    chakra:      'Soul Star',
    element:     'Akasha',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// CHAKRA_MODULE_MAP
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Maps each canonical ChakraPoint to its primary GAIAModule.
 * Used by crystal.validator.ts (check A3) to flag module/chakra mismatches.
 * Typed as Record<ChakraPoint, GAIAModule> so indexing by Chakra is safe
 * (use CHAKRA_MODULE_MAP[record.metaphysical.chakra_primary as ChakraPoint]).
 */
export const CHAKRA_MODULE_MAP: Record<string, GAIAModule> = {
  [ChakraPoint.Root]:        'AnchorPrism',
  [ChakraPoint.EarthStar]:   'AnchorPrism',
  [ChakraPoint.Sacral]:      'QuantumNexus',
  [ChakraPoint.SolarPlexus]: 'SovereignCore',
  [ChakraPoint.Heart]:       'ViriditasHeart',
  [ChakraPoint.Throat]:      'Noosphere',
  [ChakraPoint.ThirdEye]:    'ClarusLens',
  [ChakraPoint.Crown]:       'SpiritusEngine',
  [ChakraPoint.HigherCrown]: 'SpiritusEngine',
  [ChakraPoint.SoulStar]:    'ChronoWeave',
};

// ─────────────────────────────────────────────────────────────────────────────
// ANGEL_NUMBER_MAP
// ─────────────────────────────────────────────────────────────────────────────

export interface AngelNumberDefinition {
  number:      AngelNumber;
  name:        string;
  gaia_module: GAIAModule;
  meaning:     string;
}

/**
 * Maps each registered AngelNumber to its canonical GAIA definition.
 * Used by crystal.validator.ts (check B2) to verify module alignment.
 */
export const ANGEL_NUMBER_MAP: Map<AngelNumber, AngelNumberDefinition> = new Map([
  // Standard 1–9
  [1,   { number: 1,   name: 'Unity',        gaia_module: 'SovereignCore',  meaning: 'New beginnings, leadership, singular focus' }],
  [2,   { number: 2,   name: 'Duality',      gaia_module: 'ViriditasHeart', meaning: 'Balance, partnership, receptivity' }],
  [3,   { number: 3,   name: 'Trinity',      gaia_module: 'SpiritusEngine', meaning: 'Creativity, expression, divine trinity' }],
  [4,   { number: 4,   name: 'Foundation',   gaia_module: 'AnchorPrism',    meaning: 'Stability, structure, earthly order' }],
  [5,   { number: 5,   name: 'Change',       gaia_module: 'QuantumNexus',   meaning: 'Freedom, transformation, adventure' }],
  [6,   { number: 6,   name: 'Harmony',      gaia_module: 'ViriditasHeart', meaning: 'Love, family, nurturing, responsibility' }],
  [7,   { number: 7,   name: 'Mystery',      gaia_module: 'ClarusLens',     meaning: 'Spiritual wisdom, inner knowing, analysis' }],
  [8,   { number: 8,   name: 'Infinity',     gaia_module: 'SovereignCore',  meaning: 'Abundance, power, cosmic cycles' }],
  [9,   { number: 9,   name: 'Completion',   gaia_module: 'ChronoWeave',    meaning: 'Endings, humanitarian service, release' }],
  // Master numbers
  [11,  { number: 11,  name: 'Illumination', gaia_module: 'ClarusLens',     meaning: 'Spiritual awakening, intuition, master channel' }],
  [22,  { number: 22,  name: 'Master Builder',gaia_module: 'AnchorPrism',   meaning: 'Large-scale manifestation, practical idealism' }],
  [33,  { number: 33,  name: 'Master Teacher',gaia_module: 'SpiritusEngine',meaning: 'Compassionate guidance, divine instruction' }],
  // Sacred / extended
  [23,  { number: 23,  name: 'Royal Star',   gaia_module: 'SovereignCore',  meaning: 'Support from ascended masters, royal alignment' }],
  [44,  { number: 44,  name: 'Angelic Anchor',gaia_module: 'AnchorPrism',   meaning: 'Divine protection, heavenly stability' }],
  [55,  { number: 55,  name: 'Quantum Shift',gaia_module: 'QuantumNexus',   meaning: 'Accelerated change, double transformation' }],
  [66,  { number: 66,  name: 'Heart Matrix', gaia_module: 'ViriditasHeart', meaning: 'Amplified love, relational harmony' }],
  [77,  { number: 77,  name: 'Sacred Mirror',gaia_module: 'ClarusLens',     meaning: 'Reflection, deeper truth, mystical alignment' }],
  [88,  { number: 88,  name: 'Cosmic Law',   gaia_module: 'ChronoWeave',    meaning: 'Karmic balance, infinite cycles' }],
  [99,  { number: 99,  name: 'Universal End',gaia_module: 'ChronoWeave',    meaning: 'Global completion, collective release' }],
  // Sequences
  [111, { number: 111, name: 'Manifestation Gateway', gaia_module: 'SovereignCore',  meaning: 'Thoughts becoming reality, mind-gate open' }],
  [222, { number: 222, name: 'Divine Alignment',      gaia_module: 'ViriditasHeart', meaning: 'Trust, balance, relationships on track' }],
  [333, { number: 333, name: 'Ascended Presence',     gaia_module: 'SpiritusEngine', meaning: 'Masters nearby, creative expansion' }],
  [444, { number: 444, name: 'Angelic Protection',    gaia_module: 'AnchorPrism',    meaning: 'Angels surround you, stay grounded' }],
  [555, { number: 555, name: 'Major Transformation',  gaia_module: 'QuantumNexus',   meaning: 'Life-changing shifts accelerating' }],
  [666, { number: 666, name: 'Material Rebalance',    gaia_module: 'AnchorPrism',    meaning: 'Rebalance thoughts toward the spiritual' }],
  [777, { number: 777, name: 'Spiritual Jackpot',     gaia_module: 'ClarusLens',     meaning: 'Luck, miracles, divine reward' }],
  [888, { number: 888, name: 'Abundance Flow',        gaia_module: 'SovereignCore',  meaning: 'Financial/energetic abundance incoming' }],
  [999, { number: 999, name: 'Global Completion',     gaia_module: 'ChronoWeave',    meaning: 'Cycle ends, lightworker calling' }],
  // Special
  [1111,{ number: 1111,name: 'Portal Gateway',        gaia_module: 'SpiritusEngine', meaning: 'Dimensional gateway open, new timeline' }],
  [404, { number: 404, name: 'Stability Bridge',      gaia_module: 'AnchorPrism',    meaning: 'Grounding during uncertainty, bridge phase' }],
  [707, { number: 707, name: 'Mystic Mirror',         gaia_module: 'ClarusLens',     meaning: 'Spiritual truth revealed through reflection' }],
  [808, { number: 808, name: 'Karmic Infinity',       gaia_module: 'ChronoWeave',    meaning: 'Karmic cycles completing, infinite return' }],
  ['000',{number:'000',name: 'Void Cycle',            gaia_module: 'SpiritusEngine', meaning: 'New cycle begins from emptiness, void state' }],
]);
