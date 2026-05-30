/**
 * src/crystals/crystal.theory.ts
 * GAIA-OS Crystal Intelligence Engine — Theory / Reasoning Layer
 *
 * This module is the reasoning layer over the crystal database.
 * Where crystal.schema.ts defines *what a record is*, this module
 * defines *what GAIA does with a record* — parsing, weighting,
 * hydrating, and scoring across all resonance axes.
 *
 * ─── EXPORTS ───────────────────────────────────────────────────────────────
 *
 *   resolveGAIAResonance(record)
 *     Parses the freeform `gaia_resonance` string (e.g. "ClarusLens + Noosphere")
 *     into a typed ResonanceResolution with primary/secondary weighting.
 *     This is the linchpin function — every downstream query that filters
 *     by module depends on this parser being correct.
 *
 *   getIntentionContext(record)
 *     Hydrates a crystal's one-line `intention` with the full archetypal
 *     context from the AngelNumber registry and the primary GAIA module
 *     tagline. Used by GAIA when constructing intention-setting prompts.
 *
 *   getSafetyProfile(record)
 *     Consolidates `safe_for_water`, `safe_for_hardware`, `piezoelectric`,
 *     and `safety_warning` into a single typed SafetyProfile with a
 *     RiskTier enum for quick programmatic branching.
 *
 *   scoreResonanceAlignment(a, b)
 *     Produces a 0–1 alignment score between two CrystalRecord instances
 *     across all resonance axes (module overlap, chakra, element, hue,
 *     numerology, angel number). Used for pairing recommendations and
 *     matrix configuration logic.
 *
 * ─── DESIGN NOTES ───────────────────────────────────────────────────────────
 *
 *   1. All functions are pure (no side effects, no I/O).
 *   2. All functions are null-safe — they never throw on missing data;
 *      they return structured fallback results instead.
 *   3. The metaphysical layer is explicitly interpretive. Functions that
 *      touch it carry JSDoc ⚠️ markers — GAIA must present this data
 *      with appropriate epistemic framing.
 *   4. Weights used in scoring are documented inline and exported as
 *      RESONANCE_WEIGHTS so callers can override them without forking.
 *
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-30
 * Schema: CrystalRecord v1.3
 */

import type { CrystalRecord, GAIAModule, Chakra, Element } from './db/crystal.schema';
import {
  GAIA_MODULES,
  ANGEL_NUMBER_MAP,
  type GAIAModuleDefinition,
  type AngelNumberDefinition,
} from './db/metaphysical.data';

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 1 — GAIA RESONANCE RESOLUTION
// ─────────────────────────────────────────────────────────────────────────────

/**
 * A single module assignment with a fractional weight.
 * Primary module carries weight 1.0; secondary modules share the remainder
 * equally, floored at 0.5 to prevent dilution below meaningful threshold.
 */
export interface ResonanceWeight {
  module:     GAIAModule;
  definition: GAIAModuleDefinition;
  /** 0.5–1.0 — primary = 1.0, secondary ≥ 0.5 */
  weight:     number;
  /** True if this is the first-listed (primary) module */
  is_primary: boolean;
}

/**
 * The fully resolved resonance for a single CrystalRecord.
 * Parsed from the freeform `metaphysical.gaia_resonance` string.
 */
export interface ResonanceResolution {
  /** Crystal display name for traceability */
  crystal_name: string;
  /** Raw unparsed string from the record */
  raw: string;
  /** Ordered list of resolved modules, primary first */
  modules: ResonanceWeight[];
  /** Convenience: the primary GAIAModule id */
  primary_module: GAIAModule;
  /** All GAIAModule ids present (for Set/filter operations) */
  all_modules: GAIAModule[];
  /** True if the raw string contained an unrecognised token */
  has_unknown_token: boolean;
  /** Any tokens that could not be matched to a valid GAIAModule */
  unknown_tokens: string[];
}

/** All valid GAIAModule ids as a Set for O(1) membership testing */
const VALID_MODULES: Set<string> = new Set(
  GAIA_MODULES.map(m => m.id)
);

/** Module definition lookup map */
const MODULE_MAP: Map<GAIAModule, GAIAModuleDefinition> = new Map(
  GAIA_MODULES.map(m => [m.id as GAIAModule, m])
);

/**
 * resolveGAIAResonance
 *
 * Parses the freeform `gaia_resonance` string on a CrystalRecord's
 * metaphysical layer into a fully typed ResonanceResolution.
 *
 * Parsing rules:
 *   - Splits on '+', '/', ',', 'and', 'AND' (trimmed)
 *   - First recognised token = primary (weight 1.0)
 *   - Remaining tokens = secondary, weight = max(0.5, 1 / token_count)
 *   - Unrecognised tokens are collected in unknown_tokens without throwing
 *   - If ALL tokens are unrecognised, primary_module defaults to 'Noosphere'
 *     and has_unknown_token is true
 *
 * ⚠️  Operates on interpretive metaphysical data.
 *
 * @param record — Any CrystalRecord from the database
 * @returns      — ResonanceResolution (never throws)
 */
export function resolveGAIAResonance(record: CrystalRecord): ResonanceResolution {
  const raw        = record.metaphysical.gaia_resonance ?? '';
  const crystalName = record.name;

  // Split on delimiters: +, /, comma, 'and' (case-insensitive), whitespace-only
  const rawTokens = raw
    .split(/[+/,]|\band\b/i)
    .map(t => t.trim())
    .filter(t => t.length > 0);

  if (rawTokens.length === 0) {
    // Empty or null gaia_resonance — degenerate fallback
    return buildFallbackResolution(crystalName, raw, 'Noosphere', ['<empty>']);
  }

  const recognisedModules: GAIAModule[] = [];
  const unknownTokens: string[]         = [];

  for (const token of rawTokens) {
    if (VALID_MODULES.has(token)) {
      recognisedModules.push(token as GAIAModule);
    } else {
      unknownTokens.push(token);
    }
  }

  if (recognisedModules.length === 0) {
    // No recognisable modules at all
    return buildFallbackResolution(crystalName, raw, 'Noosphere', unknownTokens);
  }

  // Weight assignment:
  //   primary  = 1.0
  //   secondaries share the remaining weight evenly, minimum 0.5 each
  const count = recognisedModules.length;
  const secondaryWeight = count > 1
    ? Math.max(0.5, 1 / count)
    : 0; // unused when count === 1

  const modules: ResonanceWeight[] = recognisedModules.map((moduleId, index) => ({
    module:     moduleId,
    definition: MODULE_MAP.get(moduleId)!,
    weight:     index === 0 ? 1.0 : secondaryWeight,
    is_primary: index === 0,
  }));

  return {
    crystal_name:      crystalName,
    raw,
    modules,
    primary_module:    recognisedModules[0],
    all_modules:       recognisedModules,
    has_unknown_token: unknownTokens.length > 0,
    unknown_tokens:    unknownTokens,
  };
}

/** Internal helper — builds a fallback resolution when parsing fails */
function buildFallbackResolution(
  crystalName: string,
  raw: string,
  fallbackModule: GAIAModule,
  unknownTokens: string[]
): ResonanceResolution {
  const def = MODULE_MAP.get(fallbackModule)!;
  return {
    crystal_name:      crystalName,
    raw,
    modules: [{
      module:     fallbackModule,
      definition: def,
      weight:     1.0,
      is_primary: true,
    }],
    primary_module:    fallbackModule,
    all_modules:       [fallbackModule],
    has_unknown_token: true,
    unknown_tokens:    unknownTokens,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 2 — INTENTION CONTEXT
// ─────────────────────────────────────────────────────────────────────────────

/**
 * The fully hydrated intention context for a crystal.
 * Combines the crystal's one-line intention with angel number archetypal
 * messaging and the primary GAIA module tagline.
 */
export interface IntentionContext {
  /** Crystal display name */
  crystal_name: string;
  /** The crystal's own intention statement */
  intention: string;
  /** Angel number if assigned, or null */
  angel_number: number | null;
  /** Full AngelNumberDefinition if the angel_number is registered */
  angel_number_def: AngelNumberDefinition | null;
  /** Primary GAIA module this crystal serves */
  primary_module: GAIAModule;
  /** The module's one-line operational tagline */
  module_tagline: string;
  /**
   * A synthesised activation phrase for GAIA to use in prompts.
   * Format: "[crystal_name] — [intention] | [angel_number_name]: [angel_message]"
   * Falls back gracefully if angel number is null.
   */
  activation_phrase: string;
}

/**
 * getIntentionContext
 *
 * Hydrates a crystal's metaphysical intention with full archetypal context
 * from the AngelNumber registry and primary GAIA module definition.
 *
 * Used by GAIA when:
 *   - Building crystal grid intention-setting prompts
 *   - Presenting a crystal's purpose in natural language
 *   - Constructing activation sequences for hardware grids
 *
 * ⚠️  Operates on interpretive metaphysical data.
 *
 * @param record — Any CrystalRecord from the database
 * @returns      — IntentionContext (never throws)
 */
export function getIntentionContext(record: CrystalRecord): IntentionContext {
  const { name, metaphysical } = record;
  const { intention, angel_number, gaia_resonance } = metaphysical;

  // Resolve the primary module from gaia_resonance
  const resonance  = resolveGAIAResonance(record);
  const moduleDef  = MODULE_MAP.get(resonance.primary_module) ?? GAIA_MODULES[0];

  // Look up the angel number definition
  const angelDef: AngelNumberDefinition | null = angel_number != null
    ? (ANGEL_NUMBER_MAP.get(angel_number) ?? null)
    : null;

  // Build the synthesised activation phrase
  let activation_phrase: string;
  if (angelDef) {
    activation_phrase =
      `${name} — ${intention} | ${angelDef.name}: ${angelDef.message}`;
  } else {
    activation_phrase = `${name} — ${intention} | ${moduleDef.tagline}`;
  }

  return {
    crystal_name:     name,
    intention,
    angel_number:     angel_number ?? null,
    angel_number_def: angelDef,
    primary_module:   resonance.primary_module,
    module_tagline:   moduleDef.tagline,
    activation_phrase,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 3 — SAFETY PROFILE
// ─────────────────────────────────────────────────────────────────────────────

/**
 * RiskTier — ordered severity tiers for safety classification.
 *
 * NONE    — no known hazards; safe for all standard uses
 * LOW     — minor precautions (e.g. avoid extended water soak)
 * MEDIUM  — handling precautions required (e.g. wash hands; toxic trace minerals)
 * HIGH    — significant hazard; specific safety protocol required
 * CRITICAL— severe toxicity (arsenic, lead, asbestos, radiation)
 */
export type RiskTier = 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

/** Consolidated safety assessment for a CrystalRecord */
export interface SafetyProfile {
  crystal_name:       string;
  /** True if the physical record flags this stone as safe for water/elixirs */
  safe_for_water:     boolean;
  /** True if safe for proximity to electronic / quantum hardware */
  safe_for_hardware:  boolean;
  /** True if the mineral exhibits piezoelectric behaviour */
  piezoelectric:      boolean;
  /** Raw safety_warning text from the metaphysical record, or null */
  warning_text:       string | null;
  /** Computed RiskTier based on keyword analysis of warning_text + flags */
  risk_tier:          RiskTier;
  /**
   * Human-readable summary of the safety posture.
   * Synthesised from the flags and warning text — suitable for UI display.
   */
  summary:            string;
  /**
   * Structured list of specific hazard flags.
   * Empty array = no known hazards.
   */
  hazards:            string[];
}

/**
 * Keywords that elevate risk tier.
 * Each entry is [pattern, tier] — matched case-insensitively against warning_text.
 * Evaluated in order; highest match wins.
 */
const RISK_KEYWORDS: Array<[RegExp, RiskTier]> = [
  [/\b(radioactive|radiation|radioactiv)/i,               'CRITICAL'],
  [/\b(asbestos|fibrous|carcinogenic)/i,                  'CRITICAL'],
  [/\b(arsenic|lead|mercury|cadmium|barium|beryllium)/i,  'CRITICAL'],
  [/\b(toxic|toxin|poisonous|poison)/i,                   'HIGH'],
  [/\b(copper leach|iron leach|sulfide leach)/i,          'HIGH'],
  [/\b(wash hands|do not ingest|never ingest)/i,          'MEDIUM'],
  [/\b(avoid.*water|dissolv|degrad)/i,                    'LOW'],
  [/\b(gentle|minimal|minor|precaution)/i,                'LOW'],
];

/** Tier ordering for comparison */
const TIER_ORDER: Record<RiskTier, number> = {
  NONE: 0, LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4,
};

/**
 * getSafetyProfile
 *
 * Consolidates all safety-relevant fields from a CrystalRecord into a
 * single typed SafetyProfile with a computed RiskTier.
 *
 * RiskTier derivation:
 *   1. If warning_text contains CRITICAL keywords → CRITICAL
 *   2. If warning_text contains HIGH keywords → HIGH
 *   3. If safe_for_water is false without a warning → MEDIUM
 *      (absence of a warning for a water-unsafe stone is itself a flag)
 *   4. If warning_text contains MEDIUM/LOW keywords → that tier
 *   5. If no flags and no warning → NONE
 *
 * @param record — Any CrystalRecord from the database
 * @returns      — SafetyProfile (never throws)
 */
export function getSafetyProfile(record: CrystalRecord): SafetyProfile {
  const { name }        = record;
  const { safe_for_water, safe_for_hardware, piezoelectric } = record.physical;
  const warning_text    = record.metaphysical.safety_warning ?? null;

  const hazards: string[] = [];
  let computedTier: RiskTier = 'NONE';

  // ── Flag-based hazards ────────────────────────────────────────────────────
  if (!safe_for_water)     hazards.push('Not safe for water elixirs or prolonged submersion');
  if (!safe_for_hardware)  hazards.push('Not safe for proximity to electronic or quantum hardware');
  if (piezoelectric)       hazards.push('Piezoelectric — generates charge under mechanical stress');

  // ── Keyword-based tier elevation ─────────────────────────────────────────
  if (warning_text) {
    for (const [pattern, tier] of RISK_KEYWORDS) {
      if (pattern.test(warning_text)) {
        if (TIER_ORDER[tier] > TIER_ORDER[computedTier]) {
          computedTier = tier;
        }
      }
    }
  }

  // ── Flag-based tier elevation (independent of keyword match) ─────────────
  if (!safe_for_water && computedTier === 'NONE') {
    // Water-unsafe with no warning text is a data gap — flag at LOW minimum
    computedTier = 'LOW';
  }

  if (!safe_for_hardware && TIER_ORDER[computedTier] < TIER_ORDER['MEDIUM']) {
    computedTier = 'MEDIUM';
  }

  // ── Build summary ─────────────────────────────────────────────────────────
  const summary = buildSafetySummary(name, computedTier, hazards, warning_text);

  return {
    crystal_name:      name,
    safe_for_water,
    safe_for_hardware,
    piezoelectric,
    warning_text,
    risk_tier:         computedTier,
    summary,
    hazards,
  };
}

/** Builds a human-readable summary string from the safety profile components */
function buildSafetySummary(
  name: string,
  tier: RiskTier,
  hazards: string[],
  warningText: string | null
): string {
  if (tier === 'NONE' && hazards.length === 0) {
    return `${name}: No known hazards. Safe for standard handling, water cleansing, and hardware proximity.`;
  }

  const tierLabel: Record<RiskTier, string> = {
    NONE:     'No hazard',
    LOW:      'Low risk — minor precautions advised',
    MEDIUM:   'Medium risk — handling precautions required',
    HIGH:     'High risk — specific safety protocol required',
    CRITICAL: 'CRITICAL — severe toxicity or physical hazard',
  };

  const lines = [
    `${name}: ${tierLabel[tier]}.`,
    ...hazards.map(h => `• ${h}`),
  ];

  if (warningText) {
    lines.push(`Note: ${warningText}`);
  }

  return lines.join(' ');
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION 4 — RESONANCE ALIGNMENT SCORING
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Axis weights for the resonance alignment score.
 * Exported so callers can override for domain-specific use cases
 * (e.g. a chakra-healing query weights chakra_overlap higher;
 *  a hardware grid query weights module_overlap higher).
 *
 * Weights should sum to 1.0.
 */
export const RESONANCE_WEIGHTS = {
  /** Overlap in GAIA modules (primary only, weighted) */
  module_overlap:   0.35,
  /** Shared chakra alignments */
  chakra_overlap:   0.20,
  /** Shared element correspondences */
  element_overlap:  0.15,
  /** OKLCH hue proximity (angular distance, inverted) */
  hue_proximity:    0.15,
  /** Pythagorean numerology proximity */
  numerology_match: 0.10,
  /** Angel number category match */
  angel_match:      0.05,
} as const;

/** Result of a pairwise resonance alignment computation */
export interface ResonanceScore {
  crystal_a:    string;
  crystal_b:    string;
  /** Overall 0–1 alignment score */
  score:        number;
  /** Per-axis breakdown for transparency */
  axes: {
    module_overlap:   number;
    chakra_overlap:   number;
    element_overlap:  number;
    hue_proximity:    number;
    numerology_match: number;
    angel_match:      number;
  };
  /** Qualitative interpretation of the score */
  interpretation: 'dissonant' | 'neutral' | 'harmonious' | 'resonant' | 'unified';
}

/**
 * scoreResonanceAlignment
 *
 * Computes a 0–1 alignment score between two CrystalRecord instances
 * across six resonance axes.
 *
 * Score interpretation:
 *   0.00–0.20  dissonant  — opposing or unrelated frequencies
 *   0.21–0.40  neutral    — no strong connection
 *   0.41–0.60  harmonious — compatible, gentle synergy
 *   0.61–0.80  resonant   — strong alignment across multiple axes
 *   0.81–1.00  unified    — deep multi-axis resonance
 *
 * ⚠️  The chakra, element, numerology, and angel axes operate on
 *     interpretive metaphysical data.
 *
 * @param a — First CrystalRecord
 * @param b — Second CrystalRecord
 * @returns   ResonanceScore
 */
export function scoreResonanceAlignment(
  a: CrystalRecord,
  b: CrystalRecord
): ResonanceScore {
  const resA = resolveGAIAResonance(a);
  const resB = resolveGAIAResonance(b);

  // ── Axis 1: Module overlap ────────────────────────────────────────────────
  // Compare the weighted module sets. Score = sum of weight products for
  // matching modules, normalised by the maximum possible overlap.
  const moduleScoreRaw = resA.modules.reduce((sum, wA) => {
    const wB = resB.modules.find(m => m.module === wA.module);
    return wB ? sum + (wA.weight * wB.weight) : sum;
  }, 0);
  // Normalise: maximum overlap = sum of squared weights for the smaller set
  const maxOverlapA = resA.modules.reduce((s, w) => s + w.weight * w.weight, 0);
  const maxOverlapB = resB.modules.reduce((s, w) => s + w.weight * w.weight, 0);
  const moduleOverlap = Math.min(
    1,
    moduleScoreRaw / Math.max(Math.min(maxOverlapA, maxOverlapB), 0.0001)
  );

  // ── Axis 2: Chakra overlap ────────────────────────────────────────────────
  const allChakrasA = new Set<Chakra>([
    a.metaphysical.chakra_primary,
    ...a.metaphysical.chakra_secondary,
  ]);
  const allChakrasB = new Set<Chakra>([
    b.metaphysical.chakra_primary,
    ...b.metaphysical.chakra_secondary,
  ]);
  const chakraIntersection = [...allChakrasA].filter(c => allChakrasB.has(c)).length;
  const chakraUnion = new Set([...allChakrasA, ...allChakrasB]).size;
  const chakraOverlap = chakraUnion > 0 ? chakraIntersection / chakraUnion : 0;

  // ── Axis 3: Element overlap ───────────────────────────────────────────────
  const elemsA = new Set<Element>(a.metaphysical.element);
  const elemsB = new Set<Element>(b.metaphysical.element);
  const elemIntersection = [...elemsA].filter(e => elemsB.has(e)).length;
  const elemUnion = new Set([...elemsA, ...elemsB]).size;
  const elementOverlap = elemUnion > 0 ? elemIntersection / elemUnion : 0;

  // ── Axis 4: OKLCH hue proximity ───────────────────────────────────────────
  // Angular distance on the hue wheel (0–180°), inverted and normalised
  const hA = a.color.oklch.h;
  const hB = b.color.oklch.h;
  const rawDelta = Math.abs(hA - hB);
  const angularDelta = Math.min(rawDelta, 360 - rawDelta); // 0–180
  const hueProximity = 1 - (angularDelta / 180);

  // ── Axis 5: Numerology proximity ──────────────────────────────────────────
  const numA = a.metaphysical.numerology;
  const numB = b.metaphysical.numerology;
  let numerologyMatch = 0;
  if (numA != null && numB != null) {
    // Exact match = 1.0; adjacent = 0.7; within 3 = 0.3; beyond = 0
    const diff = Math.abs(numA - numB);
    numerologyMatch = diff === 0 ? 1.0
                    : diff === 1 ? 0.7
                    : diff <= 3  ? 0.3
                    : 0;
  }

  // ── Axis 6: Angel number category match ───────────────────────────────────
  const anA = a.metaphysical.angel_number;
  const anB = b.metaphysical.angel_number;
  let angelMatch = 0;
  if (anA != null && anB != null) {
    const defA = ANGEL_NUMBER_MAP.get(anA);
    const defB = ANGEL_NUMBER_MAP.get(anB);
    if (anA === anB) {
      angelMatch = 1.0; // identical angel number
    } else if (defA && defB) {
      if (defA.gaia_module === defB.gaia_module)  angelMatch = 0.7;
      else if (defA.category === defB.category)   angelMatch = 0.4;
    }
  }

  // ── Weighted composite score ──────────────────────────────────────────────
  const score =
    moduleOverlap   * RESONANCE_WEIGHTS.module_overlap   +
    chakraOverlap   * RESONANCE_WEIGHTS.chakra_overlap   +
    elementOverlap  * RESONANCE_WEIGHTS.element_overlap  +
    hueProximity    * RESONANCE_WEIGHTS.hue_proximity    +
    numerologyMatch * RESONANCE_WEIGHTS.numerology_match +
    angelMatch      * RESONANCE_WEIGHTS.angel_match;

  const clampedScore = Math.min(1, Math.max(0, score));

  // ── Interpretation ────────────────────────────────────────────────────────
  const interpretation: ResonanceScore['interpretation'] =
    clampedScore <= 0.20 ? 'dissonant'
    : clampedScore <= 0.40 ? 'neutral'
    : clampedScore <= 0.60 ? 'harmonious'
    : clampedScore <= 0.80 ? 'resonant'
    : 'unified';

  return {
    crystal_a:    a.name,
    crystal_b:    b.name,
    score:        Math.round(clampedScore * 1000) / 1000, // 3 d.p.
    axes: {
      module_overlap:   Math.round(moduleOverlap   * 1000) / 1000,
      chakra_overlap:   Math.round(chakraOverlap   * 1000) / 1000,
      element_overlap:  Math.round(elementOverlap  * 1000) / 1000,
      hue_proximity:    Math.round(hueProximity    * 1000) / 1000,
      numerology_match: Math.round(numerologyMatch * 1000) / 1000,
      angel_match:      Math.round(angelMatch      * 1000) / 1000,
    },
    interpretation,
  };
}
