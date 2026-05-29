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
 *                        — These were previously only in CrystalQuery (query-time) — moved to
 *                          record-level so GAIA can filter without annotation passes.
 *   2026-05-29 (v1.2)   — Added 'Isometric' to crystal_system union (synonym for Cubic, legacy data)
 *                        — Exported MetaphysicalProfile type alias (= MetaphysicalRecord)
 *                        — Added MindatMineral interface (raw Mindat API wire format)
 *                        — Added RruffSpectrum interface (RRUFF spectral record)
 *                        — Resolves TS2305 errors in metaphysical.data.ts, mindat.service.ts,
 *                          rruff.service.ts
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

/**
 * Color authenticity layer.
 * 'natural'  — colour is entirely geological / chemical — no treatment
 * 'treated'  — colour enhanced by heat, irradiation, acid, or other process
 * 'coating'  — colour from surface coating (aura/titanium vapour deposition, dye, paint)
 */
export type ColorLayer = 'natural' | 'treated' | 'coating';

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
   * 'Isometric' is an older IMA synonym for 'Cubic' — both are accepted here
   * to support legacy data entries. Prefer 'Cubic' for new records.
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

  // ─── SAFETY & HARDWARE FLAGS (v1.1) ─────────────────────────────────────
  /**
   * True if the mineral (or a key component) exhibits piezoelectric behaviour.
   * Used by GAIA to flag stones suitable / unsuitable for hardware proximity.
   * Piezoelectric stones generate electrical charge under mechanical stress.
   */
  piezoelectric: boolean;

  /**
   * True if safe to use in direct water contact (drinking elixirs, baths).
   * False for: sulfates (anhydrite/angelite — converts to gypsum),
   * sulfides (copper/iron sulfide leaching), soft stones prone to dissolution,
   * stones with toxic mineral components.
   */
  safe_for_water: boolean;

  /**
   * True if safe to use in proximity to electronic/quantum hardware.
   * False for: piezoelectric stones (charge generation),
   * electrically conductive stones (chalcopyrite, native metals),
   * strongly magnetic stones (magnetite, lodestone),
   * radioactive minerals.
   */
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

/**
 * MetaphysicalProfile — alias for MetaphysicalRecord.
 * metaphysical.data.ts imports this name; both refer to the same structure.
 * Resolves: TS2305 Module '"./crystal.schema"' has no exported member 'MetaphysicalProfile'
 */
export type MetaphysicalProfile = MetaphysicalRecord;

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

  // ─── IDENTITY FLAGS (v1.1) ─────────────────────────────────────────────
  /**
   * True if this record's display name is a trade name / variety name
   * rather than an IMA-approved mineral name.
   * Examples: Angelite (true), Ancestralite (true), Andradite (false)
   * GAIA uses this to avoid conflating trade names with IMA species
   * in scientific reasoning — the physical.name field holds the real IMA name.
   */
  trade_name: boolean;

  /**
   * Color authenticity classification.
   * 'natural'  — all colour is geological / intrinsic chemistry
   * 'treated'  — colour enhanced by heat, irradiation, acid wash, etc.
   * 'coating'  — colour from surface coating (aura titanium, dye, etc.)
   * Critical for GAIA to correctly represent stones in the metaphysical layer —
   * the energetic properties of a coated stone differ from a natural one.
   */
  color_layer: ColorLayer;

  /**
   * The structural opposite of this crystal in the database — its yin-yang pair.
   * Encodes intentional polarity relationships for matrix queries and
   * GAIA configuration recommendations.
   * Examples: Angelite ↔ Apache Tear, Anandalite ↔ Ancestralite
   * null = no pair assigned yet.
   */
  yin_yang_pair: string | null;

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
}

/** Result of a matrix simulation run */
export interface CrystalMatrixResult {
  query:     CrystalQuery;
  matches:   CrystalRecord[];
  timestamp: string;
  note?:     string;
}

// ─────────────────────────────────────────────────────────────────────────────
// EXTERNAL API WIRE TYPES
// Raw response shapes from Mindat and RRUFF.
// Intentionally loose-typed — external APIs do not guarantee our strict unions.
// Normalise to PhysicalRecord / OpticalRecord after fetching.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * MindatMineral — raw Mindat API v1 mineral response shape.
 * Fields mirror the MINDAT_FIELDS list in mindat.service.ts.
 * crystal_system and optical_type are loose strings because the Mindat API
 * does not use our strict internal union types.
 *
 * Docs: https://api.mindat.org/schema/redoc/#operation/minerals_list
 *
 * Resolves: TS2305 Module '"./crystal.schema"' has no exported member 'MindatMineral'
 */
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
  /** Raw crystal system string from Mindat (e.g. 'Cubic', 'Isometric', 'Trigonal') */
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
  /** Raw optical type from Mindat — may be 'U', 'B', 'I', 'Isotropic', or null */
  optical_type:         string | null;
  shortdesc:            string | null;
  updttime:             string | null;
}

/**
 * RruffSpectrum — a single spectral record from the RRUFF Project database.
 * Constructed by RruffService.buildSpectra() and returned by the
 * normalised search endpoint response.
 *
 * Source: https://rruff.info
 *
 * Resolves: TS2305 Module '"./crystal.schema"' has no exported member 'RruffSpectrum'
 */
export interface RruffSpectrum {
  /** RRUFF sample identifier, e.g. "R040031" */
  rruff_id:             string;
  /** Mineral name as recorded in RRUFF */
  name:                 string;
  /** Spectrum type */
  spectrum_type:        'Raman' | 'Infrared' | 'XRD';
  /** Laser excitation wavelength in nm — Raman only; omitted for IR and XRD */
  laser_wavelength_nm?: number;
  /** Direct URL to the processed spectrum data file (.txt) */
  data_url:             string;
  /** URL to the sample photograph — null if unavailable */
  photo_url:            string | null;
  /** Collection locality description — null if unknown */
  locality:             string | null;
  /** Source / donor attribution — null if unattributed */
  source:               string | null;
}
