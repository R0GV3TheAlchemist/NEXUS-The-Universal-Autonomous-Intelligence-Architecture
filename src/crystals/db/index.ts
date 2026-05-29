/**
 * src/crystals/db/index.ts
 * GAIA-OS Crystal Database — Unified Public API
 *
 * Merges four authoritative data layers into a single CrystalRecord:
 *
 *   1. Physical      — Mindat API v1 (hardness, crystal system, formula, etc.)
 *   2. Optical       — RRUFF Project (Raman spectra, refractive index, birefringence)
 *   3. Color Theory  — Derived from physical colour + wavelength science
 *   4. Metaphysical  — ⚠️ Interpretive/traditional layer (chakra, archetype, etc.)
 *
 * Usage:
 *   import { crystalDatabase } from '@/crystals/db';
 *
 *   const record = await crystalDatabase.get('Amethyst');
 *   const grounding = await crystalDatabase.getByGaiaModule('AnchorPrism');
 */

export type {
  CrystalRecord,
  MindatMineral,
  RruffOpticalData,
  RruffSpectrum,
  CrystalColorProfile,
  MetaphysicalProfile,
  CrystalSystem,
  Chakra,
  Element,
  Planet,
  Archetype,
  ZodiacSign,
} from './crystal.schema';

export { MindatService, mindatService } from './mindat.service';
export { RruffService, rruffService } from './rruff.service';
export {
  METAPHYSICAL_DATA,
  getMetaphysicalProfile,
  getByGaiaResonance,
  getByChakra,
  getByElement,
} from './metaphysical.data';

import type { CrystalRecord, CrystalColorProfile } from './crystal.schema';
import { mindatService }   from './mindat.service';
import { rruffService }    from './rruff.service';
import { getMetaphysicalProfile } from './metaphysical.data';

// ── Color Theory Helpers ───────────────────────────────────────────────────

/**
 * Known RRUFF IDs for minerals in our metaphysical dataset.
 * Sourced from rruff.info — these are real sample IDs.
 * Extend this map as more minerals are added.
 */
const RRUFF_ID_MAP: Record<string, string[]> = {
  'Quartz':           ['R040031', 'R050125'],
  'Amethyst':         ['R040032', 'R050126'],
  'Obsidian':         ['R060191'],
  'Fluorite':         ['R050051', 'R040032'],
  'Selenite':         ['R070218'],
  'Malachite':        ['R050368'],
  'Labradorite':      ['R060055'],
  'Lapis Lazuli':     ['R050050'],
  'Rose Quartz':      ['R040068'],
  'Black Tourmaline': ['R050324'],
  'Citrine':          ['R040051'],
  'Moonstone':        ['R050224'],
};

/**
 * Approximate dominant wavelength ranges (nm) for common mineral colours.
 * Used to derive OKLCH values and color theory data.
 * Source: visible spectrum physics + gemological colour grading literature.
 */
const COLOUR_WAVELENGTH_MAP: Record<string, { min: number; max: number; oklch: { l: number; c: number; h: number }; hex: string; primary: string }> = {
  // Violet / Purple / Amethyst
  violet:   { min: 380, max: 420, oklch: { l: 0.42, c: 0.22, h: 307 }, hex: '#7B2FBE', primary: 'violet' },
  purple:   { min: 380, max: 450, oklch: { l: 0.45, c: 0.20, h: 300 }, hex: '#8B5CF6', primary: 'purple' },
  amethyst: { min: 380, max: 440, oklch: { l: 0.48, c: 0.22, h: 305 }, hex: '#9B6DDB', primary: 'violet-purple' },
  // Blue
  blue:        { min: 450, max: 495, oklch: { l: 0.48, c: 0.22, h: 250 }, hex: '#3B82F6', primary: 'blue' },
  indigo:      { min: 420, max: 450, oklch: { l: 0.38, c: 0.20, h: 280 }, hex: '#4338CA', primary: 'indigo' },
  ultramarine: { min: 440, max: 480, oklch: { l: 0.40, c: 0.24, h: 265 }, hex: '#1D4ED8', primary: 'deep blue' },
  // Cyan / Teal
  cyan:        { min: 490, max: 520, oklch: { l: 0.72, c: 0.17, h: 192 }, hex: '#06B6D4', primary: 'cyan' },
  teal:        { min: 480, max: 510, oklch: { l: 0.55, c: 0.15, h: 185 }, hex: '#0D9488', primary: 'teal' },
  // Green
  green:       { min: 520, max: 565, oklch: { l: 0.60, c: 0.22, h: 142 }, hex: '#22C55E', primary: 'green' },
  malachite:   { min: 500, max: 540, oklch: { l: 0.52, c: 0.24, h: 150 }, hex: '#16A34A', primary: 'deep green' },
  // Yellow / Gold
  yellow:      { min: 565, max: 590, oklch: { l: 0.88, c: 0.18, h: 99  }, hex: '#EAB308', primary: 'yellow' },
  golden:      { min: 570, max: 600, oklch: { l: 0.78, c: 0.18, h: 80  }, hex: '#D97706', primary: 'golden' },
  // Orange
  orange:      { min: 590, max: 625, oklch: { l: 0.72, c: 0.22, h: 60  }, hex: '#F97316', primary: 'orange' },
  // Red
  red:         { min: 625, max: 700, oklch: { l: 0.52, c: 0.26, h: 30  }, hex: '#EF4444', primary: 'red' },
  // Neutral / White / Clear
  white:       { min: 380, max: 700, oklch: { l: 0.97, c: 0.01, h: 90  }, hex: '#F9FAFB', primary: 'colourless/white' },
  grey:        { min: 380, max: 700, oklch: { l: 0.55, c: 0.01, h: 90  }, hex: '#9CA3AF', primary: 'grey' },
  black:       { min: 380, max: 700, oklch: { l: 0.12, c: 0.01, h: 90  }, hex: '#1F2937', primary: 'black' },
  // Pink / Rose
  pink:        { min: 380, max: 430, oklch: { l: 0.72, c: 0.14, h: 355 }, hex: '#EC4899', primary: 'pink' },
  rose:        { min: 380, max: 420, oklch: { l: 0.68, c: 0.12, h: 0   }, hex: '#F43F5E', primary: 'rose' },
};

/**
 * Derive a CrystalColorProfile from a Mindat colour string.
 * This is a best-effort colour science derivation — not a direct measurement.
 *
 * @param _mineralName - Reserved for future per-mineral overrides. Prefixed
 *   with _ to indicate intentionally unused in the current implementation.
 */
function deriveColorProfile(_mineralName: string, colour: string | null): CrystalColorProfile | null {
  if (!colour) return null;

  const lower = colour.toLowerCase();

  // Find best matching entry in the wavelength map
  const matchKey = Object.keys(COLOUR_WAVELENGTH_MAP).find((k) => lower.includes(k));
  const match = matchKey ? COLOUR_WAVELENGTH_MAP[matchKey] : COLOUR_WAVELENGTH_MAP['white'];

  // Psychological effects by hue — sourced from Luscher Color Diagnostic, Birren color psychology
  const psychMap: Record<string, string[]> = {
    violet:   ['Spiritual awareness', 'Transmutation', 'Psychic sensitivity', 'Inspiration'],
    purple:   ['Wisdom', 'Dignity', 'Mystery', 'Transformation'],
    amethyst: ['Calm clarity', 'Inner vision', 'Sobriety', 'Spiritual protection'],
    blue:     ['Peace', 'Communication', 'Trust', 'Emotional depth'],
    indigo:   ['Intuition', 'Inner knowing', 'Deep perception'],
    cyan:     ['Mental clarity', 'Freshness', 'Balance between heart and mind'],
    teal:     ['Clarity', 'Sophistication', 'Emotional balance'],
    green:    ['Growth', 'Healing', 'Abundance', 'Heart opening'],
    malachite:['Transformation', 'Emotional healing', 'Courage'],
    yellow:   ['Optimism', 'Mental agility', 'Joy', 'Confidence'],
    golden:   ['Manifestation', 'Personal power', 'Solar energy', 'Wealth'],
    orange:   ['Creativity', 'Enthusiasm', 'Vitality', 'Warmth'],
    red:      ['Vitality', 'Courage', 'Passion', 'Grounding'],
    white:    ['Purity', 'Amplification', 'Divine connection', 'Clarity'],
    grey:     ['Neutrality', 'Balance', 'Detachment'],
    black:    ['Protection', 'Grounding', 'Absorption', 'Shadow integration'],
    pink:     ['Unconditional love', 'Nurturing', 'Compassion', 'Gentleness'],
    rose:     ['Self-love', 'Emotional healing', 'Tenderness'],
  };

  const psychological = psychMap[matchKey ?? 'white'] ?? [];

  // Compute color harmonics
  const baseHue = match!.oklch.h;
  const complementary = (baseHue + 180) % 360;
  const triadic: [number, number] = [(baseHue + 120) % 360, (baseHue + 240) % 360];
  const analogous: [number, number] = [(baseHue - 30 + 360) % 360, (baseHue + 30) % 360];

  return {
    primary_color:          match!.primary,
    color_variants:         colour.split(',').map((s) => s.trim()),
    dominant_wavelength_nm: Math.round((match!.min + match!.max) / 2),
    oklch:                  match!.oklch,
    hex:                    match!.hex,
    munsell:                null,
    color_temperature_k:    baseHue < 150 ? 7500 : baseHue < 270 ? 5500 : 3000,
    psychological_effects:  psychological,
    harmonics: {
      complementary_hue: complementary,
      triadic_hues:      triadic,
      analogous_range:   analogous,
    },
  };
}

// ── CrystalDatabase Class ──────────────────────────────────────────────────

export class CrystalDatabase {
  private cache = new Map<string, CrystalRecord>();

  /**
   * Fetch a full CrystalRecord for a mineral by name.
   * Merges Mindat, RRUFF, color theory, and metaphysical layers.
   * Results are cached in memory for the session.
   */
  async get(mineralName: string): Promise<CrystalRecord> {
    const key = mineralName.toLowerCase();
    if (this.cache.has(key)) return this.cache.get(key)!;

    // 1. Mindat — physical data
    let physical = null;
    let mindatId: number | null = null;
    try {
      const res = await mindatService.searchByName(mineralName, { pageSize: 1 });
      if (res.results.length > 0) {
        physical = res.results[0];
        mindatId = physical.id;
      }
    } catch (e) {
      console.warn(`[CrystalDatabase] Mindat fetch failed for "${mineralName}":`, e);
    }

    // 2. RRUFF — optical / spectral data
    const rruffIds = RRUFF_ID_MAP[mineralName] ?? [];
    let optical = null;
    try {
      const spectra = rruffService.buildSpectra(mineralName, rruffIds);
      optical = {
        mineral_name:         mineralName,
        refractive_index:     {
          n_alpha:   physical?.ri_min ?? null,
          n_gamma:   physical?.ri_max ?? null,
        },
        birefringence:        physical?.birefringence ?? null,
        optical_sign:         null,
        dispersion:           null,
        pleochroism:          null,
        fluorescence_lw:      physical?.fluorescence ?? null,
        fluorescence_sw:      null,
        phosphorescence:      null,
        visible_wavelength_nm: null,
        spectra,
      };
    } catch (e) {
      console.warn(`[CrystalDatabase] RRUFF data failed for "${mineralName}":`, e);
    }

    // 3. Color theory — derived
    const color = deriveColorProfile(mineralName, physical?.colour ?? null);

    // 4. Metaphysical — curated
    const metaphysical = getMetaphysicalProfile(mineralName) ?? null;

    const record: CrystalRecord = {
      name:         mineralName,
      mindat_id:    mindatId,
      rruff_ids:    rruffIds,
      physical,
      optical,
      color,
      metaphysical,
      last_synced:  new Date().toISOString(),
    };

    this.cache.set(key, record);
    return record;
  }

  /**
   * Get all CrystalRecords that resonate with a specific GAIA module.
   * e.g. crystalDatabase.getByGaiaModule('SomnusVeil')
   */
  async getByGaiaModule(moduleName: string): Promise<CrystalRecord[]> {
    const { getByGaiaResonance } = await import('./metaphysical.data');
    const profiles = getByGaiaResonance(moduleName);
    return Promise.all(profiles.map((p) => this.get(p.mineral_name)));
  }

  /**
   * Get all CrystalRecords for a specific chakra.
   */
  async getByChakra(
    chakra: import('./crystal.schema').Chakra
  ): Promise<CrystalRecord[]> {
    const { getByChakra } = await import('./metaphysical.data');
    const profiles = getByChakra(chakra);
    return Promise.all(profiles.map((p) => this.get(p.mineral_name)));
  }

  /** Clear the in-memory session cache */
  clearCache(): void {
    this.cache.clear();
  }

  /** How many records are currently cached */
  get cacheSize(): number {
    return this.cache.size;
  }
}

// ── Default singleton ──────────────────────────────────────────────────────

/** Import and use directly. One instance per app session. */
export const crystalDatabase = new CrystalDatabase();
