/**
 * src/crystals/db/index.ts
 * Crystal Database Barrel
 *
 * Re-exports:
 *   - CrystalRecord schema + all sub-types
 *   - All batch data arrays
 *   - Merged master registry
 *   - Metaphysical constants
 *
 * Changelog:
 *   2026-05-29 (v1.0)  — Initial barrel
 *   2026-05-29 (v1.1)  — Added queryCrystals engine
 *   2026-05-29 (v1.2)  — Wired metaphysical.data.ts
 *   2026-06-01 (v1.3)  — Added ALL_CRYSTALS alias for crystal.index.ts compatibility
 *                      — Imported remaining B-series and C-series batches
 *                      — Exported RiskTier, ChakraPoint const objects
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

export { RiskTier, ChakraPoint } from './crystal.schema';

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

// ─── Batch imports ────────────────────────────────────────────────────────────
import BATCH_A3 from './batch-a3.data';
import BATCH_A4 from './batch-a4.data';
import BATCH_A5 from './batch-a5.data';
import BATCH_A6 from './batch-a6.data';
import BATCH_A7 from './batch-a7.data';
import BATCH_A8 from './batch-a8.data';
import BATCH_B1 from './batch-b1.data';
import BATCH_B2 from './batch-b2.data';
import BATCH_B3 from './batch-b3.data';
import BATCH_B4 from './batch-b4.data';
import BATCH_B5 from './batch-b5.data';
import BATCH_B6 from './batch-b6.data';
import BATCH_B7 from './batch-b7.data';
import BATCH_B8 from './batch-b8.data';
import BATCH_B9 from './batch-b9.data';
import BATCH_C1 from './batch-c1.data';
import BATCH_C2 from './batch-c2.data';
import BATCH_C3 from './batch-c3.data';
import BATCH_C4 from './batch-c4.data';
import BATCH_C5 from './batch-c5.data';
import BATCH_C6 from './batch-c6.data';
import BATCH_C7 from './batch-c7.data';
import BATCH_C8A from './batch-c8a.data';
import BATCH_C8B from './batch-c8b.data';
import BATCH_C9A from './batch-c9a.data';
import BATCH_C9B from './batch-c9b.data';
import type { CrystalRecord, CrystalQuery } from './crystal.schema';

// ─── Re-export batches as named exports ───────────────────────────────────────
export {
  BATCH_A3, BATCH_A4, BATCH_A5, BATCH_A6, BATCH_A7, BATCH_A8,
  BATCH_B1, BATCH_B2, BATCH_B3, BATCH_B4, BATCH_B5, BATCH_B6,
  BATCH_B7, BATCH_B8, BATCH_B9,
  BATCH_C1, BATCH_C2, BATCH_C3, BATCH_C4, BATCH_C5, BATCH_C6,
  BATCH_C7, BATCH_C8A, BATCH_C8B, BATCH_C9A, BATCH_C9B,
};

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
  ...BATCH_B4,
  ...BATCH_B5,
  ...BATCH_B6,
  ...BATCH_B7,
  ...BATCH_B8,
  ...BATCH_B9,
  ...BATCH_C1,
  ...BATCH_C2,
  ...BATCH_C3,
  ...BATCH_C4,
  ...BATCH_C5,
  ...BATCH_C6,
  ...BATCH_C7,
  ...BATCH_C8A,
  ...BATCH_C8B,
  ...BATCH_C9A,
  ...BATCH_C9B,
];

/**
 * ALL_CRYSTALS — alias for CRYSTAL_REGISTRY.
 * Consumed by crystal.index.ts for O(1) map construction.
 */
export const ALL_CRYSTALS: CrystalRecord[] = CRYSTAL_REGISTRY;

// ─── Query engine ─────────────────────────────────────────────────────────────
/**
 * queryCrystals
 *
 * Filter CRYSTAL_REGISTRY (or any CrystalRecord[]) using a CrystalQuery object.
 * All filter fields are optional and combinable (AND logic).
 *
 * @example
 *   queryCrystals({ chakra: ['Heart'], element: ['Water'], safe_for_water: true })
 *   queryCrystals({ gaia_module: ['ClarusLens'] })
 *   queryCrystals({ angel_number: 777 })
 */
export function queryCrystals(
  query: CrystalQuery & {
    color_temperature_min?: number | null;
    color_temperature_max?: number | null;
    numerology?: number | null;
    zodiac?: string[] | null;
  },
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(crystal => {
    const m = crystal.metaphysical;
    const p = crystal.physical;
    const o = crystal.optical;
    const c = crystal.color;

    if (query.chakra?.length) {
      const allChakras = [m.chakra_primary, ...m.chakra_secondary];
      if (!query.chakra.some(ch => allChakras.includes(ch))) return false;
    }
    if (query.element?.length) {
      if (!query.element.some(e => m.element.includes(e))) return false;
    }
    if (query.gaia_module?.length) {
      if (!query.gaia_module.some(mod => m.gaia_resonance.includes(mod))) return false;
    }
    if (query.min_hardness != null) {
      if ((p.hardness_max ?? 0) < query.min_hardness) return false;
    }
    if (query.max_hardness != null) {
      if ((p.hardness_min ?? 99) > query.max_hardness) return false;
    }
    if (query.piezoelectric != null) {
      if (p.piezoelectric !== query.piezoelectric) return false;
    }
    if (query.safe_for_hardware != null) {
      if (p.safe_for_hardware !== query.safe_for_hardware) return false;
    }
    if (query.safe_for_water != null) {
      if (p.safe_for_water !== query.safe_for_water) return false;
    }
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
    if (query.angel_number != null) {
      if (m.angel_number !== query.angel_number) return false;
    }
    if (query.wavelength_min != null || query.wavelength_max != null) {
      const wl = o.visible_wavelength_nm;
      if (!wl) return false;
      if (query.wavelength_min != null && wl.max < query.wavelength_min) return false;
      if (query.wavelength_max != null && wl.min > query.wavelength_max) return false;
    }
    if (query.oklch_hue_min != null || query.oklch_hue_max != null) {
      const h = crystal.color.oklch.h;
      if (query.oklch_hue_min != null && h < query.oklch_hue_min) return false;
      if (query.oklch_hue_max != null && h > query.oklch_hue_max) return false;
    }
    if (query.color_temperature_min != null) {
      if (c.color_temperature_k == null) return false;
      if (c.color_temperature_k < query.color_temperature_min) return false;
    }
    if (query.color_temperature_max != null) {
      if (c.color_temperature_k == null) return false;
      if (c.color_temperature_k > query.color_temperature_max) return false;
    }
    if (query.numerology != null) {
      if (m.numerology !== query.numerology) return false;
    }
    if (query.zodiac?.length) {
      if (!query.zodiac.some(z => m.zodiac.includes(z))) return false;
    }

    return true;
  });
}

// ─── Convenience helpers ──────────────────────────────────────────────────────

export function getCrystalByName(
  name: string,
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord | undefined {
  const target = name.toLowerCase().trim();
  return registry.find(c => c.name.toLowerCase() === target);
}

export function getCrystalsByModule(
  module: import('./crystal.schema').GAIAModule,
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(c => c.metaphysical.gaia_resonance.includes(module));
}

export function getToxicCrystals(
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(c => c.metaphysical.safety_warning !== null);
}

export function getPiezoelectricCrystals(
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(c => c.physical.piezoelectric === true);
}
