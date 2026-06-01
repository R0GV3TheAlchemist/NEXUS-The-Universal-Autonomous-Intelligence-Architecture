/**
 * crystal.schema.ts
 * GAIA-OS Crystal Database — Master Type Definitions
 *
 * Three explicit, separated layers per record:
 *   1. PhysicalRecord   — IMA / Mindat mineral science (objective)
 *   2. OpticalRecord    — Optical / gemological properties (objective)
 *   3. MetaphysicalRecord — Healing / esoteric / vibrational data (interpretive)
 *
 * ────────────────────────────────────────────────────────────────────────────
 * CHANGELOG
 * ────────────────────────────────────────────────────────────────────────────
 *   2026-05-01 (v1.0)   — Initial schema
 *   2026-05-15 (v1.1)   — Added RiskTier, SafetyFlags
 *   2026-05-22 (v1.2)   — Added piezoelectric, safe_for_water, safe_for_hardware to PhysicalRecord
 *   2026-05-29 (v1.3)   — Added AngelNumber type
 *                        — Added rruff_ids, last_synced to CrystalRecord
 *                        — Widened AngelNumber to include 404, 707, 808, 1111
 *   2026-06-01 (v1.4)   — Widened Chakra union to include extended / compound values
 *                        — Widened Element union to include Akasha, Light, All elements
 *                        — Widened IMAStatus union for trade-name / variety / rock records
 *                        — Widened crystal_system to (string & {}) fallback for qualified variants
 *                        — Widened OpticalType to include 'I' (isotropic)
 *                        — Widened optical_sign to include 'I'
 *                        — Widened ColorLayer to include 'man-made'
 *                        — Added n_min, n_mean, n_iso, n_e to RefractiveIndexValues
 *                        — Exported ChakraPoint as const enum for runtime Object.values() usage
 *   2026-06-01 (v1.5)   — PhysicalRecord.id: number | null (trade-name/rock records have no Mindat ID)
 *                        — PhysicalRecord.ima_formula: string | null
 *                        — PhysicalRecord.mindat_formula: string | null
 *                        — OpticalRecord.refractive_index: RefractiveIndexValues | null
 *                        — RefractiveIndexValues: added n_max, n_o; widened n_beta to number | null
 *                        — AngelNumber: added '000' (void / new-cycle sequence)
 *                        — IMAStatus: added 9 missing descriptive variants
 *   2026-06-01 (v1.6)   — Element: added 'Aether' (fifth element / quintessence)
 *                        — OpticalRecord: added phosphorescence field (string | null)
 *                        — MetaphysicalRecord: added mineral_name field (string)
 *                        — MetaphysicalRecord: added safety_warning field (string | null)
 *   2026-06-01 (v1.7)   — Element: added 'Metal' (used in batch-c2 and similar records)
 *                        — OpticalRecord: added visible_wavelength_nm (WavelengthRange | null)
 *                        — OpticalRecord: added spectra (string[]) for RRUFF spectrum IDs
 *                        — MetaphysicalRecord: color_info, risk_tier, safety_notes,
 *                          companion_stones, yin_yang_polarity marked optional
 *   2026-06-01 (v1.8)   — Element: added 'Ice' (used in batch-c9b)
 *                        — CrystalRecord: added top-level color_layer (ColorLayer | null)
 *                        — Added OKLCHValue, ColorRecord, MetaphysicalProfile type alias
 *                        — Added CrystalQuery, CrystalMatrixResult, RruffSpectrum
 *                        — Added ColorHarmonics interface
 *   2026-06-01 (v1.9)   — ColorLayer: added 'natural' (unenhanced body colour) and
 *                          'treated' (colour-enhanced stone, state adjective form)
 *   2026-06-01 (v2.0)   — BREAKING: Restructured ColorHarmonics to support both batch
 *                          hue-number format and full OKLCH computation format:
 *                          - ColorHarmonicsHue  — { complementary_hue, triadic_hues, analogous_hues }
 *                          - ColorHarmonicsOKLCH — { complementary, triadic, analogous } (full OKLCH)
 *                          - ColorHarmonics      — union alias for either form
 *                          ColorRecord.harmonics now accepts ColorHarmonicsHue | ColorHarmonicsOKLCH | null
 */

// ─────────────────────────────────────────────────────────────────────────────
// PRIMITIVE UNIONS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Chakra system names used across all traditions.
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
 * ChakraPoint — canonical single-point chakra identifiers for lookup maps.
 */
export const ChakraPoint = {
  Root:        'Root',
  EarthStar:   'Earth Star',
  Sacral:      'Sacral',
  SolarPlexus: 'Solar Plexus',
  Heart:       'Heart',
  Throat:      'Throat',
  ThirdEye:    'Third Eye',
  Crown:       'Crown',
  HigherCrown: 'Higher Crown',
  SoulStar:    'Soul Star',
} as const;

export type ChakraPoint = typeof ChakraPoint[keyof typeof ChakraPoint];

/**
 * Classical + expanded elements.
 */
export type Element =
  | 'Fire'
  | 'Water'
  | 'Earth'
  | 'Air'
  | 'Storm'
  | 'Aether'
  | 'Akasha'
  | 'Light'
  | 'Metal'
  | 'Ice'
  | 'All elements';

/**
 * IMA approval status codes + descriptive variants.
 */
export type IMAStatus =
  | 'A'
  | 'Rd'
  | 'Rn'
  | 'Q'
  | 'G'
  | 'A (variety of calcite)'
  | 'A (both components IMA-recognised CaCO₃ polymorphs)'
  | 'A (variety name — IMA mineral is Quartz)'
  | 'A (variety name — IMA mineral is Albite)'
  | 'Not IMA — trade name for volcanic fumarolic rock'
  | 'Not IMA — trade name for fossil-bearing sedimentary rock'
  | 'Not IMA — trade name for porphyritic rock with script-like crystal inclusions'
  | 'Not IMA — organic material; not a mineral'
  | 'Not IMA — biogenic material; not a mineral by strict definition'
  | 'Not IMA approved — trade/variety name for Ni-bearing chalcedony'
  | 'Not IMA approved — trade name for patterned jasper/chalcedony material'
  | 'Not IMA approved — natural glass / pseudotektite trade name'
  | 'Not IMA approved — trade name for patterned agate/chalcedony'
  | 'Not IMA approved — trade name, commonly applied to psilomelane / romanèchite material'
  | 'Not IMA approved as separate species — variety of chrysoberyl (IMA 1912)'
  | 'Not IMA approved as separate species — blue Cu-bearing variety of vesuvianite (IMA 1795)'
  | null;

/**
 * AngelNumber — vibrational signal encoded in a crystal's numerological identity.
 */
export type AngelNumber =
  | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9
  | 11 | 22 | 33
  | 23 | 44 | 55 | 66 | 77 | 88 | 99
  | 111 | 222 | 333 | 444 | 555 | 666 | 777 | 888 | 999
  | 1111
  | 404 | 707 | 808
  | '000'
  | null;

/**
 * RiskTier — ordered severity tiers for safety classification.
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
 * GAIAModule — named intelligence modules within the GAIA-OS ecosystem.
 */
export type GAIAModule =
  | 'AnchorPrism'
  | 'ViriditasHeart'
  | 'SovereignCore'
  | 'ClarusLens'
  | 'Noosphere'
  | 'QuantumNexus'
  | 'SpiritusEngine'
  | 'ChronoWeave';

/**
 * OpticalType — optical character of a crystal.
 */
export type OpticalType = 'U' | 'B' | 'I' | null;

/**
 * ColorLayer — describes the origin / type of a crystal's colour.
 *
 * Values:
 *   'natural'    — unenhanced, body colour as it occurs in nature
 *   'treated'    — colour has been enhanced or altered (heat, irradiation, coating, etc.)
 *   'body'       — intrinsic body colour (synonym for 'natural'; retained for compatibility)
 *   'surface'    — colour resides on the surface (oxide film, iridescence, adularescence)
 *   'inclusion'  — colour derives from mineral inclusions within the stone
 *   'irradiation'— colour induced by natural or artificial radiation
 *   'treatment'  — catch-all for laboratory treatment not otherwise specified
 *   'man-made'   — synthetic / lab-created stone
 *    null        — colour layer not yet classified
 */
export type ColorLayer =
  | 'natural'
  | 'treated'
  | 'body'
  | 'surface'
  | 'inclusion'
  | 'irradiation'
  | 'treatment'
  | 'man-made'
  | null;

// ─────────────────────────────────────────────────────────────────────────────
// PHYSICAL RECORD
// ─────────────────────────────────────────────────────────────────────────────

export interface PhysicalRecord {
  id: number | null;
  longid: string;
  guid: string;
  name: string;
  ima_formula: string | null;
  mindat_formula: string | null;
  ima_status: IMAStatus;
  ima_year: number | null;
  strunzten: string | null;
  dana8ed: string | null;
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
    | (string & {});
  hardness_min: number | null;
  hardness_max: number | null;
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
  ri_min:        number | null;
  ri_max:        number | null;
  birefringence: number | null;
  optical_type:  OpticalType;
  shortdesc:    string;
  updttime:     string;
  mindat_url:   string | null;
  piezoelectric:     boolean;
  safe_for_water:    boolean;
  safe_for_hardware: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// OPTICAL RECORD
// ─────────────────────────────────────────────────────────────────────────────

export interface RefractiveIndexValues {
  n_omega?:   number;
  n_epsilon?: number;
  n_alpha?:   number;
  n_beta?:    number | null;
  n_gamma?:   number;
  n?:         number;
  n_min?:     number;
  n_max?:     number;
  n_mean?:    number;
  n_iso?:     number;
  n_e?:       number;
  n_o?:       number;
}

export interface WavelengthRange {
  min: number;
  max: number;
}

export interface OpticalRecord {
  mineral_name:     string;
  refractive_index: RefractiveIndexValues | null;
  birefringence:    number | null;
  optical_sign:     '+' | '-' | 'I' | null;
  dispersion:       string | null;
  pleochroism:      string | null;
  fluorescence_lw:  string | null;
  fluorescence_sw:  string | null;
  phosphorescence:  string | null;
  visible_wavelength_nm: WavelengthRange | null;
  spectra: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// COLOR RECORD
// ─────────────────────────────────────────────────────────────────────────────

/**
 * OKLCHValue — a colour expressed in the OKLCH perceptual colour space.
 */
export interface OKLCHValue {
  /** Lightness: 0–1 */
  l: number;
  /** Chroma: 0–0.4 (typical) */
  c: number;
  /** Hue: 0–360 */
  h: number;
  /** Alpha: 0–1 (optional, defaults to 1) */
  a?: number;
}

/**
 * ColorHarmonicsHue — lightweight hue-number form of colour harmonics.
 * This is the format used in batch data files authored by the crystal curation pipeline.
 *
 * Fields store raw hue angles (0–360) from the OKLCH colour wheel:
 *   complementary_hue — the hue directly opposite the primary (primary_h + 180) % 360
 *   triadic_hues      — two hues forming an equilateral triangle (±120°), or null
 *   analogous_hues    — two hues adjacent to the primary (±30°), or null
 */
export interface ColorHarmonicsHue {
  complementary_hue: number | null;
  triadic_hues:      [number, number] | null;
  analogous_hues?:   [number, number] | null;
}

/**
 * ColorHarmonicsOKLCH — full OKLCH form of colour harmonics.
 * Generated by the GAIA colour computation engine after the batch data pass.
 *
 * Each harmonic is a complete OKLCHValue (l, c, h) so it can be used
 * directly in CSS or passed to the renderer without further computation.
 */
export interface ColorHarmonicsOKLCH {
  complementary: OKLCHValue | null;
  analogous:     [OKLCHValue, OKLCHValue] | null;
  triadic:       [OKLCHValue, OKLCHValue] | null;
}

/**
 * ColorHarmonics — union of both harmonic forms.
 * A record may contain either the lightweight hue-number form (batch data)
 * or the full OKLCH form (post-computation). Use a type guard to discriminate:
 *
 *   function isHueForm(h: ColorHarmonics): h is ColorHarmonicsHue {
 *     return 'complementary_hue' in h;
 *   }
 */
export type ColorHarmonics = ColorHarmonicsHue | ColorHarmonicsOKLCH;

/**
 * ColorRecord — full colour intelligence profile for a crystal.
 * Top-level field on CrystalRecord (parallel to physical / optical / metaphysical).
 */
export interface ColorRecord {
  /** Primary colour origin type */
  color_layer:       ColorLayer;
  /** Primary colour in OKLCH */
  oklch:             OKLCHValue;
  /** Colour temperature in Kelvin (null if not applicable) */
  color_temperature_k: number | null;
  /** Derived colour harmonics — hue-number form from batch data, or full OKLCH after computation */
  harmonics?:        ColorHarmonics | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// METAPHYSICAL RECORD
// ─────────────────────────────────────────────────────────────────────────────

export interface ColorInfo {
  base:   string[];
  layer?: ColorLayer;
  notes?: string;
}

export interface MetaphysicalRecord {
  mineral_name:      string;
  color_info?:       ColorInfo;
  chakra_primary:    Chakra;
  chakra_secondary:  Chakra[];
  element:           Element[];
  planet:            string[];
  archetype:         string[];
  zodiac:            string[];
  numerology:        number | null;
  angel_number:      AngelNumber;
  intention:         string;
  traditions:        string[];
  properties:        string[];
  gaia_resonance:    string | null;
  risk_tier?:        RiskTier;
  safety_notes?:     string | null;
  safety_warning:    string | null;
  companion_stones?: string[];
  yin_yang_polarity?: 'yin' | 'yang' | 'neutral' | null;
}

/**
 * MetaphysicalProfile — alias for MetaphysicalRecord.
 * Used in some external consumers that import by this name.
 */
export type MetaphysicalProfile = MetaphysicalRecord;

// ─────────────────────────────────────────────────────────────────────────────
// QUERY TYPES
// ─────────────────────────────────────────────────────────────────────────────

/**
 * CrystalQuery — filter object for queryCrystals() in index.ts.
 * All fields are optional; supplied fields are ANDed together.
 */
export interface CrystalQuery {
  chakra?:            Chakra[];
  element?:           Element[];
  gaia_module?:       GAIAModule[];
  min_hardness?:      number | null;
  max_hardness?:      number | null;
  piezoelectric?:     boolean | null;
  safe_for_water?:    boolean | null;
  safe_for_hardware?: boolean | null;
  trade_name?:        boolean | null;
  color_layer?:       ColorLayer | null;
  has_yin_yang_pair?: boolean | null;
  angel_number?:      AngelNumber;
  wavelength_min?:    number | null;
  wavelength_max?:    number | null;
  oklch_hue_min?:     number | null;
  oklch_hue_max?:     number | null;
}

/**
 * CrystalMatrixResult — a crystal record paired with a relevance score,
 * returned by matrix / recommendation queries.
 */
export interface CrystalMatrixResult {
  crystal:   CrystalRecord;
  score:     number;
  reasons:   string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// RRUFF / SPECTRAL TYPES
// ─────────────────────────────────────────────────────────────────────────────

/**
 * RruffSpectrum — a single RRUFF spectroscopy record linked to a crystal.
 */
export interface RruffSpectrum {
  id:           string;
  mineral_name: string;
  url:          string;
  type:         'Raman' | 'IR' | 'XRD' | string;
  locality?:    string | null;
  description?: string | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// CRYSTAL RECORD — root document type
// ─────────────────────────────────────────────────────────────────────────────

export interface CrystalRecord {
  name:          string;
  trade_name:    boolean;
  mindat_id:     number | null;

  /**
   * Top-level colour layer classification.
   * Mirrors optical.color_layer for fast query-engine access without
   * navigating into the optical sub-record.
   */
  color_layer:   ColorLayer;

  physical:      PhysicalRecord;
  optical:       OpticalRecord;
  metaphysical:  MetaphysicalRecord;
  /** Full colour intelligence profile (null until colour pass is run) */
  color?:        ColorRecord;

  yin_yang_pair: string | null;
  rruff_ids:     string[];
  last_synced:   string | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// MINDAT WIRE TYPES (external API)
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
  shortdesc:            string | null;
  updttime:             string;
  mindat_url:           string | null;
}

export interface MindatRecord {
  id:             number;
  longid:         string;
  guid:           string;
  name:           string;
  ima_formula:    string;
  mindat_formula: string;
  ima_status:     string;
  ima_year:       number | null;
  strunzten:      string | null;
  dana8ed:        string | null;
  crystal_system: string | null;
  hardness_min:   number | null;
  hardness_max:   number | null;
  updttime:       string;
}

// ─────────────────────────────────────────────────────────────────────────────
// SYNC / AUDIT TYPES
// ─────────────────────────────────────────────────────────────────────────────

export interface SyncEvent {
  crystal_name: string;
  mindat_id:    number;
  timestamp:    string;
  note?:        string;
}
