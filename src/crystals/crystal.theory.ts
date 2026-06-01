/**
 * src/crystals/crystal.theory.ts
 * GAIA-OS Crystal Intelligence Engine — Theory / Reasoning Layer
 *
 * This module is the reasoning layer over the crystal database.
 * Where crystal.schema.ts defines the shape of crystal data and
 * crystal.validator.ts verifies structural correctness, crystal.theory.ts
 * interprets that data — resolving which GAIA modules a crystal resonates
 * with, computing weighted resonance scores, and producing actionable
 * context objects for GAIA's various intelligence systems.
 *
 * ⚠️  IMPORTANT: This module operates on interpretive, metaphysical data.
 *     The results it produces are meaning-layer outputs, not physical science.
 *     They are clearly marked as such throughout.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * EXPORTS
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *   resolveGAIAResonance(record)  — Primary function. Returns a full
 *                                   ResonanceResolution for any CrystalRecord.
 *
 *   getSafetyProfile(record)      — Returns safety flags (water, hardware,
 *                                   toxicity tier) in a single object.
 *
 *   getIntentionContext(record)   — Returns intention-layer context used by
 *                                   GAIA's recommendation and guidance systems.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * THEORY: HOW RESONANCE IS RESOLVED
 * ─────────────────────────────────────────────────────────────────────────────
 *
 *   Each GAIA module (ClarusLens, AnchorPrism, SomnusVeil, SovereignCore,
 *   ViriditasHeart, Noosphere, QuantumNexus) has a set of keyword signals
 *   drawn from crystallographic tradition, colour psychology, and chakra
 *   alignment theory.
 *
 *   A crystal's gaia_resonance string (free-text from the metaphysical layer)
 *   is tokenised and matched against each module's keyword set. Each match
 *   contributes a fractional weight. The sum of weights across all modules
 *   forms a resonance profile, normalised to [0, 1].
 *
 *   The module with the highest normalised weight is the primary_module.
 *   All modules with weight > 0 appear in the modules array, sorted by weight.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 */

import type {
  CrystalRecord,
  GAIAModule,
  Chakra,
  Element,
  AngelNumber,
} from './db/crystal.schema';
import { GAIA_MODULES } from './db/metaphysical.data';

// ─── Internal Module Definition ──────────────────────────────────────────────

interface ModuleDefinition {
  id:           GAIAModule;
  name:         string;
  keywords:     string[];
  chakras:      Chakra[];
  elements:     Element[];
  base_weight:  number;
}

// ─── Module Keyword Maps ──────────────────────────────────────────────────────

const MODULE_DEFINITIONS: ModuleDefinition[] = [
  {
    id:   'ClarusLens',
    name: 'ClarusLens — Clarity & Vision',
    keywords: [
      'clarity', 'vision', 'insight', 'perception', 'awareness', 'truth',
      'focus', 'mental', 'intellect', 'mind', 'psychic', 'intuition',
      'third eye', 'clairvoyance', 'light', 'illumination', 'transparency',
      'discernment', 'wisdom', 'understanding', 'knowledge', 'amplification',
      'clear', 'crystal clear', 'seeing', 'sight',
    ],
    chakras:     ['Third Eye', 'Crown', 'Higher Crown'],
    elements:    ['Air', 'Light', 'Aether'],
    base_weight: 1.0,
  },
  {
    id:   'AnchorPrism',
    name: 'AnchorPrism — Grounding & Structure',
    keywords: [
      'grounding', 'protection', 'stability', 'strength', 'root', 'earth',
      'anchor', 'foundation', 'security', 'boundaries', 'shielding',
      'physical', 'body', 'material', 'practical', 'endurance', 'resilience',
      'courage', 'determination', 'will', 'perseverance', 'structure',
      'order', 'discipline', 'manifestation', 'abundance',
    ],
    chakras:     ['Root', 'Earth Star', 'Solar Plexus'],
    elements:    ['Earth', 'Fire', 'Metal'],
    base_weight: 1.0,
  },
  {
    id:   'SomnusVeil',
    name: 'SomnusVeil — Dreams & Subconscious',
    keywords: [
      'dream', 'sleep', 'subconscious', 'unconscious', 'lunar', 'moon',
      'intuition', 'feeling', 'emotion', 'psychic', 'vision', 'trance',
      'meditation', 'astral', 'journey', 'travel', 'rebirth', 'transformation',
      'shadow', 'depth', 'mystery', 'hidden', 'inner', 'feminine',
      'receptive', 'yin', 'water', 'flow', 'release', 'letting go',
    ],
    chakras:     ['Third Eye', 'Sacral', 'Soul Star'],
    elements:    ['Water', 'Ice', 'Aether'],
    base_weight: 1.0,
  },
  {
    id:   'SovereignCore',
    name: 'SovereignCore — Will & Sovereignty',
    keywords: [
      'sovereignty', 'power', 'will', 'leadership', 'authority', 'confidence',
      'self', 'identity', 'purpose', 'intention', 'manifestation', 'action',
      'solar', 'sun', 'fire', 'transformation', 'alchemy', 'success',
      'achievement', 'ambition', 'motivation', 'drive', 'passion',
      'courage', 'strength', 'vitality', 'energy', 'activation',
    ],
    chakras:     ['Solar Plexus', 'Sacral', 'Root'],
    elements:    ['Fire', 'Metal', 'Earth'],
    base_weight: 1.0,
  },
  {
    id:   'ViriditasHeart',
    name: 'ViriditasHeart — Life Force & Healing',
    keywords: [
      'love', 'healing', 'heart', 'compassion', 'nurturing', 'growth',
      'nature', 'life', 'vitality', 'renewal', 'regeneration', 'green',
      'plant', 'earth', 'fertility', 'abundance', 'harmony', 'balance',
      'peace', 'calm', 'soothing', 'emotional', 'relationships', 'connection',
      'empathy', 'kindness', 'forgiveness', 'acceptance', 'joy',
    ],
    chakras:     ['Heart', 'Higher Heart', 'Higher Heart (Thymus)'],
    elements:    ['Earth', 'Water', 'Wood'],
    base_weight: 1.0,
  },
  {
    id:   'Noosphere',
    name: 'Noosphere — Collective Consciousness',
    keywords: [
      'consciousness', 'collective', 'unity', 'oneness', 'cosmic', 'universal',
      'akasha', 'akashic', 'record', 'higher', 'dimension', 'spirit', 'soul',
      'ascension', 'expansion', 'awakening', 'enlightenment', 'divine',
      'angelic', 'celestial', 'crown', 'connection', 'channelling', 'guide',
      'transmission', 'communication', 'bridge', 'gateway', 'portal',
    ],
    chakras:     ['Crown', 'Higher Crown', 'Soul Star'],
    elements:    ['Akasha', 'Aether', 'Air'],
    base_weight: 1.0,
  },
  {
    id:   'QuantumNexus',
    name: 'QuantumNexus — Transformation & Integration',
    keywords: [
      'transformation', 'change', 'integration', 'synthesis', 'balance',
      'duality', 'polarity', 'bridge', 'transition', 'evolution', 'shift',
      'quantum', 'multidimensional', 'frequency', 'vibration', 'resonance',
      'alchemy', 'transmutation', 'shadow work', 'integration', 'wholeness',
      'completion', 'cycle', 'karma', 'destiny', 'pattern', 'matrix',
    ],
    chakras:     ['All chakras', 'Earth Star', 'Soul Star'],
    elements:    ['Storm', 'Akasha', 'Aether'],
    base_weight: 1.0,
  },
];

/** Fast O(1) module lookup by id */
const MODULE_MAP = new Map<GAIAModule, ModuleDefinition>(
  MODULE_DEFINITIONS.map(m => [m.id, m])
);

// ─── Public Types ─────────────────────────────────────────────────────────────

/** A single module's resonance weight, normalised to [0, 1] */
export interface ResonanceWeight {
  module:     GAIAModule;
  weight:     number;  // [0, 1]
  raw_score:  number;  // pre-normalisation count
  matched_keywords: string[];
}

/** Full resonance resolution for a single CrystalRecord */
export interface ResonanceResolution {
  crystal_name:    string;
  primary_module:  GAIAModule | null;
  modules:         ResonanceWeight[];       // sorted by weight DESC, weight > 0 only
  all_modules:     GAIAModule[];            // all module IDs, for filter-by-module queries
  resonance_score: number;                  // [0, 1] — overall strength of resonance
  resolved_at:     string;                  // ISO timestamp
}

/** A single crystal's safety profile */
export interface SafetyProfile {
  safe_for_water:     boolean;
  safe_for_hardware:  boolean;
  piezoelectric:      boolean;
  safety_warning:     string | null;
  risk_tier:          'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

/** Intention context for GAIA's guidance systems */
export interface IntentionContext {
  crystal_name:     string;
  intention:        string;
  primary_module:   GAIAModule | null;
  module_name:      string;
  angel_number:     AngelNumber;
  angel_meaning:    string;
  working_guidance: string;
}

// ─── Angel Number Definitions ─────────────────────────────────────────────────

interface AngelNumberDefinition {
  number:  AngelNumber;
  meaning: string;
}

const ANGEL_NUMBERS: AngelNumberDefinition[] = [
  { number: 1,    meaning: 'New beginnings, leadership, initiation' },
  { number: 2,    meaning: 'Balance, partnership, duality' },
  { number: 3,    meaning: 'Creativity, self-expression, expansion' },
  { number: 4,    meaning: 'Structure, foundation, stability' },
  { number: 5,    meaning: 'Freedom, change, transformation' },
  { number: 6,    meaning: 'Harmony, home, healing' },
  { number: 7,    meaning: 'Spiritual wisdom, inner knowing, mystery' },
  { number: 8,    meaning: 'Abundance, power, manifestation' },
  { number: 9,    meaning: 'Completion, service, universal love' },
  { number: 11,   meaning: 'Master intuition, spiritual gateway, illumination' },
  { number: 22,   meaning: 'Master builder, manifestation at scale, vision' },
  { number: 33,   meaning: 'Master teacher, compassionate service, ascension' },
  { number: 23,   meaning: 'Integration of 23 mineral kingdoms' },
  { number: 44,   meaning: 'Angelic support, disciplined mastery' },
  { number: 55,   meaning: 'Major life changes, quantum leap' },
  { number: 66,   meaning: 'Heart expansion, unconditional love' },
  { number: 77,   meaning: 'Divine alignment, miraculous confirmation' },
  { number: 88,   meaning: 'Infinite abundance, karmic completion' },
  { number: 99,   meaning: 'Humanitarian service, cycle completion' },
  { number: 111,  meaning: 'Manifestation portal, thoughts becoming reality' },
  { number: 222,  meaning: 'Trust the process, divine timing' },
  { number: 333,  meaning: 'Ascended masters present, creative alignment' },
  { number: 444,  meaning: 'Angelic protection, you are on the right path' },
  { number: 555,  meaning: 'Major transformation incoming, embrace change' },
  { number: 666,  meaning: 'Rebalance focus from material to spiritual' },
  { number: 777,  meaning: 'Cosmic reward, spiritual luck, alignment' },
  { number: 808,  meaning: 'Karmic cycles closing, abundance portal' },
  { number: 888,  meaning: 'Infinite loop of abundance, financial flow' },
  { number: 999,  meaning: 'Completion of major cycle, universal service' },
  { number: 1111, meaning: 'Gateway portal — highest awakening sequence' },
  { number: 404,  meaning: 'Grounding in spiritual truth, firm foundations' },
  { number: 707,  meaning: 'Spiritual revelation, hidden knowledge revealed' },
];

const ANGEL_NUMBER_MAP = new Map<AngelNumber, AngelNumberDefinition>(
  ANGEL_NUMBERS.map(a => [a.number, a])
);

// ─── resolveGAIAResonance ─────────────────────────────────────────────────────

/**
 * resolveGAIAResonance(record)
 *
 * Resolves which GAIA modules a crystal resonates with, and how strongly.
 *
 * Algorithm:
 *   1. Extract gaia_resonance string from record.metaphysical
 *   2. Tokenise to lowercase words
 *   3. For each module, count keyword matches in token set
 *   4. Add chakra alignment bonus (0.5 per matching chakra)
 *   5. Add element alignment bonus (0.3 per matching element)
 *   6. Normalise all scores to [0, 1]
 *   7. Sort by weight DESC
 *
 * ⚠️  Operates on interpretive metaphysical data.
 *
 * @param record — Any CrystalRecord from the database
 * @returns ResonanceResolution
 */
export function resolveGAIAResonance(record: CrystalRecord): ResonanceResolution {
  const { metaphysical } = record;
  const resonanceText = metaphysical.gaia_resonance.toLowerCase();

  // Tokenise: split on whitespace, punctuation; deduplicate
  const tokens = new Set(
    resonanceText
      .split(/[\s,;.—()\[\]\/]+/)
      .filter(t => t.length > 2)
  );

  // Also check bigrams (two-word phrases)
  const words = resonanceText.split(/\s+/);
  const bigrams = new Set(
    words.slice(0, -1).map((w, i) => `${w} ${words[i + 1]}`)
  );

  // Score each module
  const rawScores: Array<{ module: ModuleDefinition; score: number; matched: string[] }> = [];
  let maxScore = 0;

  for (const mod of MODULE_DEFINITIONS) {
    let score = 0;
    const matched: string[] = [];

    // Keyword matching (unigrams + bigrams)
    for (const kw of mod.keywords) {
      const kwLower = kw.toLowerCase();
      const isMatch = kw.includes(' ')
        ? bigrams.has(kwLower)
        : tokens.has(kwLower) || resonanceText.includes(kwLower);

      if (isMatch) {
        score += 1;
        matched.push(kw);
      }
    }

    // Chakra alignment bonus
    const primaryChakra = metaphysical.chakra_primary;
    const secondaryChakras = metaphysical.chakra_secondary ?? [];
    for (const chakra of mod.chakras) {
      if (chakra === primaryChakra)              score += 0.5;
      else if (secondaryChakras.includes(chakra)) score += 0.25;
    }

    // Element alignment bonus
    const elements = metaphysical.element ?? [];
    for (const el of mod.elements) {
      if (elements.includes(el)) score += 0.3;
    }

    if (score > maxScore) maxScore = score;
    rawScores.push({ module: mod, score, matched });
  }

  // Normalise
  const weights: ResonanceWeight[] = rawScores
    .filter(s => s.score > 0)
    .map(s => ({
      module:           s.module.id,
      weight:           maxScore > 0 ? s.score / maxScore : 0,
      raw_score:        s.score,
      matched_keywords: s.matched,
    }))
    .sort((a, b) => b.weight - a.weight);

  const primary = weights[0]?.module ?? null;
  const resonance_score = maxScore > 0 ? Math.min(1, maxScore / 10) : 0;

  return {
    crystal_name:    record.name,
    primary_module:  primary,
    modules:         weights,
    all_modules:     weights.map(w => w.module),
    resonance_score,
    resolved_at:     new Date().toISOString(),
  };
}

// ─── getSafetyProfile ─────────────────────────────────────────────────────────

/**
 * getSafetyProfile(record)
 *
 * Returns a consolidated safety profile for a crystal record.
 * Derives risk_tier from toxicity signals in the safety_warning text
 * and the physical flags (safe_for_water, safe_for_hardware).
 *
 * @param record — Any CrystalRecord from the database
 * @returns SafetyProfile
 */
export function getSafetyProfile(record: CrystalRecord): SafetyProfile {
  const { physical, metaphysical } = record;

  const warning = metaphysical.safety_warning?.toLowerCase() ?? '';

  // Derive risk tier from safety warning text
  let risk_tier: SafetyProfile['risk_tier'] = 'NONE';

  if (warning.includes('fatal') || warning.includes('lethal') || warning.includes('arsenic') ||
      warning.includes('lead') || warning.includes('mercury') || warning.includes('cadmium') ||
      warning.includes('cyanide') || warning.includes('radioactive')) {
    risk_tier = 'CRITICAL';
  } else if (warning.includes('toxic') || warning.includes('poison') || warning.includes('asbestos') ||
             warning.includes('silica') || warning.includes('fibre') || warning.includes('fiber')) {
    risk_tier = 'HIGH';
  } else if (warning.includes('harmful') || warning.includes('ingestion') ||
             warning.includes('do not ingest') || warning.includes('do not breathe') ||
             warning.includes('soluble')) {
    risk_tier = 'MEDIUM';
  } else if (warning.length > 0) {
    risk_tier = 'LOW';
  }

  return {
    safe_for_water:    physical.safe_for_water,
    safe_for_hardware: physical.safe_for_hardware,
    piezoelectric:     physical.piezoelectric,
    safety_warning:    metaphysical.safety_warning,
    risk_tier,
  };
}

// ─── getIntentionContext ──────────────────────────────────────────────────────

/**
 * getIntentionContext(record)
 *
 * Returns an intention-layer context object for a crystal.
 * Used by GAIA's recommendation, guidance, and journalling systems.
 *
 * ⚠️  Operates on interpretive metaphysical data.
 *
 * @param record — Any CrystalRecord from the database
 * @returns      — IntentionContext (never throws)
 */
export function getIntentionContext(record: CrystalRecord): IntentionContext {
  const { name, metaphysical } = record;
  const { intention, angel_number } = metaphysical;

  // Resolve the primary module from gaia_resonance
  const resonance  = resolveGAIAResonance(record);
  const moduleDef  = MODULE_MAP.get(resonance.primary_module) ?? GAIA_MODULES[0];

  // Look up the angel number definition
  const angelDef: AngelNumberDefinition | null = angel_number != null
    ? (ANGEL_NUMBER_MAP.get(angel_number) ?? null)
    : null;

  const angel_meaning = angelDef?.meaning ?? 'No angel number assigned';

  // Build working guidance from intention + module resonance
  const moduleId   = resonance.primary_module ?? 'QuantumNexus';
  const moduleName = (moduleDef as any)?.name ?? moduleId;

  const working_guidance =
    `Work with ${name} through the ${moduleId} module. ` +
    `${intention} ` +
    (angelDef
      ? `The angel number ${angel_number} signals: ${angelDef.meaning}.`
      : '');

  return {
    crystal_name:     name,
    intention,
    primary_module:   resonance.primary_module,
    module_name:      moduleName,
    angel_number,
    angel_meaning,
    working_guidance,
  };
}
