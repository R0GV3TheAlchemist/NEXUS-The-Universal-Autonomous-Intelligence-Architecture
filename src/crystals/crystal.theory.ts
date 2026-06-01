/**
 * crystal.theory.ts
 * GAIA-OS Crystal Intelligence Engine — Resonance & Safety Theory Layer
 *
 * Implements the core reasoning functions used by crystal.index.ts and
 * crystal.validator.ts:
 *
 *   resolveGAIAResonance(record)  — maps gaia_resonance string → weighted modules
 *   getSafetyProfile(record)      — computes the composite SafetyProfile
 *
 * ─────────────────────────────────────────────────────────────────────────────
 */

import type { CrystalRecord } from './db/crystal.schema';
import { RiskTier }           from './db/crystal.schema';
import type { GAIAModule }    from './db/crystal.schema';

// ─────────────────────────────────────────────────────────────────────────────
// EXPORTED TYPES
// ─────────────────────────────────────────────────────────────────────────────

/** A single module resolved from a gaia_resonance string, with a weight score */
export interface ResonanceWeight {
  module: GAIAModule;
  /** 0–100 — higher means this module's signature is more dominant in the string */
  weight: number;
}

/** Full result of a gaia_resonance resolution pass */
export interface ResonanceResolution {
  /** Ordered list of weighted modules (highest weight first) */
  modules:            ResonanceWeight[];
  /** The single highest-weight module, or null if none resolved */
  primary_module:     GAIAModule | null;
  /** Flat list of resolved module ids */
  all_modules:        GAIAModule[];
  /** True if any token in the string didn't map to a known module */
  has_unknown_token:  boolean;
  /** The unrecognised tokens, for warning output */
  unknown_tokens:     string[];
}

/** Context passed to resolveGAIAResonance for intention-weighted scoring */
export interface IntentionContext {
  intention?: string;
  chakra?:    string;
}

/** Computed safety profile for a crystal record */
export interface SafetyProfile {
  risk_tier:         string;
  safe_for_water:    boolean;
  safe_for_hardware: boolean;
  safety_notes:      string | null;
  safety_warning:    string | null;
  flags: {
    water_hazard:    boolean;
    hardware_hazard: boolean;
    high_risk:       boolean;
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// MODULE KEYWORD MAP
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Keywords associated with each GAIAModule.
 * resolveGAIAResonance scans the gaia_resonance string for these tokens
 * and accumulates a weight score per module.
 */
const MODULE_KEYWORDS: Record<GAIAModule, string[]> = {
  AnchorPrism:    ['anchor', 'grounding', 'stability', 'root', 'earth', 'foundation', 'protection', 'shield'],
  ViriditasHeart: ['heart', 'healing', 'love', 'growth', 'viriditas', 'nature', 'compassion', 'harmony', 'green'],
  SovereignCore:  ['sovereign', 'power', 'will', 'solar', 'confidence', 'authority', 'core', 'strength'],
  ClarusLens:     ['clarity', 'clarus', 'vision', 'insight', 'truth', 'perception', 'third eye', 'lens', 'light'],
  Noosphere:      ['mind', 'intellect', 'noosphere', 'communication', 'thought', 'throat', 'knowledge', 'awareness'],
  QuantumNexus:   ['quantum', 'nexus', 'transformation', 'transmutation', 'alchemy', 'change', 'shift', 'bridge'],
  SpiritusEngine: ['spirit', 'spirituality', 'crown', 'higher', 'divine', 'transcendence', 'soul', 'cosmos', 'akasha'],
  ChronoWeave:    ['time', 'chrono', 'past', 'future', 'memory', 'weave', 'record', 'akashic', 'ancient'],
};

// ─────────────────────────────────────────────────────────────────────────────
// resolveGAIAResonance
// ─────────────────────────────────────────────────────────────────────────────

/**
 * resolveGAIAResonance
 *
 * Analyses a CrystalRecord's gaia_resonance string and returns a weighted
 * list of matching GAIAModules, sorted by relevance.
 *
 * The algorithm:
 *   1. Tokenise the gaia_resonance string (lowercase, split on word boundaries)
 *   2. For each token, check it against MODULE_KEYWORDS
 *   3. Accumulate a weight counter per module (each keyword hit = +10)
 *   4. Track tokens that didn't match any module as unknown_tokens
 *   5. Normalise weights to 0–100 range
 *   6. Return sorted ResonanceResolution
 */
export function resolveGAIAResonance(
  record: CrystalRecord,
  _ctx?: IntentionContext,
): ResonanceResolution {
  const raw = record.metaphysical.gaia_resonance ?? '';
  const lower = raw.toLowerCase();

  const scores = new Map<GAIAModule, number>();
  const matchedTokens = new Set<string>();

  // Score each module based on keyword hits
  for (const [mod, keywords] of Object.entries(MODULE_KEYWORDS) as [GAIAModule, string[]][]) {
    let score = 0;
    for (const kw of keywords) {
      if (lower.includes(kw)) {
        score += 10;
        matchedTokens.add(kw);
      }
    }
    if (score > 0) scores.set(mod, score);
  }

  // Detect unknown tokens — words in the string not covered by any keyword
  const words = lower.split(/[\s,;.\-–—/|]+/).filter(Boolean);
  const allKeywords = new Set(Object.values(MODULE_KEYWORDS).flat());
  const unknown_tokens = words.filter(
    w => w.length > 3 && !allKeywords.has(w) && !matchedTokens.has(w)
  );

  // Normalise to 0–100
  const maxScore = Math.max(...scores.values(), 1);
  const modules: ResonanceWeight[] = [...scores.entries()]
    .map(([module, weight]) => ({ module, weight: Math.round((weight / maxScore) * 100) }))
    .sort((a, b) => b.weight - a.weight);

  return {
    modules,
    primary_module:    modules[0]?.module ?? null,
    all_modules:       modules.map(m => m.module),
    has_unknown_token: unknown_tokens.length > 0,
    unknown_tokens,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// getSafetyProfile
// ─────────────────────────────────────────────────────────────────────────────

/**
 * getSafetyProfile
 *
 * Builds a composite SafetyProfile for a CrystalRecord by combining:
 *   - The record's declared risk_tier
 *   - safe_for_water and safe_for_hardware flags
 *   - safety_notes and safety_warning text
 *
 * The profile is used by crystal.validator.ts (Domain C) and by the
 * GAIA-OS UI to surface appropriate safety messaging.
 */
export function getSafetyProfile(record: CrystalRecord): SafetyProfile {
  const m = record.metaphysical;
  const p = record.physical;

  // Escalate tier if physical flags indicate hazard but tier is too low
  let effectiveTier = m.risk_tier;
  if (
    (!p.safe_for_water || !p.safe_for_hardware) &&
    (effectiveTier === RiskTier.NONE || effectiveTier === RiskTier.LOW)
  ) {
    effectiveTier = RiskTier.MEDIUM;
  }

  return {
    risk_tier:         effectiveTier,
    safe_for_water:    p.safe_for_water,
    safe_for_hardware: p.safe_for_hardware,
    safety_notes:      m.safety_notes,
    safety_warning:    m.safety_warning,
    flags: {
      water_hazard:    !p.safe_for_water,
      hardware_hazard: !p.safe_for_hardware,
      high_risk:       effectiveTier === RiskTier.HIGH || effectiveTier === RiskTier.CRITICAL,
    },
  };
}
