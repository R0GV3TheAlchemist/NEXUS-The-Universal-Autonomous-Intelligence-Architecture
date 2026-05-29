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
 *
 * NOTE: Batch files use `export default` — we import as default and
 * re-export as named so consumers can import by batch name if needed.
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

// ─── Batch imports (default) ──────────────────────────────────────────────────
import BATCH_A3 from './batch-a3.data';
import BATCH_A4 from './batch-a4.data';
import BATCH_A5 from './batch-a5.data';
import BATCH_A6 from './batch-a6.data';
import BATCH_A7 from './batch-a7.data';
import BATCH_A8 from './batch-a8.data';
import BATCH_B1 from './batch-b1.data';
import BATCH_B2 from './batch-b2.data';
import type { CrystalRecord, CrystalQuery } from './crystal.schema';

// ─── Re-export batches as named exports ────────────────────────────────────────
export { BATCH_A3, BATCH_A4, BATCH_A5, BATCH_A6, BATCH_A7, BATCH_A8, BATCH_B1, BATCH_B2 };

// ─── Master registry ─────────────────────────────────────────────────────────
export const CRYSTAL_REGISTRY: CrystalRecord[] = [
  ...BATCH_A3,
  ...BATCH_A4,
  ...BATCH_A5,
  ...BATCH_A6,
  ...BATCH_A7,
  ...BATCH_A8,
  ...BATCH_B1,
  ...BATCH_B2,
  // future batches appended here
];

// ─── Query engine ─────────────────────────────────────────────────────────────
export function queryCrystals(
  query: CrystalQuery,
  registry: CrystalRecord[] = CRYSTAL_REGISTRY
): CrystalRecord[] {
  return registry.filter(crystal => {
    const m = crystal.metaphysical;
    const p = crystal.physical;
    const o = crystal.optical;

    if (query.chakra?.length) {
      const allChakras = [m.chakra_primary, ...m.chakra_secondary];
      if (!query.chakra.some(c => allChakras.includes(c))) return false;
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

    return true;
  });
}
