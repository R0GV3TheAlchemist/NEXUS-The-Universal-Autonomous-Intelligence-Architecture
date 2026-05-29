/**
 * src/crystals/db/index.ts
 * Crystal Database Barrel
 *
 * Re-exports:
 *   - CrystalRecord schema + all sub-types
 *   - All batch data arrays
 *   - Merged master registry
 *
 * Usage:
 *   import { CRYSTAL_REGISTRY, CrystalRecord } from '@/crystals/db';
 *   import { queryCrystals } from '@/crystals/db';
 */

export type {
  CrystalRecord,
  PhysicalRecord,
  OpticalRecord,
  ColorRecord,
  MetaphysicalRecord,
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
} from './crystal.schema';

export { BATCH_A4 } from './batch-a4.data';

/**
 * Master crystal registry — all batches merged.
 * Import this for full-database queries.
 */
import { BATCH_A4 } from './batch-a4.data';
import type { CrystalRecord, CrystalQuery } from './crystal.schema';

export const CRYSTAL_REGISTRY: CrystalRecord[] = [
  ...BATCH_A4,
  // future batches appended here
];

// ─────────────────────────────────────────────────────────────────────────────
// QUERY ENGINE — basic multi-dimensional filter
// ─────────────────────────────────────────────────────────────────────────────

/**
 * queryCrystals(query)
 *
 * Filter the registry by any combination of CrystalQuery fields.
 * Each provided field narrows the result — omitted fields are ignored.
 *
 * Example:
 *   queryCrystals({ chakra: ['Third Eye'], safe_for_hardware: true })
 */
export function queryCrystals(
  query: CrystalQuery,
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(crystal => {
    const m = crystal.metaphysical;
    const p = crystal.physical;
    const o = crystal.optical;

    // Chakra filter — primary or secondary must match any in query list
    if (query.chakra?.length) {
      const allChakras = [m.chakra_primary, ...m.chakra_secondary];
      if (!query.chakra.some(c => allChakras.includes(c))) return false;
    }

    // Element filter
    if (query.element?.length) {
      if (!query.element.some(e => m.element.includes(e))) return false;
    }

    // GAIA module filter — match substring in gaia_resonance string
    if (query.gaia_module?.length) {
      if (!query.gaia_module.some(mod => m.gaia_resonance.includes(mod))) return false;
    }

    // Hardness filter
    if (query.min_hardness != null) {
      if ((p.hardness_max ?? 0) < query.min_hardness) return false;
    }
    if (query.max_hardness != null) {
      if ((p.hardness_min ?? 99) > query.max_hardness) return false;
    }

    // Safety — hardware use (no asbestos, no toxic dust, no soluble toxins)
    if (query.safe_for_hardware === true) {
      if (m.safety_warning !== null) return false;
    }

    // Safety — water elixir use
    if (query.safe_for_water === true) {
      const w = m.safety_warning?.toLowerCase() ?? '';
      if (w.includes('water') || w.includes('toxic') || w.includes('soluble') || w.includes('asbestos')) return false;
    }

    // Wavelength filter
    if (query.wavelength_min != null || query.wavelength_max != null) {
      const wl = o.visible_wavelength_nm;
      if (!wl) return false;
      if (query.wavelength_min != null && wl.max < query.wavelength_min) return false;
      if (query.wavelength_max != null && wl.min > query.wavelength_max) return false;
    }

    // OKLCH hue filter
    if (query.oklch_hue_min != null || query.oklch_hue_max != null) {
      const h = crystal.color.oklch.h;
      if (query.oklch_hue_min != null && h < query.oklch_hue_min) return false;
      if (query.oklch_hue_max != null && h > query.oklch_hue_max) return false;
    }

    return true;
  });
}
