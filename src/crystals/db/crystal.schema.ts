/**
 * crystal.schema.ts
 * GAIA-OS Crystal Database — Master Type Definitions
 *
 * Three explicit, separated layers per record:
 *   1. PhysicalRecord   — IMA / Mindat mineral science (objective)
 *   2. OpticalRecord    — Light behaviour, wavelengths, spectra (objective)
 *   3. ColorRecord      — Color theory, OKLCH, psychology (interpretive)
 *   4. MetaphysicalRecord — Traditional / esoteric layer (interpretive, clearly marked)
 *
 * ⚠️  The metaphysical layer is explicitly interpretive / traditional.
 *     It is separated from physics so GAIA can reason across both
 *     without conflating them.
 *
 * Updated: 2026-05-29
 */

// ─────────────────────────────────────────────────────────────────────────────
// SHARED PRIMITIVES
// ─────────────────────────────────────────────────────────────────────────────

/** Chakra system names used across all traditions */
export type Chakra =
  | 'Root'
  | 'Sacral'
  | 'Solar Plexus'
  | 'Heart'
  | 'Throat'
  | 'Third Eye'
  | 'Crown'
  | 'Higher Crown'
  | 'Earth Star'
  | 'Soul Star';

/** Classical + expanded elements */
export type Element =
  | 'Earth'
  | 'Water'
  | 'Fire'
  | 'Air'
  | 'Aether'
  | 'Storm'
  | 'Ice'
  | 'Wood'
  | 'Metal';

/** Optical character — uniaxial or biaxial */
export type OpticalType = 'U' | 'B' | 'Isotropic' | null;

/** IMA status codes */
export type IMAStatus = 'A' | 'Rd' | 'Rn' | 'Q' | 'G' | null;

/** GAIA module resonance targets */
export type GAIAModule =
  | 'ClarusLens'
  | 'AnchorPrism'
  | 'SomnusVeil'
  | 'SovereignCore'
  | 'ViriditasHeart'
  | 'Noosphere'
  | 'QuantumNexus';

// ─────────────────────────────────────────────────────────────────────────────
// LAYER 1: PHYSICAL
// ─────────────────────────────────────────────────────────────────────────────

export interface PhysicalRecord {
  /** Internal numeric ID (Mindat-compatible; 0 = not yet synced) */
  id: number;
  /** Mindat longid string */
  longid: string;
  /** Mindat GUID */
  guid: string;

  /** IMA-approved mineral name */
  name: string;
  /** IMA chemical formula (Unicode subscripts/superscripts OK) */
  ima_formula: string;
  /** Mindat-normalised ASCII formula */
  mindat_formula: string;
  /** IMA approval status */
  ima_status: IMAStatus;
  /** Year of IMA approval */
  ima_year: number | null;

  /** Strunz 10th edition classification */
  strunzten: string | null;
  /** Dana 8th edition classification */
  dana8ed: string | null;

  /** Crystal system */
  crystal_system:
    | 'Triclinic'
    | 'Monoclinic'
    | 'Orthorhombic'
    | 'Tetragonal'
    | 'Trigonal'
    | 'Hexagonal'
    | 'Cubic'
    | 'Amorphous'
    | 'Pseudohexagonal';

  /** Mohs hardness range */
  hardness_min: number | null;
  hardness_max: number | null;

  /** Specific gravity range */
  specific_gravity_min: number | null;
  specific_gravity_max: number | null;

  cleavage:    string | null;
  fracture:    string | null;
  tenacity:    string | null;
  luster:      string[];
  diaphaneity: string[];
  colour:      string;
  streak:      string | null;
  fluorescence: string | null;

  /** Refractive index range */
  ri_min: number | null;
  ri_max: number | null;
  birefringence: number | null;
  optical_type: OpticalType;

  /** Short mineralogical description */
  shortdesc: string;
  /** ISO 8601 last Mindat sync timestamp */
  updttime: string | null;
  /** Canonical Mindat URL */
  mindat_url: string | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// LAYER 2: OPTICAL
// ─────────────────────────────────────────────────────────────────────────────

export interface RefractiveIndexValues {
  /** Uniaxial ordinary */
  n_omega?:   number;
  /** Uniaxial extraordinary */
  n_epsilon?: number;
  /** Biaxial alpha */
  n_alpha?:   number;
  /** Biaxial beta */
  n_beta?:    number;
  /** Biaxial gamma */
  n_gamma?:   number;
  /** Single isotropic value */
  n?:         number;
}

export interface WavelengthRange {
  min: number;
  max: number;
}

export interface OpticalRecord {
  mineral_name:     string;
  refractive_index: RefractiveIndexValues;
  birefringence:    number | null;
  /** '+' or '-' optical sign */
  optical_sign:     '+' | '-' | null;
  dispersion:       string | null;
  pleochroism:      string | null;
  fluorescence_lw:  string | null;
  fluorescence_sw:  string | null;
  phosphorescence:  string | null;
  /** Dominant visible wavelength range in nm */
  visible_wavelength_nm: WavelengthRange | null;
  /** RRUFF or other spectral reference IDs */
  spectra: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// LAYER 3: COLOR
// ─────────────────────────────────────────────────────────────────────────────

export interface OKLCHValue {
  /** Perceptual lightness 0–1 */
  l: number;
  /** Chroma 0–0.4 */
  c: number;
  /** Hue angle 0–360 */
  h: number;
}

export interface ColorHarmonics {
  /** Complementary hue angle */
  complementary_hue: number | null;
  /** Triadic hue angles */
  triadic_hues:      [number, number] | null;
  /** Analogous hue range [min, max] */
  analogous_range:   [number, number] | null;
}

export interface ColorRecord {
  primary_color:          string;
  color_variants:         string[];
  /** Dominant wavelength in nm (null for non-spectral / iridescent) */
  dominant_wavelength_nm: number | null;
  /** OKLCH perceptual color value */
  oklch:                  OKLCHValue;
  /** Representative hex value (null for iridescent / multicolor) */
  hex:                    string | null;
  /** Munsell notation */
  munsell:                string | null;
  /** Correlated color temperature in Kelvin */
  color_temperature_k:    number | null;
  /** Established psychological / perceptual effects of this hue */
  psychological_effects:  string[];
  /** Color wheel harmonics for crystal pairing logic */
  harmonics:              ColorHarmonics;
}

// ─────────────────────────────────────────────────────────────────────────────
// LAYER 4: METAPHYSICAL
// ⚠️  INTERPRETIVE / TRADITIONAL — NOT SCIENTIFIC DATA
// ─────────────────────────────────────────────────────────────────────────────

export interface MetaphysicalRecord {
  mineral_name:     string;

  /** Primary chakra resonance */
  chakra_primary:   Chakra;
  /** Secondary chakra resonances */
  chakra_secondary: Chakra[];

  /** Classical element correspondences */
  element: Element[];
  /** Planetary correspondences */
  planet:  string[];
  /** Jungian / traditional archetypes */
  archetype: string[];
  /** Zodiac signs */
  zodiac:    string[];
  /** Pythagorean numerology value */
  numerology: number | null;

  /** One-line intention statement */
  intention: string;

  /** Named traditions this data is sourced from */
  traditions: string[];

  /** Expanded property descriptions */
  properties: string[];

  /**
   * Which GAIA modules this crystal primarily supports.
   * Freeform string to allow compound assignments (e.g. "SomnusVeil + ClarusLens").
   */
  gaia_resonance: string;

  /**
   * Safety warning — toxicity, asbestos, radiation, water safety, etc.
   * null = no known hazard.
   * ALWAYS populate when a hazard exists.
   */
  safety_warning: string | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// MASTER RECORD
// ─────────────────────────────────────────────────────────────────────────────

export interface CrystalRecord {
  /** Display name (may differ from IMA mineral name for trade names / varieties) */
  name: string;

  /** Mindat numeric ID — null until synced */
  mindat_id: number | null;

  /** RRUFF reference IDs */
  rruff_ids: string[];

  /** ISO 8601 timestamp of last external data sync */
  last_synced: string | null;

  physical:     PhysicalRecord;
  optical:      OpticalRecord;
  color:        ColorRecord;
  metaphysical: MetaphysicalRecord;
}

// ─────────────────────────────────────────────────────────────────────────────
// QUERY / MATRIX TYPES
// Used by GAIA reasoning engine to filter and cross-reference crystals
// ─────────────────────────────────────────────────────────────────────────────

/** Query filter for multi-dimensional crystal matrix lookups */
export interface CrystalQuery {
  chakra?:          Chakra[];
  element?:         Element[];
  gaia_module?:     GAIAModule[];
  min_hardness?:    number;
  max_hardness?:    number;
  piezoelectric?:   boolean;
  safe_for_water?:  boolean;
  safe_for_hardware?: boolean;
  wavelength_min?:  number;
  wavelength_max?:  number;
  oklch_hue_min?:   number;
  oklch_hue_max?:   number;
}

/** Result of a matrix simulation run */
export interface CrystalMatrixResult {
  query:     CrystalQuery;
  matches:   CrystalRecord[];
  timestamp: string;
  note?:     string;
}
