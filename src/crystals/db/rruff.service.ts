/**
 * rruff.service.ts
 * Typed fetch wrapper for the RRUFF Project mineral spectral database.
 *
 * Source: https://rruff.info
 * Docs:   https://rruff.info/about/about_database.php
 *
 * RRUFF provides:
 *   - Raman spectra (laser excitation at 532nm, 785nm, 1064nm)
 *   - Infrared spectra
 *   - Powder X-ray diffraction patterns
 *   - Electron microprobe chemistry
 *   - Optical / physical property data
 *
 * The RRUFF search endpoint returns JSON when queried with
 * ?format=json&mineral=<name> or by RRUFF ID.
 */

import type { RruffSpectrum } from './crystal.schema';

// ── Constants ──────────────────────────────────────────────────────────────

const RRUFF_BASE_URL = 'https://rruff.info';

/**
 * Known laser wavelengths RRUFF uses for Raman spectra (nm).
 * Source: rruff.info/about/about_spectra.php
 */
export const RRUFF_LASER_WAVELENGTHS = [532, 780, 785, 1064] as const;
export type RruffLaserWavelength = typeof RRUFF_LASER_WAVELENGTHS[number];

// ── Types ──────────────────────────────────────────────────────────────────

export interface RruffSearchResult {
  rruff_id:     string;
  mineral_name: string;
  /** RRUFF sample URL */
  sample_url:   string;
  photo_url:    string | null;
  locality:     string | null;
  source:       string | null;
  /** Available spectrum types for this sample */
  spectrum_types: ('Raman' | 'Infrared' | 'XRD')[];
}

// ── Service Class ──────────────────────────────────────────────────────────

export class RruffService {
  private readonly baseUrl: string;

  constructor(baseUrl = RRUFF_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // ── URL builders ─────────────────────────────────────────────────────────

  /**
   * URL for the RRUFF sample page (human-readable).
   * e.g. https://rruff.info/Amethyst/R040031
   */
  samplePageUrl(mineralName: string, rruffId: string): string {
    const name = encodeURIComponent(mineralName);
    return `${this.baseUrl}/${name}/${rruffId}`;
  }

  /**
   * URL for a specific Raman spectrum data file (.txt).
   * RRUFF naming convention: R<rruff_id>__Raman__<wavelength>__0__unoriented__Raman_Data_Processed__5479.txt
   * We construct the search URL instead, which returns JSON.
   */
  ramanSearchUrl(mineralName: string): string {
    const name = encodeURIComponent(mineralName);
    return `${this.baseUrl}/sample/search?keywords=${name}&format=json`;
  }

  /**
   * URL for downloading a Raman spectrum file by RRUFF ID and laser wavelength.
   */
  ramanDataUrl(rruffId: string, laserNm: RruffLaserWavelength): string {
    return `${this.baseUrl}/sample/${rruffId}/Raman/${laserNm}nm/processed`;
  }

  /**
   * URL for the infrared spectrum data file.
   */
  infraredDataUrl(rruffId: string): string {
    return `${this.baseUrl}/sample/${rruffId}/Infrared/processed`;
  }

  /**
   * URL for the XRD pattern data file.
   */
  xrdDataUrl(rruffId: string): string {
    return `${this.baseUrl}/sample/${rruffId}/XRD/processed`;
  }

  // ── Fetch methods ─────────────────────────────────────────────────────────

  /**
   * Search RRUFF for all samples of a given mineral name.
   * Returns an array of RruffSearchResult.
   *
   * Note: RRUFF does not have a fully public JSON API in the same sense as
   * Mindat — this uses the search endpoint which returns structured JSON
   * when queried with format=json.
   */
  async searchByName(mineralName: string): Promise<RruffSearchResult[]> {
    const url = this.ramanSearchUrl(mineralName);
    const res = await fetch(url, {
      headers: { 'Accept': 'application/json' },
    });

    if (!res.ok) {
      throw new Error(
        `[RruffService] ${res.status} ${res.statusText} — searching "${mineralName}"`
      );
    }

    // RRUFF returns varied shapes; we normalise to RruffSearchResult[]
    const raw = await res.json() as any;
    return this.normaliseSearchResponse(raw, mineralName);
  }

  /**
   * Build spectrum entries for a mineral from known RRUFF IDs.
   * This constructs the data URLs without a network call —
   * use when you already know the RRUFF IDs from the crystal registry.
   */
  buildSpectra(
    mineralName: string,
    rruffIds: string[],
    laserWavelengths: RruffLaserWavelength[] = [532, 785]
  ): RruffSpectrum[] {
    const spectra: RruffSpectrum[] = [];

    for (const id of rruffIds) {
      for (const nm of laserWavelengths) {
        spectra.push({
          rruff_id:         id,
          name:             mineralName,
          spectrum_type:    'Raman',
          laser_wavelength_nm: nm,
          data_url:         this.ramanDataUrl(id, nm),
          photo_url:        `${this.baseUrl}/repository/sample_child_image/${id}`,
          locality:         null,
          source:           null,
        });
      }

      spectra.push({
        rruff_id:      id,
        name:          mineralName,
        spectrum_type: 'Infrared',
        data_url:      this.infraredDataUrl(id),
        photo_url:     `${this.baseUrl}/repository/sample_child_image/${id}`,
        locality:      null,
        source:        null,
      });

      spectra.push({
        rruff_id:      id,
        name:          mineralName,
        spectrum_type: 'XRD',
        data_url:      this.xrdDataUrl(id),
        photo_url:     `${this.baseUrl}/repository/sample_child_image/${id}`,
        locality:      null,
        source:        null,
      });
    }

    return spectra;
  }

  // ── Normalisation ─────────────────────────────────────────────────────────

  private normaliseSearchResponse(
    raw: any,
    mineralName: string
  ): RruffSearchResult[] {
    if (!raw) return [];

    // RRUFF may return an array or a {results: []} envelope
    const items: any[] = Array.isArray(raw)
      ? raw
      : Array.isArray(raw.results)
        ? raw.results
        : [];

    return items.map((item: any) => {
      const id = item.rruffid ?? item.rruff_id ?? item.id ?? '';
      return {
        rruff_id:       id,
        mineral_name:   item.mineral ?? mineralName,
        sample_url:     `${this.baseUrl}/${encodeURIComponent(mineralName)}/${id}`,
        photo_url:      item.photo ?? `${this.baseUrl}/repository/sample_child_image/${id}`,
        locality:       item.locality ?? null,
        source:         item.source ?? null,
        spectrum_types: this.inferSpectrumTypes(item),
      } satisfies RruffSearchResult;
    });
  }

  private inferSpectrumTypes(item: any): ('Raman' | 'Infrared' | 'XRD')[] {
    const types: ('Raman' | 'Infrared' | 'XRD')[] = [];
    if (item.raman)    types.push('Raman');
    if (item.infrared) types.push('Infrared');
    if (item.xrd)      types.push('XRD');
    // If no flags, assume all three are potentially available
    return types.length ? types : ['Raman', 'Infrared', 'XRD'];
  }
}

// ── Default singleton ──────────────────────────────────────────────────────

export const rruffService = new RruffService();
