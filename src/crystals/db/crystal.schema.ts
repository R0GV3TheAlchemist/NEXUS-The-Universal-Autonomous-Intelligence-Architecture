/**
 * crystal.schema.ts
 * TypeScript types for GAIA-OS Crystal Database.
 *
 * Scientific layers (Mindat, RRUFF) mirror real API response shapes.
 * Metaphysical layer is clearly marked as interpretive/traditional — not scientific.
 *
 * Sources:
 *   Mindat API v1:  https://api.mindat.org/v1/
 *   RRUFF Project:  https://rruff.info/
 *   OpenMindat fields reference: github.com/ChuBL/How-to-Use-Mindat-API
 */

// ─────────────────────────────────────────────
// MINDAT — Physical & Crystallographic Data
// ─────────────────────────────────────────────

/** Crystal systems as defined by IMA / Mindat */
export type CrystalSystem =
  | 'Triclinic'
  | 'Monoclinic'
  | 'Orthorhombic'
  | 'Tetragonal'
  | 'Trigonal'
  | 'Hexagonal'
  | 'Isometric'
  | 'Amorphous'
  | 'Unknown';

/** Luster types as catalogued in Mindat */
export type Luster =
  | 'Adamantine'
  | 'Dull'
  | 'Greasy'
  | 'Metallic'
  | 'Pearly'
  | 'Resinous'
  | 'Silky'
  | 'Sub-Adamantine'
  | 'Sub-Metallic'
  | 'Sub-Resinous'
  | 'Sub-Vitreous'
  | 'Vitreous'
  | 'Waxy'
  | string;

/** Diaphaneity (transparency) values */
export type Diaphaneity = 'Opaque' | 'Translucent' | 'Transparent' | string;

/**
 * MindatMineral
 * Mirrors the Mindat API v1 /minerals/ endpoint response.
 * Fields sourced from: api.mindat.org/schema/redoc and OpenMindat field list.
 * Non-exhaustive — includes fields relevant to GAIA-OS crystal database.
 */
export interface MindatMineral {
  /** Mindat internal integer ID */
  id: number;
  /** Mindat long-form unique ID string */
  longid: string;
  /** GUID */
  guid: string;
  /** IMA-approved mineral name */
  name: string;
  /** IMA chemical formula (may include Unicode) */
  ima_formula: string | null;
  /** Mindat display formula */
  mindat_formula: string | null;
  /** IMA approval status: 'A' = approved, 'N' = not approved, 'Q' = questionable */
  ima_status: 'A' | 'N' | 'Q' | null;
  /** IMA approval year */
  ima_year: number | null;
  /** Strunz 10th edition classification code */
  strunzten: string | null;
  /** Dana 8th edition classification code */
  dana8ed: string | null;
  /** Crystal system string */
  crystal_system: CrystalSystem | null;
  /** Mohs hardness min */
  hardness_min: number | null;
  /** Mohs hardness max */
  hardness_max: number | null;
  /** Specific gravity min */
  specific_gravity_min: number | null;
  /** Specific gravity max */
  specific_gravity_max: number | null;
  /** Cleavage description */
  cleavage: string | null;
  /** Fracture type */
  fracture: string | null;
  /** Tenacity */
  tenacity: string | null;
  /** Luster types array */
  luster: Luster[] | null;
  /** Diaphaneity */
  diaphaneity: Diaphaneity[] | null;
  /** Colour description (free text) */
  colour: string | null;
  /** Streak colour */
  streak: string | null;
  /** Fluorescence under UV */
  fluorescence: string | null;
  /** Refractive index min */
  ri_min: number | null;
  /** Refractive index max */
  ri_max: number | null;
  /** Birefringence value */
  birefringence: number | null;
  /** Optical type: U = uniaxial, B = biaxial, I = isotropic */
  optical_type: 'U' | 'B' | 'I' | null;
  /** Short description text from Mindat */
  shortdesc: string | null;
  /** Last update timestamp */
  updttime: string | null;
  /** Mindat page URL slug */
  mindat_url: string | null;
}

// ─────────────────────────────────────────────
// RRUFF — Light & Spectral Data
// ─────────────────────────────────────────────

/**
 * RruffSpectrum
 * A single Raman or XRD spectrum entry from the RRUFF database.
 * Source: rruff.info
 */
export interface RruffSpectrum {
  /** RRUFF sample ID (e.g. "R040031") */
  rruff_id: string;
  /** Mineral name as catalogued in RRUFF */
  name: string;
  /** Spectrum type */
  spectrum_type: 'Raman' | 'Infrared' | 'XRD';
  /** Laser wavelength used (nm) — Raman only */
  laser_wavelength_nm?: number | null;
  /** URL to raw spectrum data file on rruff.info */
  data_url: string;
  /** URL to sample photo on rruff.info */
  photo_url: string | null;
  /** Locality of the sample */
  locality: string | null;
  /** Source/owner of the sample */
  source: string | null;
}

/**
 * RruffOpticalData
 * Optical and light-interaction properties sourced from RRUFF / literature.
 */
export interface RruffOpticalData {
  mineral_name: string;
  /** Refractive index values */
  refractive_index: {
    n_alpha?: number | null;
    n_beta?:  number | null;
    n_gamma?: number | null;
    n_omega?: number | null;
    n_epsilon?: number | null;
  };
  /** Birefringence (delta) */
  birefringence: number | null;
  /** Optical sign: '+' positive, '-' negative */
  optical_sign: '+' | '-' | null;
  /** Dispersion description */
  dispersion: string | null;
  /** Pleochroism description */
  pleochroism: string | null;
  /** Fluorescence under longwave UV */
  fluorescence_lw: string | null;
  /** Fluorescence under shortwave UV */
  fluorescence_sw: string | null;
  /** Phosphorescence */
  phosphorescence: string | null;
  /** Dominant visible wavelength range in nm (approximate) */
  visible_wavelength_nm: { min: number; max: number } | null;
  /** Available RRUFF spectra for this mineral */
  spectra: RruffSpectrum[];
}

// ─────────────────────────────────────────────
// COLOR THEORY — Derived Layer
// ─────────────────────────────────────────────

/**
 * CrystalColorProfile
 * Maps the mineral's physical colour to color science.
 * OKLCH values are computed from the dominant visible wavelength.
 * Psychological effects sourced from established color psychology literature.
 */
export interface CrystalColorProfile {
  /** Primary color name (e.g. "violet", "rose", "golden") */
  primary_color: string;
  /** All documented color variants for this mineral */
  color_variants: string[];
  /** Dominant wavelength in nanometers (visible spectrum 380–700nm) */
  dominant_wavelength_nm: number | null;
  /** OKLCH representation of the dominant color
   *  L = lightness 0–1, C = chroma 0–0.4, H = hue angle 0–360 */
  oklch: { l: number; c: number; h: number } | null;
  /** Hex representation for display (derived from OKLCH) */
  hex: string | null;
  /** Munsell notation if applicable */
  munsell: string | null;
  /** Color temperature in Kelvin (warm / neutral / cool) */
  color_temperature_k: number | null;
  /** Psychological associations — sourced from Luscher, Birren, Itten */
  psychological_effects: string[];
  /** Color harmony relationships (complementary, triadic, etc.) */
  harmonics: {
    complementary_hue: number | null;
    triadic_hues: [number, number] | null;
    analogous_range: [number, number] | null;
  };
}

// ─────────────────────────────────────────────
// METAPHYSICAL — Interpretive / Traditional Layer
// ─────────────────────────────────────────────

/**
 * ⚠️  INTERPRETIVE LAYER
 * This data is sourced from documented cultural, spiritual, and metaphysical
 * traditions (Vedic chakra system, Western esotericism, crystal healing
 * literature). It is NOT scientifically validated. It is preserved here
 * as a cross-cultural knowledge layer within GAIA-OS.
 */

export type Chakra =
  | 'Root'
  | 'Sacral'
  | 'Solar Plexus'
  | 'Heart'
  | 'Throat'
  | 'Third Eye'
  | 'Crown'
  | 'Higher Crown'
  | 'Earth Star';

export type Element = 'Earth' | 'Water' | 'Fire' | 'Air' | 'Aether' | 'Storm';

export type Planet =
  | 'Sun' | 'Moon' | 'Mercury' | 'Venus' | 'Mars'
  | 'Jupiter' | 'Saturn' | 'Uranus' | 'Neptune' | 'Pluto' | 'Earth';

export type Archetype =
  | 'Warrior'
  | 'Healer'
  | 'Sage'
  | 'Mystic'
  | 'Sovereign'
  | 'Lover'
  | 'Creator'
  | 'Trickster'
  | 'Guardian'
  | 'Alchemist'
  | 'Oracle'
  | 'Empath'   // added: covers empathic/oceanic stones (e.g. Abalone Shell)
  | 'Guide';   // added: covers way-finding / navigational stones (e.g. Afghanite, Adularia)

export type ZodiacSign =
  | 'Aries' | 'Taurus' | 'Gemini' | 'Cancer' | 'Leo' | 'Virgo'
  | 'Libra' | 'Scorpio' | 'Sagittarius' | 'Capricorn' | 'Aquarius' | 'Pisces';

/** ⚠️ INTERPRETIVE — See above notice */
export interface MetaphysicalProfile {
  mineral_name: string;
  /** Primary chakra association */
  chakra_primary: Chakra;
  /** Secondary chakra associations */
  chakra_secondary: Chakra[];
  /** Elemental correspondence */
  element: Element[];
  /** Planetary rulership */
  planet: Planet[];
  /** Jungian / archetypal correspondence */
  archetype: Archetype[];
  /** Zodiac signs traditionally associated */
  zodiac: ZodiacSign[];
  /** Numerological vibration (1–9, 11, 22, 33) */
  numerology: number | null;
  /** Core energetic intention / keyword */
  intention: string;
  /** Healing traditions that reference this stone */
  traditions: string[];
  /** Key metaphysical properties as documented in crystal literature */
  properties: string[];
  /** Suggested use within GAIA-OS (e.g. grounding, clarity, dreaming) */
  gaia_resonance: string;
  /**
   * ⚠️ SAFETY — Physical handling/elixir warnings.
   * null = no known hazard.
   * Present = do NOT create water elixirs; follow instructions for hardware nodes.
   */
  safety_warning?: string | null;
}

// ─────────────────────────────────────────────
// UNIFIED CRYSTAL RECORD
// ─────────────────────────────────────────────

/**
 * CrystalRecord
 * The unified record merging all four database layers.
 * Each layer is optional — records can be partial when data isn't available.
 */
export interface CrystalRecord {
  /** Canonical mineral name (from IMA / Mindat) */
  name: string;
  /** Mindat ID for API lookups */
  mindat_id: number | null;
  /** RRUFF sample IDs for this mineral */
  rruff_ids: string[];
  /** Physical and crystallographic data — from Mindat */
  physical: MindatMineral | null;
  /** Light and spectral data — from RRUFF */
  optical: RruffOpticalData | null;
  /** Color science layer — derived */
  color: CrystalColorProfile | null;
  /** ⚠️ Interpretive/traditional metaphysical layer */
  metaphysical: MetaphysicalProfile | null;
  /** ISO timestamp of last data sync */
  last_synced: string | null;
}
