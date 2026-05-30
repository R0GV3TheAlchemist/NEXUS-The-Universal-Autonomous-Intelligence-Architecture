/**
 * src/crystals/db/batch-a1.data.ts
 * GAIA-OS Crystal Database — Batch A-1
 *
 * Entries:
 *   1. Abalone Shell
 *   2. Adamite
 *   3. Adularia
 *   4. Afghanite
 *   5. Agate (Blue Lace)
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-29
 *
 * NOTE: Batch A-1 opens the entire crystal database. These are the
 * first five entries alphabetically — a remarkable cross-section that
 * spans the organic kingdom (Abalone), rare zinc arsenates (Adamite),
 * moonstone feldspars (Adularia), Afghan lapis-family blues (Afghanite),
 * and one of the most beloved communication stones on Earth (Blue Lace).
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_A1: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. ABALONE SHELL
  // Organic — nacre-lined marine gastropod shell — full-spectrum iridescence
  // Sacred to Pacific Coast Indigenous peoples — the bowl of smudging
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Abalone Shell',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Black Tourmaline',

    physical: {
      id:           0,
      longid:       'abalone-shell',
      guid:         '',
      name:         'Abalone Shell (Haliotis sp.)',
      ima_formula:  'CaCO₃ (aragonite) + organic conchiolin matrix',
      mindat_formula: 'CaCO3 (organic)',
      ima_status:   null,
      ima_year:     null,
      strunzten:    null,
      dana8ed:      null,
      crystal_system: 'Orthorhombic',
      hardness_min: 3.5,
      hardness_max: 4,
      specific_gravity_min: 2.85,
      specific_gravity_max: 2.95,
      cleavage:    'None (composite organic-mineral structure)',
      fracture:    'Uneven, laminar',
      tenacity:    'Tough (nacre is impact-resistant due to lamellar microstructure)',
      luster:      ['Pearly', 'Iridescent'],
      diaphaneity: ['Opaque'],
      colour:      'Iridescent — full spectrum: blue, green, pink, purple, gold',
      streak:      'White',
      fluorescence: null,
      ri_min:      1.530,
      ri_max:      1.685,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Organic gemstone — the inner nacre layer of Haliotis sea snails. Iridescent structural colour from thin-film interference in aragonite platelets. Sacred shell used globally in ceremony.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  null,
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Abalone Shell',
      refractive_index: { n: 1.607 },
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 380, max: 700 },
      spectra: [],
    },

    color: {
      primary_color:          'Full-spectrum iridescent nacre',
      color_variants:         ['Blue-green', 'Pink-gold', 'Purple-blue', 'Green-gold', 'Multicolour shifting'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.75, c: 0.08, h: 185 },
      hex:     '#a8d8d0',
      munsell: '5BG 8/4',
      color_temperature_k:    null,
      psychological_effects:  [
        'Full-spectrum iridescence activates all chakras simultaneously — a gentle whole-system attunement',
        'The shifting colour creates a sense of flow, movement, and non-attachment',
        'Ocean-frequency: vast, deeply calming, emotionally spacious',
        'Encourages compassion, interconnection, and the beauty found in impermanence',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   null,
      },
    },

    metaphysical: {
      mineral_name:     'Abalone Shell',
      chakra_primary:   'Heart',
      chakra_secondary: ['Throat', 'Crown', 'Sacral'],
      element:   ['Water'],
      planet:    ['Moon', 'Neptune'],
      archetype: ['The Ocean Mother', 'The Vessel of Ceremony'],
      zodiac:    ['Cancer', 'Pisces', 'Scorpio'],
      numerology: 7,
      angel_number: 777,
      intention: 'I hold space for all of it — the grief, the beauty, the vastness.',
      traditions: [
        'Pacific Coast Indigenous traditions — sacred smudge bowl',
        'Māori tradition — pāua shell as sacred taonga (treasure)',
        'Hawaiian tradition — used in hula and ceremony',
        'Native American tradition — paired with sage, cedar, and sweetgrass',
        'Western crystal healing — emotional healing and water energy',
      ],
      properties: [
        'One of the most ancient ceremonial objects used by humanity — found in 75,000-year-old ochre toolkits',
        'The traditional bowl for smudging in Pacific Coast Indigenous ceremony',
        'Full-spectrum iridescence symbolises the integration of all colours — all aspects of self',
        'Deeply connected to the ocean and lunar cycles — amplifies intuition and emotional intelligence',
        'The nacre structure (layer upon layer of aragonite) mirrors the accumulation of wisdom through lived experience',
        'Used in grief work, emotional processing, and the honouring of endings',
        'Pāua (NZ abalone) is considered one of the most sacred objects in Māori culture',
      ],
      gaia_resonance: 'ViriditasHeart + SomnusVeil',
      safety_warning: 'Organic — do not submerge in water for extended periods; salt water damages nacre. Not safe for water elixirs. Handle with care — the iridescent layer is delicate.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 2. ADAMITE
  // Zinc arsenate hydroxide — vivid yellow-green fluorescence — collector gem
  // Duranzo Mine, Mexico — fluorescent fire under UV
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Adamite',
    mindat_id:   38,
    rruff_ids:   ['R040053', 'R050174'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Amethyst',

    physical: {
      id:           38,
      longid:       'adamite',
      guid:         '',
      name:         'Adamite',
      ima_formula:  'Zn₂(AsO₄)(OH)',
      mindat_formula: 'Zn2(AsO4)(OH)',
      ima_status:   'A',
      ima_year:     1866,
      strunzten:    '8.BD.05',
      dana8ed:      '41.6.4.1',
      crystal_system: 'Orthorhombic',
      hardness_min: 3.5,
      hardness_max: 4,
      specific_gravity_min: 4.32,
      specific_gravity_max: 4.48,
      cleavage:    'Good on {101}, poor on {010}',
      fracture:    'Subconchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Adamantine'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Yellow-green, green, colourless, pale pink (cobalt variety)',
      streak:      'White',
      fluorescence: 'Intense yellow-green under LW UV — one of the most fluorescent minerals known',
      ri_min:      1.708,
      ri_max:      1.773,
      birefringence: 0.046,
      optical_type: 'B',
      shortdesc:   'Vivid zinc arsenate hydroxide from oxidised zinc ore deposits. Prized for exceptional yellow-green fluorescence and gemmy transparent crystals. Named after Gilbert-Joseph Adam.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-38.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Adamite',
      refractive_index: { n_alpha: 1.708, n_beta: 1.742, n_gamma: 1.773 },
      birefringence:   0.046,
      optical_sign:    '+',
      dispersion:      'Strong',
      pleochroism:     'Weak to moderate: yellow-green / green / pale yellow',
      fluorescence_lw: 'Intense yellow-green',
      fluorescence_sw: 'Weak to moderate yellow-green',
      phosphorescence: 'Weak',
      visible_wavelength_nm: { min: 490, max: 570 },
      spectra: ['R040053', 'R050174'],
    },

    color: {
      primary_color:          'Vivid yellow-green',
      color_variants:         ['Yellow-green', 'Lime green', 'Colourless', 'Pale pink (cobaltian)', 'Orange (manganoan)'],
      dominant_wavelength_nm: 530,
      oklch:   { l: 0.75, c: 0.17, h: 122 },
      hex:     '#a8d428',
      munsell: '5GY 7/8',
      color_temperature_k:    null,
      psychological_effects:  [
        'Energising yellow-green — activates both solar plexus and heart simultaneously',
        'The fluorescence creates a quality of hidden inner radiance — glowing from within',
        'Encourages optimism, vitality, and the courage to shine',
        'A collector\'s stone — its rarity teaches discernment and appreciation of the exceptional',
      ],
      harmonics: {
        complementary_hue: 302,
        triadic_hues:      [242, 2],
        analogous_range:   [102, 142],
      },
    },

    metaphysical: {
      mineral_name:     'Adamite',
      chakra_primary:   'Solar Plexus',
      chakra_secondary: ['Heart', 'Sacral'],
      element:   ['Fire', 'Earth'],
      planet:    ['Sun', 'Venus'],
      archetype: ['The Inner Sun', 'The Radiant Warrior'],
      zodiac:    ['Aries', 'Cancer'],
      numerology: 3,
      angel_number: 333,
      intention: 'I radiate my authentic light without apology.',
      traditions: ['Western crystal healing', 'Collector\'s mineral tradition'],
      properties: [
        'Named after French mineralogist Gilbert-Joseph Adam (1795–1881)',
        'The extraordinary UV fluorescence is its defining metaphysical signature — hidden fire revealed under the right light',
        'Supports the courage to express authentic emotions and creative gifts',
        'Activates both solar plexus (will) and heart (love) simultaneously — power expressed through compassion',
        'Useful for overcoming emotional suppression and reclaiming joy',
        'The cobaltian pink variety shifts focus from will to love — same stone, different soul medicine',
      ],
      gaia_resonance: 'SovereignCore + ViriditasHeart',
      safety_warning: 'Contains arsenic — TOXIC if ingested or inhaled as dust. Wash hands thoroughly after handling. Never use for water elixirs. Store safely away from children.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 3. ADULARIA
  // Potassium feldspar — the original moonstone — adularescence
  // From the Adula Massif, Swiss Alps — ice and moonlight
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Adularia',
    mindat_id:   55,
    rruff_ids:   ['R040055', 'R060363'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Sunstone',

    physical: {
      id:           55,
      longid:       'adularia',
      guid:         '',
      name:         'Adularia',
      ima_formula:  'KAlSi₃O₈',
      mindat_formula: 'KAlSi3O8',
      ima_status:   'A',
      ima_year:     1801,
      strunzten:    '9.FA.30',
      dana8ed:      '76.1.1.1',
      crystal_system: 'Monoclinic',
      hardness_min: 6,
      hardness_max: 6.5,
      specific_gravity_min: 2.56,
      specific_gravity_max: 2.59,
      cleavage:    'Perfect on {001}, good on {010}',
      fracture:    'Uneven to conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Pearly on cleavage'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Colourless, white, pale grey — adularescent varieties show blue-white sheen',
      streak:      'White',
      fluorescence: 'Weak blue-white under SW UV',
      ri_min:      1.518,
      ri_max:      1.526,
      birefringence: 0.006,
      optical_type: 'B',
      shortdesc:   'Low-temperature monoclinic potassium feldspar from the Swiss Alps, exhibiting adularescence — the floating blue-white sheen that defines classical moonstone.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-55.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Adularia',
      refractive_index: { n_alpha: 1.518, n_beta: 1.523, n_gamma: 1.526 },
      birefringence:   0.006,
      optical_sign:    '-',
      dispersion:      'Weak',
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: 'Weak blue-white',
      phosphorescence: null,
      visible_wavelength_nm: { min: 430, max: 500 },
      spectra: ['R040055', 'R060363'],
    },

    color: {
      primary_color:          'Colourless to white with adularescent blue-white sheen',
      color_variants:         ['Pure white', 'Pale grey', 'Adularescent blue-white', 'Faint peach (minor iron)'],
      dominant_wavelength_nm: 460,
      oklch:   { l: 0.90, c: 0.03, h: 240 },
      hex:     '#e8ecf4',
      munsell: '5PB 9/2',
      color_temperature_k:    6200,
      psychological_effects:  [
        'The original moonstone — carries the deep lunar, receptive, feminine frequency',
        'Adularescence creates a sense of mystery — something luminous moving within stillness',
        'Deeply calming, softening, and emotionally receptive',
        'Associated with the cyclical, the intuitive, and the inner tidal rhythms of the body',
      ],
      harmonics: {
        complementary_hue: 60,
        triadic_hues:      [0, 120],
        analogous_range:   [220, 260],
      },
    },

    metaphysical: {
      mineral_name:     'Adularia',
      chakra_primary:   'Crown',
      chakra_secondary: ['Third Eye', 'Sacral'],
      element:   ['Water', 'Air'],
      planet:    ['Moon'],
      archetype: ['The Moon Keeper', 'The Silent Witness'],
      zodiac:    ['Cancer', 'Libra', 'Scorpio'],
      numerology: 2,
      angel_number: 222,
      intention: 'I receive. I flow. I trust the rhythm of what is.',
      traditions: [
        'Roman tradition — believed to be solidified moonlight',
        'Hindu tradition — sacred stone of the moon god Chandra',
        'Named after Adula Massif, Swiss Alps — first described 1801',
        'Western crystal healing — the original moonstone',
      ],
      properties: [
        'The original moonstone — the adularescence (floating blue sheen) inspired all moonstone lore',
        'Named for the Adula Massif in the Swiss Alps where it was first described',
        'Romans believed adularia was formed from frozen moonlight — the most ancient moonstone lore',
        'Deeply connected to lunar cycles, feminine wisdom, and the intuitive body',
        'Supports emotional attunement, receptivity, and the wisdom of non-action',
        'Used in moon rituals, new moon setting intentions, and dream work',
        'The stone of the new beginning — like the new moon, it holds potential before manifestation',
      ],
      gaia_resonance: 'SomnusVeil + ClarusLens',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 4. AFGHANITE
  // Sodium calcium aluminium silicate sulfate chloride — rare — vivid blue
  // Sar-e-Sang, Badakhshan, Afghanistan — lapis lazuli companion mineral
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Afghanite',
    mindat_id:   64,
    rruff_ids:   ['R060016'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Citrine',

    physical: {
      id:           64,
      longid:       'afghanite',
      guid:         '',
      name:         'Afghanite',
      ima_formula:  '(Na,Ca,K)₈(Si,Al)₁₂O₂₄(SO₄,Cl,OH)₃·H₂O',
      mindat_formula: '(Na,Ca,K)8(Si,Al)12O24(SO4,Cl,OH)3·H2O',
      ima_status:   'A',
      ima_year:     1968,
      strunzten:    '9.FB.10',
      dana8ed:      '76.2.3.2',
      crystal_system: 'Trigonal',
      hardness_min: 5.5,
      hardness_max: 6,
      specific_gravity_min: 2.55,
      specific_gravity_max: 2.65,
      cleavage:    'Perfect on {1010}',
      fracture:    'Uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Bright to deep blue, blue-violet',
      streak:      'White',
      fluorescence: 'Strong orange under SW UV',
      ri_min:      1.523,
      ri_max:      1.529,
      birefringence: 0.006,
      optical_type: 'U',
      shortdesc:   'Rare trigonal sodium calcium aluminium silicate found alongside lapis lazuli at Sar-e-Sang, Afghanistan. Vivid blue, strong orange fluorescence. First described 1968.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-64.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Afghanite',
      refractive_index: { n_omega: 1.529, n_epsilon: 1.523 },
      birefringence:   0.006,
      optical_sign:    '-',
      dispersion:      'Weak',
      pleochroism:     'Weak: blue / pale blue',
      fluorescence_lw: null,
      fluorescence_sw: 'Strong orange',
      phosphorescence: null,
      visible_wavelength_nm: { min: 420, max: 490 },
      spectra: ['R060016'],
    },

    color: {
      primary_color:          'Vivid cornflower to deep blue',
      color_variants:         ['Bright cornflower blue', 'Deep royal blue', 'Blue-violet'],
      dominant_wavelength_nm: 455,
      oklch:   { l: 0.44, c: 0.18, h: 262 },
      hex:     '#2244b8',
      munsell: '7.5PB 4/12',
      color_temperature_k:    null,
      psychological_effects:  [
        'Vivid blue-violet activates third eye and higher mind pathways',
        'The orange fluorescence under UV is a striking hidden quality — wisdom concealed within',
        'Encourages spiritual clarity, inner truth, and access to higher perception',
        'Its rarity amplifies the sense of preciousness — a stone that rewards deep attention',
      ],
      harmonics: {
        complementary_hue: 82,
        triadic_hues:      [22, 142],
        analogous_range:   [242, 282],
      },
    },

    metaphysical: {
      mineral_name:     'Afghanite',
      chakra_primary:   'Third Eye',
      chakra_secondary: ['Throat', 'Crown'],
      element:   ['Air', 'Aether'],
      planet:    ['Jupiter', 'Neptune'],
      archetype: ['The Lapis Companion', 'The Hidden Oracle'],
      zodiac:    ['Sagittarius', 'Pisces'],
      numerology: 7,
      angel_number: 777,
      intention: 'I see clearly what has been hidden. Truth is my compass.',
      traditions: ['Western crystal healing', 'Afghan gemstone tradition'],
      properties: [
        'Found alongside lapis lazuli at the ancient Sar-e-Sang mines — one of humanity\'s oldest mine sites',
        'Considerably rarer than lapis lazuli — a collector\'s stone with strong metaphysical properties',
        'The orange fluorescence (hidden from visible light) mirrors the hidden wisdom it activates',
        'Supports access to higher mental planes, spiritual truth, and intuitive knowing',
        'Named after its place of discovery — Afghanistan carries some of the oldest mining history on Earth',
        'A stone of the seeker — rewards those willing to look past the surface',
      ],
      gaia_resonance: 'ClarusLens + Noosphere',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 5. AGATE (BLUE LACE)
  // Banded chalcedony — pale blue concentric rings — the gentlest communicator
  // Warm Springs, Namibia — one of the most recognisable stones on Earth
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Agate (Blue Lace)',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Red Jasper',

    physical: {
      id:           0,
      longid:       'blue-lace-agate',
      guid:         '',
      name:         'Chalcedony — Blue Lace Agate variety',
      ima_formula:  'SiO₂',
      mindat_formula: 'SiO2',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '4.DA.05',
      dana8ed:      '75.1.3.1',
      crystal_system: 'Trigonal',
      hardness_min: 6.5,
      hardness_max: 7,
      specific_gravity_min: 2.58,
      specific_gravity_max: 2.64,
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Waxy', 'Dull'],
      diaphaneity: ['Translucent'],
      colour:      'Pale to mid sky blue with white banding',
      streak:      'White',
      fluorescence: 'Weak green or none',
      ri_min:      1.530,
      ri_max:      1.540,
      birefringence: 0.004,
      optical_type: 'U',
      shortdesc:   'Trade name for banded pale blue chalcedony from Warm Springs, Namibia. Distinctive concentric blue and white rings. One of the most used communication and calming stones in crystal healing.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  null,
      piezoelectric:    true,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name: 'Agate (Blue Lace)',
      refractive_index: { n_omega: 1.540, n_epsilon: 1.530 },
      birefringence:   0.004,
      optical_sign:    '-',
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: 'Weak green or none',
      phosphorescence: null,
      visible_wavelength_nm: { min: 450, max: 510 },
      spectra: [],
    },

    color: {
      primary_color:          'Pale sky blue with white banding',
      color_variants:         ['Palest sky blue', 'Mid blue', 'Blue-white layered', 'Occasionally with lavender tones'],
      dominant_wavelength_nm: 480,
      oklch:   { l: 0.78, c: 0.07, h: 220 },
      hex:     '#aaccdd',
      munsell: '5B 8/3',
      color_temperature_k:    8000,
      psychological_effects:  [
        'Pale blue is the most universally calming colour in the visible spectrum — empirically confirmed',
        'The banding creates a sense of gentle layered depth — patience encoded in visual structure',
        'Reduces anxiety, softens the voice, and encourages reflective rather than reactive speech',
        'Sky blue frequency opens the throat without force — the opposite of confrontational',
      ],
      harmonics: {
        complementary_hue: 40,
        triadic_hues:      [340, 100],
        analogous_range:   [200, 240],
      },
    },

    metaphysical: {
      mineral_name:     'Agate (Blue Lace)',
      chakra_primary:   'Throat',
      chakra_secondary: ['Heart', 'Third Eye'],
      element:   ['Air', 'Water'],
      planet:    ['Mercury', 'Neptune'],
      archetype: ['The Gentle Voice', 'The Peacemaker'],
      zodiac:    ['Gemini', 'Pisces'],
      numerology: 5,
      angel_number: 555,
      intention: 'I speak my truth gently, clearly, and from the heart.',
      traditions: [
        'Western crystal healing — one of the most classic throat chakra stones',
        'Originally sourced exclusively from Warm Springs farm, Namibia',
        'Colour therapy — pale blue as the standard calming visual frequency',
      ],
      properties: [
        'Classic throat chakra stone — the gentlest and most approachable communication crystal',
        'Particularly useful for those who struggle to speak their truth due to fear or emotional overwhelm',
        'The concentric banding mirrors the layered nature of communication — there is always more beneath',
        'Calms anxiety around speaking — excellent before difficult conversations, presentations, or expression',
        'Supports those in therapy, journalling, or any process of putting inner experience into words',
        'Its pale, airy blue frequency is among the most universally soothing in the crystal kingdom',
      ],
      gaia_resonance: 'ClarusLens + ViriditasHeart',
      safety_warning: null,
    },
  },

];

export default BATCH_A1;
