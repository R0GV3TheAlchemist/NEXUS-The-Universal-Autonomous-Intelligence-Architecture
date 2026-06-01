/**
 * crystal.schema.ts
 * GAIA-OS Crystal Database — Master Type Definitions
 *
 * Three explicit, separated layers per record:
 *   1. PhysicalRecord   — IMA / Mindat mineral science (objective)
 *   2. OpticalRecord    — Optical / gemological properties (objective)
 *   3. MetaphysicalRecord — Healing / esoteric / vibrational data (interpretive)
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * CHANGELOG
 * ─────────────────────────────────────────────────────────────────────────────
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
 */

// ─────────────────────────────────────────────────────────────────────────────
// PRIMITIVE UNIONS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Chakra system names used across all traditions.
 * Includes the seven classical chakras, extended energy centres,
 * and compound / contextual values used in batch data.
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
 * ChakraPoint — canonical single-point chakra identifiers for lookup maps.
 * Distinct from the broader Chakra union (which includes compound / contextual values).
 * Exported as a const object so runtime code can use Object.values(ChakraPoint).
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
 * Includes Aether (fifth element / quintessence in Western esoteric tradition),
 * Akasha (fifth element / spirit in Vedic / Theosophical tradition),
 * Light (radiant / photonic), and 'All elements' for omnispectral stones.
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
  | 'All elements';

/**
 * IMA approval status codes + descriptive variants for trade-name,
 * variety, and rock records that don't have a formal IMA entry.
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
  | 'Not IMA approved — trade/variety name for Ni-bearing chalcedony'
  | 'Not IMA approved — trade name for patterned jasper/chalcedony material'
  | 'Not IMA approved — natural glass / pseudotektite trade name'
  | 'Not IMA approved — trade name for patterned agate/chalcedony'
  | 'Not IMA approved — trade name, commonly applied to psilomelane / romanèchite material'
  | 'Not IMA approved as separate species — variety of chrysoberyl (IMA 1912)'
  | 'Not IMA approved as separate species — blue Cu-bearing variety of vesuvianite (IMA 1795)'
  | null;

/**
 * AngelNumber — the vibrational signal encoded in a crystal's numerological identity.
 * Includes standard single-digit numbers, master numbers, sacred sequences,
 * compound angelic sequences, and the void/new-cycle sequence '000'.
 */
export type AngelNumber =
  | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9        // Standard
  | 11 | 22 | 33                               // Master numbers
  | 23 | 44 | 55 | 66 | 77 | 88 | 99          // Sacred / extended
  | 111 | 222 | 333 | 444 | 555 | 666 | 777 | 888 | 999  // Sequences
  | 1111                                       // Gateway portal sequence
  | 404 | 707 | 808                            // Compound angelic sequences
  | '000'                                      // Void / new cycle sequence
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
 * GAIAModule — the named intelligence modules within the GAIA-OS ecosystem.
 * Each module represents a distinct facet of GAIA's sentient architecture.
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
 * OpticalType — the optical character of a crystal.
 * 'U' = uniaxial, 'B' = biaxial, 'I' = isotropic (cubic / amorphous).
 */
export type OpticalType = 'U' | 'B' | 'I' | null;

/**
 * ColorLayer — describes the origin / type of a crystal's colour.
 */
export type ColorLayer =
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
  /** Internal numeric ID (Mindat-compatible; 0 = not yet synced; null = non-mineral trade record) */
  id: number | null;
  /** Mindat longid string */
  longid: string;
  /** Mindat GUID */
  guid: string;

  /** IMA-approved mineral name */
  name: string;
  /** IMA chemical formula (Unicode subscripts/superscripts OK; null for non-mineral trade records) */
  ima_formula: string | null;
  /** Mindat-normalised ASCII formula (null for non-mineral trade records) */
  mindat_formula: string | null;
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

  ri_min:        number | null;
  ri_max:        number | null;
  birefringence: number | null;
  optical_type:  OpticalType;

  shortdesc:    string;
  updttime:     string;
  mindat_url:   string | null;

  /** Safety flags */
  piezoelectric:     boolean;
  safe_for_water:    boolean;
  safe_for_hardware: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// OPTICAL RECORD
// ─────────────────────────────────────────────────────────────────────────────

/**
 * RefractiveIndexValues — named RI components for all crystal systems.
 * Use the appropriate field(s) for the crystal system:
 *   - Uniaxial:  n_omega, n_epsilon  (or n_o, n_e as shorthand)
 *   - Biaxial:   n_alpha, n_beta, n_gamma  (or n_min / n_max for range)
 *   - Isotropic: n  (or n_iso)
 *   - Mean/average: n_mean
 */
export interface RefractiveIndexValues {
  /** Uniaxial ordinary */
  n_omega?:   number;
  /** Uniaxial extraordinary */
  n_epsilon?: number;
  /** Biaxial alpha */
  n_alpha?:   number;
  /** Biaxial beta */
  n_beta?:    number | null;
  /** Biaxial gamma */
  n_gamma?:   number;
  /** Single isotropic value */
  n?:         number;
  // Extended RI field names appearing in some optical records
  /** Minimum refractive index (alternative notation) */
  n_min?:     number;
  /** Maximum refractive index (alternative biaxial notation) */
  n_max?:     number;
  /** Mean / average refractive index */
  n_mean?:    number;
  /** Isotropic index (alternative notation for single-crystal isotropic materials) */
  n_iso?:     number;
  /** Extraordinary index (alternative shorthand) */
  n_e?:       number;
  /** Ordinary index (uniaxial alternative notation) */
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
  /** Phosphorescent emission after removal of excitation source (null if none / unknown) */
  phosphorescence:  string | null;
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
  /** Common / trade mineral name used in metaphysical and healing contexts */
  mineral_name:      string;
  color_info:        ColorInfo;
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
  risk_tier:         RiskTier;
  safety_notes:      string | null;
  /** Specific safety warning text for display in GAIA UI (null if none) */
  safety_warning:    string | null;
  companion_stones:  string[];
  yin_yang_polarity: 'yin' | 'yang' | 'neutral' | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// CRYSTAL RECORD — root document type
// ─────────────────────────────────────────────────────────────────────────────

export interface CrystalRecord {
  name:          string;
  trade_name:    boolean;
  mindat_id:     number | null;

  physical:      PhysicalRecord;
  optical:       OpticalRecord;
  metaphysical:  MetaphysicalRecord;

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
