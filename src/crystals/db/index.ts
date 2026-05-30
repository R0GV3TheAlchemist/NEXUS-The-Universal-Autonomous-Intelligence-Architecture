/**
 * src/crystals/db/index.ts
 * Crystal Database Barrel
 *
 * Re-exports:
 *   - CrystalRecord schema + all sub-types
 *   - All batch data arrays
 *   - Merged master registry
 *   - Metaphysical constants (GAIA modules, angel numbers, archetypes, elements, harmonic policy)
 *
 * Usage:
 *   import { CRYSTAL_REGISTRY, CrystalRecord } from '@/crystals/db';
 *   import { queryCrystals, GAIA_MODULES, ANGEL_NUMBER_MAP } from '@/crystals/db';
 *
 * NOTE: Batch files use `export default` — we import as default and
 * re-export as named so consumers can import by batch name if needed.
 *
 * Changelog:
 *   2026-05-29 (v1.0)  — Initial barrel
 *   2026-05-29 (v1.1)  — Added queryCrystals engine
 *   2026-05-29 (v1.2)  — Wired metaphysical.data.ts; added color_temperature_k,
 *                         numerology, and zodiac query filters
 */

export type {
  CrystalRecord,
  PhysicalRecord,
  OpticalRecord,
  ColorRecord,
  MetaphysicalRecord,
  MetaphysicalProfile,
  RefractiveIndexValues,
  WavelengthRange,
  OKLCHValue,
  ColorHarmonics,
  CrystalQuery,
  CrystalMatrixResult,
  Chakra,
  Element,
  OpticalType,
  IMAStatus,
  GAIAModule,
  ColorLayer,
  AngelNumber,
} from './crystal.schema';

// ─── Metaphysical constants ───────────────────────────────────────────────────
export type {
  GAIAModuleDefinition,
  AngelNumberDefinition,
  ArchetypeDefinition,
  ElementProfile,
} from './metaphysical.data';

export {
  GAIA_MODULES,
  CHAKRA_MODULE_MAP,
  ANGEL_NUMBER_REGISTRY,
  ANGEL_NUMBER_MAP,
  ARCHETYPE_GLOSSARY,
  ELEMENT_PROFILES,
  HARMONIC_POLICY,
} from './metaphysical.data';

// ─── Batch imports (default) ──────────────────────────────────────────────────
import BATCH_A3 from './batch-a3.data';
import BATCH_A4 from './batch-a4.data';
import BATCH_A5 from './batch-a5.data';
import BATCH_A6 from './batch-a6.data';
import BATCH_A7 from './batch-a7.data';
import BATCH_A8 from './batch-a8.data';
import BATCH_B1 from './batch-b1.data';
import BATCH_B2 from './batch-b2.data';
import BATCH_B3 from './batch-b3.data';
import type { CrystalRecord, CrystalQuery } from './crystal.schema';

// ─── Re-export batches as named exports ───────────────────────────────────────
export { BATCH_A3, BATCH_A4, BATCH_A5, BATCH_A6, BATCH_A7, BATCH_A8, BATCH_B1, BATCH_B2, BATCH_B3 };

// ─── Master registry ──────────────────────────────────────────────────────────
export const CRYSTAL_REGISTRY: CrystalRecord[] = [
  ...BATCH_A3,
  ...BATCH_A4,
  ...BATCH_A5,
  ...BATCH_A6,
  ...BATCH_A7,
  ...BATCH_A8,
  ...BATCH_B1,
  ...BATCH_B2,
  ...BATCH_B3,
  // future batches appended here — A-1, A-2 pending
];

// ─── Query engine ─────────────────────────────────────────────────────────────
/**
 * queryCrystals
 *
 * Filter CRYSTAL_REGISTRY (or any CrystalRecord[]) using a CrystalQuery object.
 * All filter fields are optional and combinable (AND logic).
 * Returns all matching CrystalRecord entries.
 *
 * New in v1.2:
 *   - color_temperature_min / color_temperature_max  (K range filter)
 *   - numerology                                     (exact match)
 *   - zodiac                                         (any-of match)
 *
 * @example
 *   queryCrystals({ chakra: ['Heart'], element: ['Water'], safe_for_water: true })
 *   queryCrystals({ gaia_module: ['ClarusLens'], color_temperature_min: 7000 })
 *   queryCrystals({ angel_number: 777 })
 *   queryCrystals({ zodiac: ['Aquarius'], trade_name: false })
 */
export function queryCrystals(
  query: CrystalQuery & {
    /** Filter to stones whose color_temperature_k >= this value (inclusive). */
    color_temperature_min?: number | null;
    /** Filter to stones whose color_temperature_k <= this value (inclusive). */
    color_temperature_max?: number | null;
    /** Filter to stones matching this exact numerology value. */
    numerology?: number | null;
    /** Filter to stones assigned to any of these zodiac signs. */
    zodiac?: string[] | null;
  },
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(crystal => {
    const m = crystal.metaphysical;
    const p = crystal.physical;
    const o = crystal.optical;
    const c = crystal.color;

    // ── Chakra ───────────────────────────────────────────────────────────────
    if (query.chakra?.length) {
      const allChakras = [m.chakra_primary, ...m.chakra_secondary];
      if (!query.chakra.some(ch => allChakras.includes(ch))) return false;
    }

    // ── Element ──────────────────────────────────────────────────────────────
    if (query.element?.length) {
      if (!query.element.some(e => m.element.includes(e))) return false;
    }

    // ── GAIA module ──────────────────────────────────────────────────────────
    if (query.gaia_module?.length) {
      if (!query.gaia_module.some(mod => m.gaia_resonance.includes(mod))) return false;
    }

    // ── Hardness range ───────────────────────────────────────────────────────
    if (query.min_hardness != null) {
      if ((p.hardness_max ?? 0) < query.min_hardness) return false;
    }
    if (query.max_hardness != null) {
      if ((p.hardness_min ?? 99) > query.max_hardness) return false;
    }

    // ── Physical flags ───────────────────────────────────────────────────────
    if (query.piezoelectric != null) {
      if (p.piezoelectric !== query.piezoelectric) return false;
    }
    if (query.safe_for_hardware != null) {
      if (p.safe_for_hardware !== query.safe_for_hardware) return false;
    }
    if (query.safe_for_water != null) {
      if (p.safe_for_water !== query.safe_for_water) return false;
    }

    // ── Record-level flags ───────────────────────────────────────────────────
    if (query.trade_name != null) {
      if (crystal.trade_name !== query.trade_name) return false;
    }
    if (query.color_layer != null) {
      if (crystal.color_layer !== query.color_layer) return false;
    }
    if (query.has_yin_yang_pair != null) {
      const hasPair = crystal.yin_yang_pair !== null;
      if (hasPair !== query.has_yin_yang_pair) return false;
    }

    // ── Angel number ─────────────────────────────────────────────────────────
    if (query.angel_number != null) {
      if (m.angel_number !== query.angel_number) return false;
    }

    // ── Wavelength ───────────────────────────────────────────────────────────
    if (query.wavelength_min != null || query.wavelength_max != null) {
      const wl = o.visible_wavelength_nm;
      if (!wl) return false;
      if (query.wavelength_min != null && wl.max < query.wavelength_min) return false;
      if (query.wavelength_max != null && wl.min > query.wavelength_max) return false;
    }

    // ── OKLCH hue ────────────────────────────────────────────────────────────
    if (query.oklch_hue_min != null || query.oklch_hue_max != null) {
      const h = crystal.color.oklch.h;
      if (query.oklch_hue_min != null && h < query.oklch_hue_min) return false;
      if (query.oklch_hue_max != null && h > query.oklch_hue_max) return false;
    }

    // ── Color temperature (K) ─────────────────────────────────────────────── NEW v1.2
    if (query.color_temperature_min != null) {
      if (c.color_temperature_k == null) return false;
      if (c.color_temperature_k < query.color_temperature_min) return false;
    }
    if (query.color_temperature_max != null) {
      if (c.color_temperature_k == null) return false;
      if (c.color_temperature_k > query.color_temperature_max) return false;
    }

    // ── Numerology ────────────────────────────────────────────────────────── NEW v1.2
    if (query.numerology != null) {
      if (m.numerology !== query.numerology) return false;
    }

    // ── Zodiac ────────────────────────────────────────────────────────────── NEW v1.2
    if (query.zodiac?.length) {
      if (!query.zodiac.some(z => m.zodiac.includes(z))) return false;
    }

    return true;
  });
}

// ─── Convenience helpers ──────────────────────────────────────────────────────

/**
 * getCrystalByName
 * Case-insensitive exact name lookup across the full registry.
 */
export function getCrystalByName(
  name: string,
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord | undefined {
  const target = name.toLowerCase().trim();
  return registry.find(c => c.name.toLowerCase() === target);
}

/**
 * getCrystalsByModule
 * Returns all crystals whose gaia_resonance string includes the given module.
 */
export function getCrystalsByModule(
  module: import('./crystal.schema').GAIAModule,
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(c => c.metaphysical.gaia_resonance.includes(module));
}

/**
 * getToxicCrystals
 * Returns all crystals with a non-null safety_warning — useful for UI
 * warning overlays and hardware placement validation.
 */
export function getToxicCrystals(
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(c => c.metaphysical.safety_warning !== null);
}

/**
 * getPiezoelectricCrystals
 * Returns all crystals where physical.piezoelectric === true.
 * Used by GAIA hardware placement engine to route piezo signals.
 */
export function getPiezoelectricCrystals(
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(c => c.physical.piezoelectric === true);
}
