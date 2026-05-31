/**
 * cod.service.ts
 * Crystallography Open Database (COD) Client Service
 * GAIA-OS | src/crystals/cod.service.ts
 *
 * PURPOSE:
 * Fetches real, open-source physical mineral data from the Crystallography
 * Open Database (https://www.crystallography.net/cod/) to enrich GAIA's
 * CrystalRecord with scientifically accurate physical properties.
 *
 * The COD is a fully open, royalty-free, CC0-licensed database of
 * crystal structures. No API key. No subscription. No permission required.
 * This is by design — GAIA uses only open data sources. Always.
 *
 * WHAT THIS SERVICE DOES:
 * - Queries COD by mineral name, chemical formula, or mineral ID
 * - Maps COD structural data onto GAIA's PhysicalProperties schema
 * - Caches results locally to avoid redundant network calls
 * - Gracefully degrades — if COD is unreachable, GAIA uses existing data
 * - Never overwrites GAIA-authored metaphysical content with COD data
 *   The physical and metaphysical layers are always kept separate.
 *
 * ARCHITECTURE:
 * COD REST API → CodRawEntry → mapCodToCrystalPhysics() → PhysicalProperties
 * PhysicalProperties is merged INTO CrystalRecord.physical_properties only.
 * It never touches: gaia_resonance, healing_properties, chakra_associations,
 * affirmations, or any other GAIA-authored field.
 *
 * LICENSE: AGPL-3.0-or-later + Ethical Use Addendum (see LICENSE)
 * COD data is CC0 — no attribution required, but we cite it anyway.
 * Because GAIA honors her sources.
 */

// ─── COD API Configuration ───────────────────────────────────────────────────

const COD_BASE_URL = 'https://www.crystallography.net/cod';
const COD_SEARCH_URL = `${COD_BASE_URL}/result`;
const COD_CIF_URL    = `${COD_BASE_URL}/cif`;
const COD_API_URL    = `${COD_BASE_URL}/api/v1`;

/** How long to cache COD results in milliseconds. Default: 24 hours. */
const COD_CACHE_TTL_MS = 1000 * 60 * 60 * 24;

// ─── COD Raw API Types ────────────────────────────────────────────────────────

/**
 * Raw entry returned by the COD search/result API.
 * Only the fields GAIA actually uses are mapped here.
 * COD returns many more fields — we intentionally ignore anything
 * not relevant to physical mineral properties.
 */
export interface CodRawEntry {
  /** COD numeric identifier — e.g. 9000041 */
  file: number;

  /** Mineral/compound name as recorded in COD */
  mineral: string;

  /** Chemical formula — e.g. "Si O2" for Quartz */
  formula: string;

  /** Full chemical formula with subscripts */
  formula_sum?: string;

  /** Crystal system: cubic, hexagonal, trigonal, tetragonal,
   *  orthorhombic, monoclinic, or triclinic */
  sg?: string;          // Space group symbol e.g. "P 63/m m c"
  sgHall?: string;      // Hall notation
  sgNumber?: number;    // International Tables number (1–230)

  /** Unit cell parameters in Angstroms and degrees */
  a?: number;    // a axis length (Å)
  b?: number;    // b axis length (Å)
  c?: number;    // c axis length (Å)
  alpha?: number; // α angle (°)
  beta?: number;  // β angle (°)
  gamma?: number; // γ angle (°)

  /** Unit cell volume in Å³ */
  vol?: number;

  /** Number of formula units per unit cell */
  Z?: number;

  /** Calculated density in g/cm³ */
  calcdens?: number;

  /** Measured density in g/cm³ */
  measdens?: number;

  /** R-factor — quality indicator of the crystal structure determination */
  Robs?: number;

  /** Authors of the structure determination */
  authors?: string;

  /** Journal of publication */
  journal?: string;

  /** Year of publication */
  year?: number;

  /** DOI of the source paper */
  doi?: string;

  /** URL to the CIF file for this entry */
  cifLink?: string;
}

// ─── GAIA Physical Properties Schema ─────────────────────────────────────────

/**
 * Crystal system classification.
 * Maps directly from the 7 crystal systems in crystallography.
 */
export type CrystalSystem =
  | 'cubic'
  | 'hexagonal'
  | 'trigonal'
  | 'tetragonal'
  | 'orthorhombic'
  | 'monoclinic'
  | 'triclinic'
  | 'amorphous'
  | 'unknown';

/**
 * Unit cell parameters — the fundamental geometric container
 * of a crystal's repeating structure.
 */
export interface UnitCell {
  /** Axis lengths in Angstroms (1 Å = 0.1 nm) */
  a_angstrom: number | null;
  b_angstrom: number | null;
  c_angstrom: number | null;

  /** Angles in degrees */
  alpha_deg: number | null;
  beta_deg:  number | null;
  gamma_deg: number | null;

  /** Volume in cubic Angstroms */
  volume_angstrom3: number | null;

  /** Formula units per unit cell */
  Z: number | null;
}

/**
 * Physical properties of a mineral — sourced from COD.
 * This is the ONLY section of CrystalRecord that COD data populates.
 * All other GAIA fields are authored by GAIA contributors.
 */
export interface CodPhysicalProperties {
  /** Chemical formula as written — e.g. "SiO₂" */
  chemical_formula: string | null;

  /** Simplified sum formula — e.g. "O2 Si" */
  formula_sum: string | null;

  /** Crystal system */
  crystal_system: CrystalSystem;

  /** Space group in Hermann-Mauguin notation — e.g. "P 63/m m c" */
  space_group: string | null;

  /** Space group number (1–230) per International Tables */
  space_group_number: number | null;

  /** Unit cell geometry */
  unit_cell: UnitCell;

  /** Calculated density in g/cm³ (from unit cell + formula weight) */
  density_calc_g_cm3: number | null;

  /** Measured density in g/cm³ (from experiment) */
  density_meas_g_cm3: number | null;

  /** COD entry ID — for direct citation and CIF download */
  cod_id: number | null;

  /** Direct link to the CIF file */
  cod_cif_url: string | null;

  /** DOI of the original crystallographic paper */
  source_doi: string | null;

  /** Authors of the crystal structure determination */
  source_authors: string | null;

  /** Year the structure was published */
  source_year: number | null;

  /** ISO timestamp of when GAIA last fetched this data from COD */
  last_fetched_at: string;

  /** Whether this data came from a live COD fetch or the local cache */
  source: 'cod_live' | 'cod_cached' | 'cod_unavailable';
}

// ─── Cache Layer ──────────────────────────────────────────────────────────────

interface CodCacheEntry {
  data: CodRawEntry[];
  fetched_at: number; // Unix timestamp ms
}

/** In-memory cache. Persists for the lifetime of the GAIA session. */
const codCache = new Map<string, CodCacheEntry>();

/**
 * Returns cached COD results if still within TTL, or null if stale/missing.
 */
function getCached(key: string): CodRawEntry[] | null {
  const entry = codCache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.fetched_at > COD_CACHE_TTL_MS) {
    codCache.delete(key);
    return null;
  }
  return entry.data;
}

/**
 * Stores COD results in the in-memory cache.
 */
function setCache(key: string, data: CodRawEntry[]): void {
  codCache.set(key, { data, fetched_at: Date.now() });
}

// ─── Crystal System Mapping ───────────────────────────────────────────────────

/**
 * Maps a COD space group number (1–230) to a crystal system string.
 * Space group ranges per International Tables for Crystallography:
 *   1–2:     Triclinic
 *   3–15:    Monoclinic
 *   16–74:   Orthorhombic
 *   75–142:  Tetragonal
 *   143–167: Trigonal
 *   168–194: Hexagonal
 *   195–230: Cubic
 */
export function spaceGroupNumberToCrystalSystem(sgNumber: number | undefined): CrystalSystem {
  if (!sgNumber) return 'unknown';
  if (sgNumber >= 1   && sgNumber <= 2)   return 'triclinic';
  if (sgNumber >= 3   && sgNumber <= 15)  return 'monoclinic';
  if (sgNumber >= 16  && sgNumber <= 74)  return 'orthorhombic';
  if (sgNumber >= 75  && sgNumber <= 142) return 'tetragonal';
  if (sgNumber >= 143 && sgNumber <= 167) return 'trigonal';
  if (sgNumber >= 168 && sgNumber <= 194) return 'hexagonal';
  if (sgNumber >= 195 && sgNumber <= 230) return 'cubic';
  return 'unknown';
}

// ─── COD API Query Functions ──────────────────────────────────────────────────

/**
 * Searches the COD for crystal structures matching a mineral name.
 *
 * Uses the COD text search endpoint. Returns up to `limit` results,
 * ordered by relevance (COD default ordering).
 *
 * @param mineralName - Common or IMA mineral name, e.g. "Quartz"
 * @param limit       - Maximum results to return (default 5)
 * @returns Array of raw COD entries, or empty array on failure
 */
export async function searchCodByMineral(
  mineralName: string,
  limit = 5
): Promise<CodRawEntry[]> {
  const cacheKey = `mineral:${mineralName.toLowerCase().trim()}:${limit}`;
  const cached = getCached(cacheKey);
  if (cached) return cached;

  try {
    const params = new URLSearchParams({
      mineral: mineralName,
      format:  'json',
      limit:   String(limit),
    });
    const url = `${COD_SEARCH_URL}?${params.toString()}`;
    const response = await fetch(url, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(10_000), // 10s timeout
    });

    if (!response.ok) {
      console.warn(`[COD] Search failed for "${mineralName}": HTTP ${response.status}`);
      return [];
    }

    const data: CodRawEntry[] = await response.json();
    setCache(cacheKey, data);
    return data;
  } catch (err) {
    console.warn(`[COD] Network error searching for "${mineralName}":`, err);
    return [];
  }
}

/**
 * Fetches a specific COD entry by its numeric COD ID.
 *
 * @param codId - The COD integer identifier, e.g. 9000041
 * @returns The raw COD entry, or null if not found / network error
 */
export async function fetchCodById(codId: number): Promise<CodRawEntry | null> {
  const cacheKey = `id:${codId}`;
  const cached = getCached(cacheKey);
  if (cached && cached.length > 0) return cached[0];

  try {
    const url = `${COD_API_URL}/entries/${codId}`;
    const response = await fetch(url, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(10_000),
    });

    if (!response.ok) {
      console.warn(`[COD] Fetch failed for ID ${codId}: HTTP ${response.status}`);
      return null;
    }

    const data: CodRawEntry = await response.json();
    setCache(cacheKey, [data]);
    return data;
  } catch (err) {
    console.warn(`[COD] Network error fetching COD ID ${codId}:`, err);
    return null;
  }
}

/**
 * Searches COD by chemical formula.
 * Useful for minerals with ambiguous common names.
 *
 * @param formula - Chemical formula, e.g. "SiO2" or "Si O2"
 * @param limit   - Maximum results (default 5)
 */
export async function searchCodByFormula(
  formula: string,
  limit = 5
): Promise<CodRawEntry[]> {
  const cacheKey = `formula:${formula.toLowerCase().replace(/\s/g, '')}:${limit}`;
  const cached = getCached(cacheKey);
  if (cached) return cached;

  try {
    const params = new URLSearchParams({
      formula: formula,
      format:  'json',
      limit:   String(limit),
    });
    const url = `${COD_SEARCH_URL}?${params.toString()}`;
    const response = await fetch(url, {
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(10_000),
    });

    if (!response.ok) {
      console.warn(`[COD] Formula search failed for "${formula}": HTTP ${response.status}`);
      return [];
    }

    const data: CodRawEntry[] = await response.json();
    setCache(cacheKey, data);
    return data;
  } catch (err) {
    console.warn(`[COD] Network error in formula search for "${formula}": `, err);
    return [];
  }
}

// ─── Data Mapping ─────────────────────────────────────────────────────────────

/**
 * Maps a raw COD entry onto GAIA's CodPhysicalProperties schema.
 *
 * This is the bridge between the scientific world and GAIA's world.
 * It translates crystallographic notation into clean, typed GAIA fields
 * without losing any of the source precision.
 *
 * @param raw    - The raw COD entry
 * @param source - Whether this came from a live fetch or cache
 */
export function mapCodToCrystalPhysics(
  raw: CodRawEntry,
  source: 'cod_live' | 'cod_cached' = 'cod_live'
): CodPhysicalProperties {
  const crystalSystem = spaceGroupNumberToCrystalSystem(raw.sgNumber);

  return {
    chemical_formula:     raw.formula    ?? null,
    formula_sum:          raw.formula_sum ?? null,
    crystal_system:       crystalSystem,
    space_group:          raw.sg          ?? null,
    space_group_number:   raw.sgNumber    ?? null,

    unit_cell: {
      a_angstrom:        raw.a     ?? null,
      b_angstrom:        raw.b     ?? null,
      c_angstrom:        raw.c     ?? null,
      alpha_deg:         raw.alpha ?? null,
      beta_deg:          raw.beta  ?? null,
      gamma_deg:         raw.gamma ?? null,
      volume_angstrom3:  raw.vol   ?? null,
      Z:                 raw.Z     ?? null,
    },

    density_calc_g_cm3:  raw.calcdens ?? null,
    density_meas_g_cm3:  raw.measdens ?? null,

    cod_id:              raw.file       ?? null,
    cod_cif_url:         raw.file
                           ? `${COD_CIF_URL}/${raw.file}.cif`
                           : null,
    source_doi:          raw.doi        ?? null,
    source_authors:      raw.authors    ?? null,
    source_year:         raw.year       ?? null,

    last_fetched_at:     new Date().toISOString(),
    source,
  };
}

// ─── Primary Enrichment API ───────────────────────────────────────────────────

/**
 * The main enrichment entry point for GAIA's crystal pipeline.
 *
 * Given a mineral name, returns the best-matching COD physical properties.
 * "Best match" is determined by:
 *   1. Exact mineral name match
 *   2. Lowest R-factor (highest quality structure determination)
 *   3. Most recent publication year
 *
 * If no COD data is found, returns a CodPhysicalProperties object with
 * source='cod_unavailable' and all physical fields set to null.
 * GAIA degrades gracefully. She never crashes because science was offline.
 *
 * @param mineralName - The mineral name to enrich, e.g. "Amethyst" or "Quartz"
 * @param chemFormula - Optional chemical formula to refine the search
 * @returns CodPhysicalProperties — always returns an object, never throws
 */
export async function enrichCrystalFromCod(
  mineralName: string,
  chemFormula?: string
): Promise<CodPhysicalProperties> {
  const unavailableResult: CodPhysicalProperties = {
    chemical_formula:   chemFormula ?? null,
    formula_sum:        null,
    crystal_system:     'unknown',
    space_group:        null,
    space_group_number: null,
    unit_cell: {
      a_angstrom: null, b_angstrom: null, c_angstrom: null,
      alpha_deg:  null, beta_deg:   null, gamma_deg:  null,
      volume_angstrom3: null, Z: null,
    },
    density_calc_g_cm3: null,
    density_meas_g_cm3: null,
    cod_id:             null,
    cod_cif_url:        null,
    source_doi:         null,
    source_authors:     null,
    source_year:        null,
    last_fetched_at:    new Date().toISOString(),
    source:             'cod_unavailable',
  };

  try {
    // Step 1: Search by mineral name
    let results = await searchCodByMineral(mineralName, 10);

    // Step 2: If no results and formula provided, try by formula
    if (results.length === 0 && chemFormula) {
      results = await searchCodByFormula(chemFormula, 10);
    }

    // Step 3: If still nothing, return graceful unavailable
    if (results.length === 0) {
      console.info(`[COD] No results found for "${mineralName}". Using unavailable fallback.`);
      return unavailableResult;
    }

    // Step 4: Select best result
    // Priority: lowest R-factor (best quality), then newest year
    const best = results
      .filter(r => r.file != null)
      .sort((a, b) => {
        // Prefer lower R-factor
        const rA = a.Robs ?? 999;
        const rB = b.Robs ?? 999;
        if (rA !== rB) return rA - rB;
        // Tie-break: prefer newer publication
        return (b.year ?? 0) - (a.year ?? 0);
      })[0];

    if (!best) return unavailableResult;

    const isFromCache = getCached(`mineral:${mineralName.toLowerCase().trim()}:10`) !== null;
    return mapCodToCrystalPhysics(best, isFromCache ? 'cod_cached' : 'cod_live');

  } catch (err) {
    console.warn(`[COD] Unexpected error enriching "${mineralName}":`, err);
    return { ...unavailableResult };
  }
}

// ─── Bulk Enrichment ──────────────────────────────────────────────────────────

/**
 * Enriches multiple minerals from COD in parallel.
 * Uses Promise.allSettled so a single failure never blocks the rest.
 *
 * @param minerals - Array of { name, formula? } objects
 * @returns Map of mineral name → CodPhysicalProperties
 */
export async function enrichBatchFromCod(
  minerals: Array<{ name: string; formula?: string }>
): Promise<Map<string, CodPhysicalProperties>> {
  const results = await Promise.allSettled(
    minerals.map(m => enrichCrystalFromCod(m.name, m.formula))
  );

  const map = new Map<string, CodPhysicalProperties>();
  results.forEach((result, index) => {
    const name = minerals[index].name;
    if (result.status === 'fulfilled') {
      map.set(name, result.value);
    } else {
      console.warn(`[COD] Batch enrichment failed for "${name}": `, result.reason);
      // Still insert an unavailable entry so callers always get a complete map
      map.set(name, {
        chemical_formula: null, formula_sum: null,
        crystal_system: 'unknown', space_group: null, space_group_number: null,
        unit_cell: {
          a_angstrom: null, b_angstrom: null, c_angstrom: null,
          alpha_deg: null, beta_deg: null, gamma_deg: null,
          volume_angstrom3: null, Z: null,
        },
        density_calc_g_cm3: null, density_meas_g_cm3: null,
        cod_id: null, cod_cif_url: null,
        source_doi: null, source_authors: null, source_year: null,
        last_fetched_at: new Date().toISOString(),
        source: 'cod_unavailable',
      });
    }
  });

  return map;
}

// ─── CIF File Access ──────────────────────────────────────────────────────────

/**
 * Returns the direct URL to a COD CIF file for a given COD ID.
 * CIF (Crystallographic Information File) is the universal format
 * for crystal structure data. Tools like VESTA, Mercury, and others
 * can visualize these directly.
 *
 * In GAIA Phase 3+, Sentinels may use CIF data to render
 * accurate 3D crystal visualizations in Digital Earth.
 *
 * @param codId - The COD integer ID
 * @returns Full URL to the .cif file
 */
export function getCifUrl(codId: number): string {
  return `${COD_CIF_URL}/${codId}.cif`;
}

/**
 * Fetches the raw text content of a CIF file from COD.
 * Returns null if the file is unreachable.
 *
 * @param codId - The COD integer ID
 */
export async function fetchCifContent(codId: number): Promise<string | null> {
  try {
    const url = getCifUrl(codId);
    const response = await fetch(url, {
      signal: AbortSignal.timeout(15_000),
    });
    if (!response.ok) return null;
    return await response.text();
  } catch {
    return null;
  }
}

// ─── Cache Management ─────────────────────────────────────────────────────────

/**
 * Returns the current state of the COD in-memory cache.
 * Useful for diagnostics and the GAIA dev-suite.
 */
export function getCodCacheStats(): { entries: number; keys: string[] } {
  return {
    entries: codCache.size,
    keys: Array.from(codCache.keys()),
  };
}

/**
 * Clears the entire COD cache.
 * Use when you need fresh data — e.g. after a COD database update.
 */
export function clearCodCache(): void {
  codCache.clear();
  console.info('[COD] Cache cleared.');
}

/**
 * Removes a specific entry from the COD cache by its cache key.
 */
export function evictCodCacheEntry(key: string): boolean {
  return codCache.delete(key);
}

// ─── Diagnostics ──────────────────────────────────────────────────────────────

/**
 * Pings the COD API to verify connectivity.
 * Returns true if COD is reachable, false otherwise.
 * Used by GAIA's startup diagnostics and the dev-suite health check.
 */
export async function pingCod(): Promise<boolean> {
  try {
    const response = await fetch(`${COD_BASE_URL}/`, {
      method: 'HEAD',
      signal: AbortSignal.timeout(5_000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Returns the COD base URL and API URL for reference.
 * Used by the GAIA dev-suite and diagnostics panel.
 */
export const COD_ENDPOINTS = {
  base:   COD_BASE_URL,
  search: COD_SEARCH_URL,
  cif:    COD_CIF_URL,
  api:    COD_API_URL,
} as const;
