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
 * Changelog:
 *   2026-05-29 (initial) — Base schema
 *   2026-05-29 (v1.1)   — Added trade_name, color_layer, yin_yang_pair to CrystalRecord
 *                        — Added piezoelectric, safe_for_water, safe_for_hardware to PhysicalRecord
 *   2026-05-29 (v1.2)   — Added 'Isometric' to crystal_system union
 *                        — Exported MetaphysicalProfile type alias
 *                        — Added MindatMineral, RruffSpectrum interfaces
 *   2026-05-29 (v1.3)   — Added AngelNumber type
 *                        — Added angel_number field to MetaphysicalRecord
 *                        — Added angel_number filter to CrystalQuery
 *   2026-06-01 (v1.4)   — Widened Chakra union to include extended / compound values
 *                          used in batch data (Higher Heart, All chakras variants, Base)
 *                        — Widened Element union to include Akasha, Light, All elements
 *                        — Widened AngelNumber to include 404, 707, 808, 1111
 *                        — Widened OpticalType to include 'I' (isotropic shorthand)
 *                        — Widened IMAStatus to include descriptive strings used for
 *                          trade-name / variety records
 *                        — Widened crystal_system to string to accommodate qualified
 *                          compound values in legacy / trade-name records
 *                        — Added n_min, n_mean, n_iso, n_e to RefractiveIndexValues
 *                        — Added 'I' to optical_sign for legacy data
 *                        — Added 'man-made' to ColorLayer
 *                        — Exported RiskTier as const enum for runtime Object.values() usage
 *                        — Exported ChakraPoint as const enum for runtime Object.values() usage
 */

// ─────────────────────────────────────────────────────────────────────────────
// SHARED PRIMITIVES
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Chakra system names used across all traditions.
 * Includes extended / compound values used in legacy and trade-name crystal records.
 * The compound values (e.g. 'All chakras (clearing)') are used for stones that
 * work across the full chakra column rather than a single point.
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
  | 'Earth Star'
  | 'Soul Star'
  // Extended / compound values used in batch data
  | 'Higher Heart'
  | 'Higher Heart (Thymus)'
  | 'Base'
  | 'All chakras'
  | 'All chakras (clearing)'
  | 'All chakras (iridescent full-spectrum)'
  | 'All chakras (integrated)'
  | 'All chakras (via colour varieties)'
  | 'All chakras (via rainbow)'
  | 'All (alignment)'
  | 'All chakras — colour-specific varieties govern specific centres'
  | 'All chakras — clear quartz amplifies every centre equally';

/**
 * Classical + expanded elements.
 * Includes Akasha (fifth element / spirit in Vedic / Theosophical tradition),
 * Light (radiant / photonic), and 'All elements' for omnispectral stones.
 */
export type Element =
  | 'Earth'
  | 'Water'
  | 'Fire'
  | 'Air'
  | 'Aether'
  | 'Storm'
  | 'Ice'
  | 'Wood'
  | 'Metal'
  // Extended values used in batch data
  | 'Akasha'
  | 'Light'
  | 'All elements';

/**
 * Optical character — uniaxial, biaxial, or isotropic.
 * 'I' is the legacy single-letter shorthand for Isotropic used in some
 * Mindat / RRUFF records. Prefer 'Isotropic' for new entries.
 */
export type OpticalType = 'U' | 'B' | 'Isotropic' | 'I' | null;

/**
 * IMA status codes.
 * The standard codes (A, Rd, Rn, Q, G) cover IMA-approved minerals.
 * The extended string variants cover trade names, variety names, and
 * biogenic / organic materials that appear in the crystal database but
 * are not formally classified as minerals by the IMA.
 *
 * Using a broad string union preserves type safety while accommodating
 * the mineralogical reality that many commercially traded crystals
 * (e.g. Septarian, Ammolite, Fairy Stone) are rocks or fossils, not minerals.
 */
export type IMAStatus =
  | 'A'
  | 'Rd'
  | 'Rn'
  | 'Q'
  | 'G'
  // Descriptive variants used for trade-name / variety / rock records
  | 'A (variety of calcite)'
  | 'A (both components IMA-recognised CaCO₃ polymorphs)'
  | 'A (variety name — IMA mineral is Quartz)'
  | 'A (variety name — IMA mineral is Albite)'
  | 'Not IMA — trade name for volcanic fumarolic rock'
  | 'Not IMA — trade name for fossil-bearing sedimentary rock'
  | 'Not IMA — trade name for porphyritic rock with script-like crystal inclusions'
  | 'Not IMA — organic material; not a mineral'
  | 'Not IMA — biogenic material; not a mineral by strict definition'
  | 'Not IMA approved — trade name for patterned jasper/chalcedony material'
  | 'Not IMA approved — trade/variety name for Ni-bearing chalcedony'
  | 'Not IMA approved — trade name for patterned agate/chalcedony'
  | 'Not IMA approved — natural glass / pseudotektite trade name'
  | 'Not IMA approved — trade name, commonly applied to psilomelane / romanèchite material'
  | 'Not IMA approved — trade name for patterned jasper/chalcedony material'
  | 'Not IMA approved as separate species — variety of chrysoberyl (IMA 1912)'
  | 'Not IMA approved as separate species — blue Cu-bearing variety of vesuvianite (IMA 1795)'
  | 'Not IMA approved — trade name for patterned agate/chalcedony'
  | 'Not IMA approved — trade name, commonly applied to psilomelane / romanèchite material'
  | (string & {})  // Escape hatch for any additional descriptive IMAStatus strings not yet enumerated
  | null;

/** GAIA module resonance targets */
export type GAIAModule =
  | 'ClarusLens'
  | 'AnchorPrism'
  | 'SomnusVeil'
  | 'SovereignCore'
  | 'ViriditasHeart'
  | 'Noosphere'
  | 'QuantumNexus';

/**
 * Color authenticity layer.
 * 'natural'  — colour is entirely geological / chemical — no treatment
 * 'treated'  — colour enhanced by heat, irradiation, acid, or other process
 * 'coating'  — colour from surface coating (aura/titanium vapour deposition, dye, paint)
 * 'man-made' — entirely synthetic / manufactured material
 */
export type ColorLayer = 'natural' | 'treated' | 'coating' | 'man-made';

/**
 * AngelNumber — the vibrational signal encoded in a crystal's numerological identity.
 *
 * Standard numbers (1–9): Pythagorean root frequencies
 * Master numbers (11, 22, 33): Do NOT reduce
 * Sacred numbers: Crystals with numerologically significant counts (e.g. Auralite-23 = 23)
 * Repeated sequences (111–999 and 1111): Angelic signal sequences
 * Extended numbers (404, 707, 808): Compound angelic sequences used in some traditions
 * null = not yet assigned
 */
export type AngelNumber =
  | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9        // Standard
  | 11 | 22 | 33                               // Master numbers
  | 23 | 44 | 55 | 66 | 77 | 88 | 99          // Sacred / extended
  | 111 | 222 | 333 | 444 | 555 | 666 | 777 | 888 | 999  // Sequences
  | 1111                                       // Gateway portal sequence
  | 404 | 707 | 808                            // Compound angelic sequences
  | null;

/**
 * RiskTier — ordered severity tiers for safety classification.
 * Exported as a const object so runtime code can use Object.values(RiskTier)
 * without needing TypeScript enums.
 */
export const RiskTier = {
  NONE:     'NONE',
  LOW:      'LOW',
  MEDIUM:   'MEDIUM',
  HIGH:     'HIGH',
  CRITICAL: 'CRITICAL',
} as const;
export type RiskTier = typeof RiskTier[keyof typeof RiskTier];

/**
 * ChakraPoint — canonical single-point chakra identifiers for lookup maps.
 * Distinct from the broader Chakra union (which includes compound / contextual values).
 * Exported as a const object so runtime code can use Object.values(ChakraPoint).
 */
export const ChakraPoint = {
  ROOT:          'Root',
  SACRAL:        'Sacral',
  SOLAR_PLEXUS:  'Solar Plexus',
  HEART:         'Heart',
  THROAT:        'Throat',
  THIRD_EYE:     'Third Eye',
  CROWN:         'Crown',
  HIGHER_CROWN:  'Higher Crown',
  EARTH_STAR:    'Earth Star',
  SOUL_STAR:     'Soul Star',
  HIGHER_HEART:  'Higher Heart',
} as const;
export type ChakraPoint = typeof ChakraPoint[keyof typeof ChakraPoint];

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

  /**
   * Crystal system.
   * The narrow union covers the seven crystal systems plus Amorphous,
   * Pseudohexagonal, and Isometric (legacy synonym for Cubic).
   * The broad string fallback (string & {}) accommodates qualified compound
   * values used in trade-name / rock records (e.g. 'Trigonal (cryptocrystalline)',
   * 'Mixed (monoclinic serpentine + trigonal stichtite)', 'Not applicable (rock)').
   * Use the narrow values for all IMA-approved mineral records.
   */
  crystal_system:
    | 'Triclinic'
    | 'Monoclinic'
    | 'Orthorhombic'
    | 'Tetragonal'
    | 'Trigonal'
    | 'Hexagonal'
    | 'Cubic'
    | 'Isometric'
    | 'Amorphous'
    | 'Pseudohexagonal'
    | (string & {});  // Qualified variants for legacy / trade-name records

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

  // ─── SAFETY & HARDWARE FLAGS (v1.1) ──────────────────────────────────────────
  piezoelectric:     boolean;
  safe_for_water:    boolean;
  safe_for_hardware: boolean;
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
  // Extended RI field names appearing in some optical records
  /** Minimum refractive index (alternative notation) */
  n_min?:     number;
  /** Mean / average refractive index */
  n_mean?:    number;
  /** Isotropic index (alternative notation for single-crystal isotropic materials) */
  n_iso?:     number;
  /** Extraordinary index (alternative shorthand) */
  n_e?:       number;
}

export interface WavelengthRange {
  min: number;
  max: number;
}

export interface OpticalRecord {
  mineral_name:     string;
  refractive_index: RefractiveIndexValues;
  birefringence:    number | null;
  /** '+', '-', 'I' (isotropic), or null */
  optical_sign:     '+' | '-' | 'I' | null;
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
  l: number;
  c: number;
  h: number;
}

export interface ColorHarmonics {
  complementary_hue: number | null;
  triadic_hues:      [number, number] | null;
  analogous_range:   [number, number] | null;
}

export interface ColorRecord {
  primary_color:          string;
  color_variants:         string[];
  dominant_wavelength_nm: number | null;
  oklch:                  OKLCHValue;
  hex:                    string | null;
  munsell:                string | null;
  color_temperature_k:    number | null;
  psychological_effects:  string[];
  harmonics:              ColorHarmonics;
}

// ─────────────────────────────────────────────────────────────────────────────
// LAYER 4: METAPHYSICAL
// ⚠️  INTERPRETIVE / TRADITIONAL — NOT SCIENTIFIC DATA
// ─────────────────────────────────────────────────────────────────────────────

export interface MetaphysicalRecord {
  mineral_name:     string;
  chakra_primary:   Chakra;
  chakra_secondary: Chakra[];
  element:          Element[];
  planet:           string[];
  archetype:        string[];
  zodiac:           string[];
  numerology:       number | null;
  angel_number:     AngelNumber;
  intention:        string;
  traditions:       string[];
  properties:       string[];
  gaia_resonance:   string;
  safety_warning:   string | null;
}

/** MetaphysicalProfile — alias for MetaphysicalRecord. */
export type MetaphysicalProfile = MetaphysicalRecord;

// ─────────────────────────────────────────────────────────────────────────────
// MASTER RECORD
// ─────────────────────────────────────────────────────────────────────────────

export interface CrystalRecord {
  name:          string;
  mindat_id:     number | null;
  rruff_ids:     string[];
  last_synced:   string | null;
  trade_name:    boolean;
  color_layer:   ColorLayer;
  yin_yang_pair: string | null;
  physical:      PhysicalRecord;
  optical:       OpticalRecord;
  color:         ColorRecord;
  metaphysical:  MetaphysicalRecord;
}

// ─────────────────────────────────────────────────────────────────────────────
// QUERY / MATRIX TYPES
// ─────────────────────────────────────────────────────────────────────────────

export interface CrystalQuery {
  chakra?:              Chakra[];
  element?:             Element[];
  gaia_module?:         GAIAModule[];
  min_hardness?:        number;
  max_hardness?:        number;
  piezoelectric?:       boolean;
  safe_for_water?:      boolean;
  safe_for_hardware?:   boolean;
  trade_name?:          boolean;
  color_layer?:         ColorLayer;
  has_yin_yang_pair?:   boolean;
  wavelength_min?:      number;
  wavelength_max?:      number;
  oklch_hue_min?:       number;
  oklch_hue_max?:       number;
  angel_number?:        AngelNumber;
}

export interface CrystalMatrixResult {
  query:     CrystalQuery;
  matches:   CrystalRecord[];
  timestamp: string;
  note?:     string;
}

// ─────────────────────────────────────────────────────────────────────────────
// EXTERNAL API WIRE TYPES
// ─────────────────────────────────────────────────────────────────────────────

export interface MindatMineral {
  id:                   number;
  longid:               string;
  guid:                 string;
  name:                 string;
  ima_formula:          string | null;
  mindat_formula:       string | null;
  ima_status:           string | null;
  ima_year:             number | null;
  strunzten:            string | null;
  dana8ed:              string | null;
  crystal_system:       string | null;
  hardness_min:         number | null;
  hardness_max:         number | null;
  specific_gravity_min: number | null;
  specific_gravity_max: number | null;
  cleavage:             string | null;
  fracture:             string | null;
  tenacity:             string | null;
  luster:               string | null;
  diaphaneity:          string | null;
  colour:               string | null;
  streak:               string | null;
  fluorescence:         string | null;
  ri_min:               number | null;
  ri_max:               number | null;
  birefringence:        number | null;
  optical_type:         string | null;
  shortdesc:            string | null;
  updttime:             string | null;
}

export interface RruffSpectrum {
  rruff_id:             string;
  name:                 string;
  spectrum_type:        'Raman' | 'Infrared' | 'XRD';
  laser_wavelength_nm?: number;
  data_url:             string;
  photo_url:            string | null;
  locality:             string | null;
  source:               string | null;
}
