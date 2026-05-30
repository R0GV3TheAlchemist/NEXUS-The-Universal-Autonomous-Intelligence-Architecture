/**
 * src/crystals/db/batch-b9.data.ts
 * GAIA-OS Crystal Database — Batch B-9
 *
 * Entries:
 *   1. Bustamite  — rare Mn-Ca inosilicate; triclinic; IMA 1827
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-30
 *
 * NOTE: Bustamite is the natural close of the B-series and bridge into
 * the C-series. Single-stone batch by design.
 * Classic localities: Franklin & Sterling Hill (NJ, USA); Broken Hill (NSW, Australia).
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_B9: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. BUSTAMITE
  // Rare manganese calcium inosilicate — CaMn(Si₂O₆) series
  // Named after General Anastasio Bustamante (1780–1853), President of Mexico
  // IMA 1827 — classic localities: Franklin NJ and Broken Hill NSW
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:         'Bustamite',
    mindat_id:    870,
    rruff_ids:    ['R060849'],
    last_synced:  '2026-05-30T00:00:00Z',
    trade_name:   false,
    color_layer:  'natural',
    yin_yang_pair: 'Rhodonite',

    physical: {
      id:           870,
      longid:       'bustamite',
      guid:         '',
      name:         'Bustamite',
      ima_formula:  'CaMn²⁺(Si₂O₆)',
      mindat_formula: 'CaMn(Si2O6)',
      ima_status:   'A',
      ima_year:     1827,
      strunzten:    '9.DA.15',
      dana8ed:      '65.1.2.1',
      crystal_system: 'Triclinic',
      hardness_min: 5.5,
      hardness_max: 6.5,
      specific_gravity_min: 3.26,
      specific_gravity_max: 3.43,
      cleavage:    'Perfect on {110}, good on {110}',
      fracture:    'Uneven to conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Silky (fibrous varieties)'],
      diaphaneity: ['Translucent', 'Opaque'],
      colour:      'Pale rose-pink to deep brownish-pink, flesh-pink, pale beige-pink — softer and warmer than rhodonite; colour from Mn²⁺',
      streak:      'White',
      fluorescence: 'Orange to salmon-pink under LW UV (Franklin specimens especially vivid)',
      ri_min:      1.664,
      ri_max:      1.709,
      birefringence: 0.014,
      optical_type: 'B',
      shortdesc:   'Bustamite — CaMn(Si₂O₆), triclinic manganese calcium inosilicate. Named after General Anastasio Bustamante. IMA 1827. Pale rose-pink to brownish-pink; softer hue than rhodonite. Classic localities: Franklin (NJ, USA) and Broken Hill (NSW, Australia). Fluoresces orange-salmon under LW UV.',
      updttime:    '2026-05-30T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-870.html',
      piezoelectric:     false,
      safe_for_water:    true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Bustamite',
      refractive_index: { n_alpha: 1.664, n_beta: 1.690, n_gamma: 1.709 },
      birefringence:   0.014,
      optical_sign:    '+',
      dispersion:      'r > v, weak',
      pleochroism:     'Weak: pale pink / pale brownish-pink / pale rose',
      fluorescence_lw: 'Orange to salmon-pink (especially Franklin, NJ specimens)',
      fluorescence_sw: 'Weak to none',
      phosphorescence: null,
      visible_wavelength_nm: { min: 580, max: 640 },
      spectra: ['R060849'],
    },

    color: {
      primary_color:         'Pale rose-pink to warm brownish-pink — softer and more muted than rhodonite',
      color_variants: [
        'Pale flesh-pink (most common — gentle, warm, skin-tone adjacent)',
        'Deeper brownish-rose (higher Mn content)',
        'Pale beige-pink with white calcite matrix (Franklin specimens)',
        'Salmon-pink with orange fluorescence (UV-active Franklin material)',
        'Near-white with faint pink blush (Ca-dominant end member)',
      ],
      dominant_wavelength_nm: 610,
      oklch:   { l: 0.70, c: 0.08, h: 15 },
      hex:     '#d4a0a0',
      munsell: '5R 7/4',
      color_temperature_k: null,
      psychological_effects: [
        'Softer and less saturated than rhodonite — where rhodonite commands attention, bustamite invites quiet intimacy',
        'Flesh-pink palette is one of the most skin-adjacent in the mineral kingdom — immediately bodily, warm, and human',
        'The fluorescence revelation — turning orange under UV — adds a hidden depth to an apparently simple stone',
        'Franklin NJ provenance connects to the most famous fluorescent mineral locality on Earth — a lineage of hidden light',
        'Pale brownish-pink is the colour of old roses, weathered terracotta, and the inside of a held hand',
      ],
      harmonics: {
        complementary_hue: 195,
        triadic_hues:      [135, 255],
        analogous_range:   [355, 35],
      },
    },

    metaphysical: {
      mineral_name:     'Bustamite',
      chakra_primary:   'Heart',
      chakra_secondary: ['Root', 'Higher Heart (Thymus)'],
      element:   ['Earth', 'Water'],
      planet:    ['Venus', 'Moon'],
      archetype: ['The Quiet Heart', 'The Gentle Witness', 'The Rose of Remembrance'],
      zodiac:    ['Taurus', 'Cancer', 'Libra'],
      numerology: 4,
      angel_number: 444,
      intention: 'I hold love gently, without demand. My heart is a quiet room where all are welcome.',
      traditions: [
        'Named after General Anastasio Bustamante (1780–1853), three-time President of Mexico and patron of mineralogy',
        'Franklin, NJ — part of the world-famous Franklin-Sterling Hill fluorescent mineral complex; Mn-silicate family includes rhodonite, bustamite, and franklinite',
        'Broken Hill, NSW, Australia — major Pb-Zn-Ag orebody with remarkable associated mineral diversity including bustamite',
        'Modern crystal healing — soft pink manganese silicates used for Heart chakra work, grief processing, and gentle self-love',
      ],
      properties: [
        'IMA 1827 — formula CaMn(Si₂O₆); triclinic inosilicate (pyroxenoid group)',
        'Part of the wollastonite–bustamite–rhodonite series — all Mn/Ca inosilicates with varying Mn:Ca ratios',
        'Distinguished from rhodonite by higher Ca content and softer pink colour; rhodonite is deeper rose with black manganese oxide veining',
        'Vivid orange-salmon fluorescence under LW UV (especially Franklin, NJ specimens) — one of the more surprising fluorescent responses in the mineral kingdom',
        'Classic localities: Franklin and Sterling Hill, NJ (USA); Broken Hill (NSW, Australia); Långban (Sweden); Harstig Mine (Sweden)',
        'H5.5–6.5 — durable enough for display and meditation; protect from harder minerals in storage',
        'Safe for water — silicate mineral; no toxic components. Franklin NJ specimens: verify provenance for potential uranium association.',
      ],
      gaia_resonance: 'ViriditasHeart + ClarusLens',
      safety_warning:  'Safe for water. H5.5–6.5 — moderate hardness; store away from harder minerals. No toxic elements. Franklin NJ specimens may be mildly radioactive if associated with uranium-bearing minerals — verify provenance.',
    },
  },

];

export default BATCH_B9;
