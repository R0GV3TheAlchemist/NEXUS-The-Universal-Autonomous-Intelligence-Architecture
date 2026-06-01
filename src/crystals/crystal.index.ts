/**
 * crystal.index.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Unified Crystal Database — the single import surface for all crystal data,
 * theory resolution, and validation across GAIA-OS.
 *
 * Usage:
 *   import {
 *     CRYSTAL_DB, getCrystalByName, getCrystalsByModule,
 *     getCrystalProfile, searchCrystals,
 *     resolveGAIAResonance, validateRecord,
 *   } from '@/crystals/crystal.index';
 *
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { ALL_CRYSTALS } from './db/index';
import type { CrystalRecord, GAIAModule, Chakra } from './db/crystal.schema';
import { GAIA_MODULES } from './db/metaphysical.data';
import {
  resolveGAIAResonance,
  getSafetyProfile,
  type ResonanceWeight,
  type ResonanceResolution,
  type IntentionContext,
  type SafetyProfile,
} from './crystal.theory';
import {
  validateRecord,
  validateBatch,
  assertRecord,
  formatBatchReport,
  type ValidationResult,
  type BatchReport,
  type ValidationIssue,
  type IssueSeverity,
  ValidationError,
} from './crystal.validator';

// ─── Re-exports ───────────────────────────────────────────────────────────────
export {
  // crystal.theory.ts
  resolveGAIAResonance,
  getSafetyProfile,
  // crystal.validator.ts
  validateRecord,
  validateBatch,
  assertRecord,
  formatBatchReport,
  ValidationError,
};
export type {
  CrystalRecord,
  ResonanceWeight,
  ResonanceResolution,
  IntentionContext,
  SafetyProfile,
  ValidationResult,
  BatchReport,
  ValidationIssue,
  IssueSeverity,
};

// ─── Primary Lookup Maps ──────────────────────────────────────────────────────

/**
 * CRYSTAL_DB
 * O(1) lookup by canonical crystal name (lowercased).
 * Authoritative source of truth for the full registry.
 */
export const CRYSTAL_DB: ReadonlyMap<string, CrystalRecord> = (() => {
  const map = new Map<string, CrystalRecord>();
  for (const record of ALL_CRYSTALS) {
    map.set(record.name.toLowerCase(), record);
  }
  return map;
})();

/**
 * CRYSTAL_BY_NAME
 * O(1) case-insensitive lookup by primary crystal name.
 */
export const CRYSTAL_BY_NAME: ReadonlyMap<string, CrystalRecord> = CRYSTAL_DB;

/**
 * CRYSTAL_BY_MODULE
 * Multi-value map keyed by GAIAModule.
 * Each crystal appears under EVERY module resolved from its gaia_resonance string.
 */
export const CRYSTAL_BY_MODULE: ReadonlyMap<GAIAModule, CrystalRecord[]> = (() => {
  const map = new Map<GAIAModule, CrystalRecord[]>();

  // Seed every known module with an empty array
  for (const mod of GAIA_MODULES) {
    map.set(mod.id as GAIAModule, []);
  }

  for (const record of ALL_CRYSTALS) {
    const resolution = resolveGAIAResonance(record);
    for (const weight of resolution.modules) {
      const bucket = map.get(weight.module);
      if (bucket) bucket.push(record);
    }
  }

  return map;
})();

/**
 * CRYSTAL_BY_CHAKRA
 * Multi-value map keyed by primary chakra string.
 */
export const CRYSTAL_BY_CHAKRA: ReadonlyMap<Chakra, CrystalRecord[]> = (() => {
  const map = new Map<Chakra, CrystalRecord[]>();

  for (const record of ALL_CRYSTALS) {
    const primary = record.metaphysical.chakra_primary;
    if (!map.has(primary)) map.set(primary, []);
    map.get(primary)!.push(record);

    for (const chakra of record.metaphysical.chakra_secondary ?? []) {
      if (chakra !== primary) {
        if (!map.has(chakra)) map.set(chakra, []);
        map.get(chakra)!.push(record);
      }
    }
  }

  return map;
})();

// ─── Query Helpers ────────────────────────────────────────────────────────────

/** Returns the CrystalRecord whose primary name matches (case-insensitive), or undefined. */
export function getCrystalByName(name: string): CrystalRecord | undefined {
  return CRYSTAL_DB.get(name.toLowerCase());
}

/** Returns all CrystalRecords associated with the given GAIAModule. */
export function getCrystalsByModule(module: GAIAModule): CrystalRecord[] {
  return CRYSTAL_BY_MODULE.get(module) ?? [];
}

/** Returns all CrystalRecords associated with the given Chakra. */
export function getCrystalsByChakra(chakra: Chakra): CrystalRecord[] {
  return CRYSTAL_BY_CHAKRA.get(chakra) ?? [];
}

/** Returns the full array of every CrystalRecord in the database. */
export function getAllCrystals(): CrystalRecord[] {
  return ALL_CRYSTALS;
}

/** Returns the total number of crystals in the database. */
export function getCrystalCount(): number {
  return CRYSTAL_DB.size;
}

// ─── Search ───────────────────────────────────────────────────────────────────

export interface SearchOptions {
  limit?: number;
  module?: GAIAModule;
  safeForWater?: boolean;
  safeForHardware?: boolean;
}

/**
 * searchCrystals(query, options?)
 *
 * Full-text search across name and gaia_resonance.
 * Results are ordered: exact name match first, then partial name, then resonance text.
 */
export function searchCrystals(
  query: string,
  options: SearchOptions = {},
): CrystalRecord[] {
  const q = query.toLowerCase().trim();
  if (!q) return [];

  type Scored = { record: CrystalRecord; score: number };
  const scored: Scored[] = [];

  for (const record of ALL_CRYSTALS) {
    // Apply filters first
    if (options.module !== undefined) {
      const resolution = resolveGAIAResonance(record);
      if (!resolution.all_modules.includes(options.module)) continue;
    }
    if (options.safeForWater === true && !record.physical.safe_for_water) continue;
    if (options.safeForHardware === true && !record.physical.safe_for_hardware) continue;

    let score = 0;
    const nameLower = record.name.toLowerCase();

    if (nameLower === q)                                    score = 100;
    else if (nameLower.includes(q))                        score = 80;
    else if (record.metaphysical.gaia_resonance.toLowerCase().includes(q)) score = 10;

    if (score > 0) scored.push({ record, score });
  }

  scored.sort((a, b) =>
    b.score !== a.score
      ? b.score - a.score
      : a.record.name.localeCompare(b.record.name),
  );

  const results = scored.map(s => s.record);
  return options.limit !== undefined ? results.slice(0, options.limit) : results;
}

// ─── CrystalProfile ───────────────────────────────────────────────────────────

export interface CrystalProfile {
  record:        CrystalRecord;
  validation:    ValidationResult;
  isValid:       boolean;
  primaryModule: GAIAModule | null;
  safetyProfile: SafetyProfile;
}

/**
 * getCrystalProfile(name)
 *
 * Returns a fully resolved CrystalProfile for the given crystal name, or
 * undefined if no crystal exists with that name.
 */
export function getCrystalProfile(name: string): CrystalProfile | undefined {
  const record = getCrystalByName(name);
  if (!record) return undefined;

  const resolution = resolveGAIAResonance(record);
  const validation = validateRecord(record);

  return {
    record,
    validation,
    isValid:       validation.valid,
    primaryModule: resolution.primary_module,
    safetyProfile: getSafetyProfile(record),
  };
}

// ─── Integrity Check ──────────────────────────────────────────────────────────

/**
 * runIntegrityCheck()
 *
 * Validates every record in ALL_CRYSTALS using validateBatch().
 * Intended for CI pipelines and startup health checks.
 */
export function runIntegrityCheck(): BatchReport {
  return validateBatch(ALL_CRYSTALS, 'FULL_DB_INTEGRITY_CHECK');
}
