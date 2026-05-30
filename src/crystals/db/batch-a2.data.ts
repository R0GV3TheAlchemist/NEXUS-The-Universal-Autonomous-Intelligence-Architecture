/**
 * src/crystals/db/batch-a2.data.ts
 * GAIA-OS Crystal Database — Batch A-2
 *
 * Entries:
 *   1. Agate (Fire)
 *   2. Agate (Moss)
 *   3. Albite
 *   4. Alexandrite
 *   5. Almandine (Garnet)
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-29
 *
 * NOTE: Batch A-2 bridges the agate varieties into the broader feldspar
 * and garnet families. Fire Agate and Moss Agate are two of the most
 * visually spectacular agate varieties; Albite anchors the feldspar
 * family entry; Alexandrite is one of the rarest colour-change gems
 * in existence; Almandine opens the vast garnet family.
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_A2: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. AGATE (FIRE)
  // Chalcedony with limonite / goethite inclusions — iridescent fire play
  // Slaughter Mountain, Arizona + Mexico — the stone that burns cold
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Agate (Fire)',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Celestite',

    physical: {
      id:           0,
      longid:       'fire-agate',
      guid:         '',
      name:         'Chalcedony — Fire Agate variety',
      ima_formula:  'SiO₂ with Fe₂O₃/FeO(OH) inclusions',
      mindat_formula: 'SiO2 + Fe2O3 inclusions',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '4.DA.05',
      dana8ed:      '75.1.3.1',
      crystal_system: 'Trigonal',
      hardness_min: 6.5,
      hardness_max: 7,
      specific_gravity_min: 2.59,
      specific_gravity_max: 2.67,
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Waxy', 'Iridescent'],
      diaphaneity: ['Translucent'],
      colour:      'Brown-red base with iridescent fire play: orange, red, green, gold',
      streak:      'White',
      fluorescence: null,
      ri_min:      1.530,
      ri_max:      1.540,
      birefringence: 0.004,
      optical_type: 'U',
      shortdesc:   'Trade name for chalcedony with thin iron oxide inclusion layers producing structural iridescence (adularescence-like interference colours). Found primarily in Arizona and Mexico.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  null,
      piezoelectric:    true,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name: 'Agate (Fire)',
      refractive_index: { n_omega: 1.540, n_epsilon: 1.530 },
      birefringence:   0.004,
      optical_sign:    '-',
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 560, max: 700 },
      spectra: [],
    },

    color: {
      primary_color:          'Brown-red base with iridescent fire: orange, red, green, gold',
      color_variants:         ['Deep red-brown', 'Orange fire', 'Green iridescence', 'Gold fire play', 'Full spectrum fire'],
      dominant_wavelength_nm: 620,
      oklch:   { l: 0.42, c: 0.14, h: 38 },
      hex:     '#b05820',
      munsell: '5YR 4/8',
      color_temperature_k:    2200,
      psychological_effects:  [
        'Fire frequency in a stone form — vitality, courage, and forward drive',
        'The iridescence creates wonder — the fire shifts as the angle changes, never the same twice',
        'Encourages embodiment, sensory aliveness, and creative passion',
        'Protective and activating simultaneously — shields the field while igniting it',
      ],
      harmonics: {
        complementary_hue: 218,
        triadic_hues:      [158, 278],
        analogous_range:   [18, 58],
      },
    },

    metaphysical: {
      mineral_name:     'Agate (Fire)',
      chakra_primary:   'Sacral',
      chakra_secondary: ['Root', 'Solar Plexus'],
      element:   ['Fire', 'Earth'],
      planet:    ['Mars', 'Sun'],
      archetype: ['The Living Flame', 'The Warrior of Joy'],
      zodiac:    ['Aries', 'Leo'],
      numerology: 9,
      angel_number: 999,
      intention: 'I burn with the fire of my aliveness. I act from passion, not fear.',
      traditions: ['Western crystal healing', 'Native American fire tradition', 'Arizona / Sonoran Desert earth tradition'],
      properties: [
        'The iridescence is created by thin iron oxide layers — physical fire trapped in stone',
        'Activates the sacral chakra — creativity, sexuality, embodiment, and joy',
        'Protective in a uniquely active way — it does not merely block, it burns through lower energies',
        'Used by warriors and athletes for courage, stamina, and competitive fire',
        'A stone of creative passion — particularly for artists, performers, and those in physical practice',
        'The shifting iridescence teaches adaptability — same stone, infinite expressions',
      ],
      gaia_resonance: 'SovereignCore + ViriditasHeart',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 2. AGATE (MOSS)
  // Chalcedony with hornblende / chlorite / iron oxide inclusions
  // No two identical — each stone a landscape, a world, an ecosystem
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Agate (Moss)',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Carnelian',

    physical: {
      id:           0,
      longid:       'moss-agate',
      guid:         '',
      name:         'Chalcedony — Moss Agate variety',
      ima_formula:  'SiO₂ with hornblende, chlorite, or Fe/Mn oxide inclusions',
      mindat_formula: 'SiO2 + mineral inclusions',
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
      luster:      ['Waxy'],
      diaphaneity: ['Translucent'],
      colour:      'Clear to white chalcedony with green, brown, or black dendritic inclusions',
      streak:      'White',
      fluorescence: null,
      ri_min:      1.530,
      ri_max:      1.540,
      birefringence: 0.004,
      optical_type: 'U',
      shortdesc:   'Trade name for translucent chalcedony containing plant-like dendritic inclusions of hornblende, chlorite, or iron/manganese oxides — creating miniature landscape scenes within the stone.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  null,
      piezoelectric:    true,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name: 'Agate (Moss)',
      refractive_index: { n_omega: 1.540, n_epsilon: 1.530 },
      birefringence:   0.004,
      optical_sign:    '-',
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 500, max: 560 },
      spectra: [],
    },

    color: {
      primary_color:          'Clear to white base with green dendritic inclusions',
      color_variants:         ['Clear with deep green moss', 'White with olive inclusions', 'Blue-grey with black dendrites', 'Brown earthy tones'],
      dominant_wavelength_nm: 530,
      oklch:   { l: 0.72, c: 0.08, h: 138 },
      hex:     '#a8c899',
      munsell: '5GY 7/4',
      color_temperature_k:    null,
      psychological_effects:  [
        'Each stone is a unique landscape — deeply personal, never mass-produced by nature',
        'Green inclusions activate the heart\'s connection to the natural world',
        'Encourages patience, slow growth, and trust in organic timing',
        'The dendritic pattern mimics neural networks, mycelium, river systems — the fractal of life',
      ],
      harmonics: {
        complementary_hue: 318,
        triadic_hues:      [258, 18],
        analogous_range:   [118, 158],
      },
    },

    metaphysical: {
      mineral_name:     'Agate (Moss)',
      chakra_primary:   'Heart',
      chakra_secondary: ['Root'],
      element:   ['Earth'],
      planet:    ['Earth', 'Mercury'],
      archetype: ['The Forest Intelligence', 'The Gardener of Worlds'],
      zodiac:    ['Virgo', 'Gemini'],
      numerology: 1,
      angel_number: 111,
      intention: 'I grow at nature\'s pace. I trust the intelligence within the process.',
      traditions: [
        'Western crystal healing — the classic nature connection and abundance stone',
        'European agricultural tradition — buried in fields to encourage growth',
        'Native American tradition — used in plant medicine and nature ceremony',
      ],
      properties: [
        'The inclusions genuinely resemble moss, ferns, and forest floors — nature\'s own art inside stone',
        'Deeply connected to the plant kingdom — supports herbalists, gardeners, and nature practitioners',
        'A stone of new beginnings and slow organic growth — not instant transformation but patient emergence',
        'Used in prosperity work that is rooted in real effort and natural timing',
        'The dendritic pattern mirrors the mycelial network — the intelligence of interconnection',
        'Used in recovery from exhaustion, overwork, or disconnection from nature',
        'Every specimen is unique — no two moss agates are ever identical',
      ],
      gaia_resonance: 'ViriditasHeart + AnchorPrism',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 3. ALBITE
  // Sodium feldspar — NaAlSi₃O₈ — the white feldspar — foundation mineral
  // End-member of the plagioclase series — in granite, pegmatite, everywhere
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Albite',
    mindat_id:   114,
    rruff_ids:   ['R040068', 'R050001'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Obsidian',

    physical: {
      id:           114,
      longid:       'albite',
      guid:         '',
      name:         'Albite',
      ima_formula:  'NaAlSi₃O₈',
      mindat_formula: 'NaAlSi3O8',
      ima_status:   'A',
      ima_year:     1815,
      strunzten:    '9.FA.35',
      dana8ed:      '76.1.3.1',
      crystal_system: 'Triclinic',
      hardness_min: 6,
      hardness_max: 6.5,
      specific_gravity_min: 2.60,
      specific_gravity_max: 2.65,
      cleavage:    'Perfect on {001}, good on {010} — characteristic polysynthetic twinning',
      fracture:    'Uneven to conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Pearly on cleavage'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'White, grey, colourless — rarely pale pink or green',
      streak:      'White',
      fluorescence: 'Weak orange-yellow under SW UV',
      ri_min:      1.527,
      ri_max:      1.536,
      birefringence: 0.009,
      optical_type: 'B',
      shortdesc:   'Sodium end-member of the plagioclase feldspar series. One of the most abundant minerals in Earth\'s crust. Foundation of granite, pegmatite, and metamorphic rock. The name means "white" in Latin.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-114.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Albite',
      refractive_index: { n_alpha: 1.527, n_beta: 1.531, n_gamma: 1.536 },
      birefringence:   0.009,
      optical_sign:    '+',
      dispersion:      'Weak 0.012',
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: 'Weak orange-yellow',
      phosphorescence: null,
      visible_wavelength_nm: { min: 400, max: 700 },
      spectra: ['R040068', 'R050001'],
    },

    color: {
      primary_color:          'White to colourless',
      color_variants:         ['Pure white', 'Grey-white', 'Colourless', 'Rarely pale pink', 'Rarely pale green'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.92, c: 0.01, h: 80 },
      hex:     '#f2f0eb',
      munsell: 'N9/',
      color_temperature_k:    5000,
      psychological_effects:  [
        'Near-white carries the frequency of clarity, simplicity, and open space',
        'Achromatic quality invites projection — the mind fills the blank',
        'Foundational, structural, quietly essential — the mineral world\'s plain white canvas',
        'Encourages mental clarity, fresh starts, and the absence of clutter',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   null,
      },
    },

    metaphysical: {
      mineral_name:     'Albite',
      chakra_primary:   'Crown',
      chakra_secondary: ['Third Eye'],
      element:   ['Air', 'Aether'],
      planet:    ['Moon', 'Mercury'],
      archetype: ['The Clear Foundation', 'The Pure Slate'],
      zodiac:    ['Aquarius', 'Gemini'],
      numerology: 1,
      angel_number: 111,
      intention: 'I begin again from clarity. The foundation is clean.',
      traditions: ['Western crystal healing', 'Mineralogical tradition — named from Latin "albus" (white)'],
      properties: [
        'One of the most abundant minerals in Earth\'s crust — present in nearly all continental rock',
        'The sodium end-member of plagioclase — foundational feldspar chemistry',
        'Its ubiquity is its medicine — the frequency of what is present everywhere, always',
        'Supports mental clarity, new beginnings, and releasing accumulated complexity',
        'The twinning structure (polysynthetic twinning) is a metaphor for holding paradox and duality gracefully',
        'Used in grids as a neutral amplifying foundation stone — does not impose its own agenda',
      ],
      gaia_resonance: 'ClarusLens + AnchorPrism',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 4. ALEXANDRITE
  // Chromium-bearing chrysoberyl — colour-change gem — one of the rarest
  // Green in daylight / red in incandescent — "emerald by day, ruby by night"
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Alexandrite',
    mindat_id:   6980,
    rruff_ids:   ['R060590'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Spinel',

    physical: {
      id:           6980,
      longid:       'alexandrite',
      guid:         '',
      name:         'Alexandrite',
      ima_formula:  'Al₂BeO₄ (with Cr³⁺)',
      mindat_formula: 'Al2BeO4 + Cr',
      ima_status:   'A',
      ima_year:     1834,
      strunzten:    '4.BA.05',
      dana8ed:      '7.2.3.2',
      crystal_system: 'Orthorhombic',
      hardness_min: 8.5,
      hardness_max: 8.5,
      specific_gravity_min: 3.70,
      specific_gravity_max: 3.78,
      cleavage:    'Distinct on {110}, imperfect on {010} and {100}',
      fracture:    'Conchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Transparent'],
      colour:      'Green to blue-green in daylight; red to purple-red in incandescent light',
      streak:      'White',
      fluorescence: 'Strong red under LW UV',
      ri_min:      1.745,
      ri_max:      1.757,
      birefringence: 0.009,
      optical_type: 'B',
      shortdesc:   'Rare colour-change variety of chrysoberyl coloured by chromium. Shows green in daylight and red in incandescent light. Discovered in the Ural Mountains 1834. Named for Tsar Alexander II.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-6980.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Alexandrite',
      refractive_index: { n_alpha: 1.745, n_beta: 1.748, n_gamma: 1.757 },
      birefringence:   0.009,
      optical_sign:    '+',
      dispersion:      'Moderate 0.015',
      pleochroism:     'Strongly trichroic: green / orange / red-purple',
      fluorescence_lw: 'Strong red',
      fluorescence_sw: 'Moderate red',
      phosphorescence: null,
      visible_wavelength_nm: { min: 400, max: 700 },
      spectra: ['R060590'],
    },

    color: {
      primary_color:          'Green (daylight) / Red (incandescent) — the defining colour-change gem',
      color_variants:         ['Emerald green (daylight)', 'Blue-green (daylight)', 'Red (incandescent)', 'Purple-red (incandescent)', 'Grey-green (weak change)'],
      dominant_wavelength_nm: 555,
      oklch:   { l: 0.45, c: 0.18, h: 155 },
      hex:     '#2a7a4a',
      munsell: '5G 4/8',
      color_temperature_k:    null,
      psychological_effects:  [
        'The colour change is the metaphysical signature — the same stone, utterly transformed by light',
        'Invites perspective shifts, dual awareness, and the ability to hold two realities simultaneously',
        'The green (daylight) anchors in heart and nature; the red (incandescent) ignites passion and will',
        'Exceptionally rare specimens amplify the sense of preciousness and significance',
      ],
      harmonics: {
        complementary_hue: 335,
        triadic_hues:      [275, 35],
        analogous_range:   [135, 175],
      },
    },

    metaphysical: {
      mineral_name:     'Alexandrite',
      chakra_primary:   'Heart',
      chakra_secondary: ['Crown', 'Solar Plexus'],
      element:   ['Earth', 'Fire'],
      planet:    ['Mercury', 'Mars'],
      archetype: ['The Shape-Shifter', 'The Bridge Between Worlds'],
      zodiac:    ['Gemini', 'Scorpio', 'Sagittarius'],
      numerology: 5,
      angel_number: 555,
      intention: 'I hold both realities in balance. I am the same self in every light.',
      traditions: [
        'Russian Imperial tradition — discovered in the Ural Mountains 1834',
        'Named for Tsar Alexander II — its red and green mirror the Russian Imperial colours',
        'Western crystal healing — the rarest of the transformation stones',
        'Vedic astrology — substitute for ruby and emerald simultaneously',
      ],
      properties: [
        'One of the rarest gemstones on Earth — fine alexandrite exceeds diamond in per-carat value',
        'Discovered on the future Tsar Alexander II\'s birthday, 1834, in the Ural Mountains',
        'The colour change (green by day, red by night) made it Russia\'s national stone — Imperial colours',
        'The supreme stone of transformation and duality — embodies the capacity to be both things at once',
        'Used in work around identity, paradox, and integrating opposing aspects of self',
        'Supports those at major life crossroads — its energy is one of graceful, complete metamorphosis',
        'Chrysoberyl hardness of 8.5 — one of the hardest gemstones, mirrors its capacity to hold transformation without shattering',
      ],
      gaia_resonance: 'QuantumNexus + ViriditasHeart + SovereignCore',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 5. ALMANDINE
  // Iron aluminium garnet — the deep blood-red — the original garnet
  // One of the six main garnet species — Fe₃Al₂(SiO₄)₃
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Almandine',
    mindat_id:   178,
    rruff_ids:   ['R040029', 'R050028'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Aquamarine',

    physical: {
      id:           178,
      longid:       'almandine',
      guid:         '',
      name:         'Almandine',
      ima_formula:  'Fe₃Al₂(SiO₄)₃',
      mindat_formula: 'Fe3Al2(SiO4)3',
      ima_status:   'A',
      ima_year:     1803,
      strunzten:    '9.AD.25',
      dana8ed:      '51.4.3a.3',
      crystal_system: 'Isometric',
      hardness_min: 7,
      hardness_max: 7.5,
      specific_gravity_min: 3.95,
      specific_gravity_max: 4.30,
      cleavage:    'None; parting on {110}',
      fracture:    'Subconchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Resinous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Deep red, red-violet, brownish red',
      streak:      'White',
      fluorescence: null,
      ri_min:      1.775,
      ri_max:      1.830,
      birefringence: null,
      optical_type: 'I',
      shortdesc:   'Iron aluminium garnet — the most common red garnet species. Deep blood-red to violet-red. Found worldwide in metamorphic rocks. The original garnet of antiquity.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-178.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Almandine',
      refractive_index: { n: 1.790 },
      birefringence:   null,
      optical_sign:    null,
      dispersion:      'Strong 0.024',
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 620, max: 700 },
      spectra: ['R040029', 'R050028'],
    },

    color: {
      primary_color:          'Deep blood-red to red-violet',
      color_variants:         ['Deep blood red', 'Brownish red', 'Red-violet', 'Dark wine red'],
      dominant_wavelength_nm: 660,
      oklch:   { l: 0.32, c: 0.18, h: 28 },
      hex:     '#8a1c2a',
      munsell: '5R 2/8',
      color_temperature_k:    1900,
      psychological_effects:  [
        'Deep blood-red is among the most viscerally activating colours in the spectrum',
        'Encourages courage, will, passion, and the embodied vitality of being fully alive',
        'Grounding in an earthy, blood-warm way — anchors to the physical body specifically',
        'Historically associated with protection in battle — the warrior\'s stone',
      ],
      harmonics: {
        complementary_hue: 208,
        triadic_hues:      [148, 268],
        analogous_range:   [8, 48],
      },
    },

    metaphysical: {
      mineral_name:     'Almandine',
      chakra_primary:   'Root',
      chakra_secondary: ['Sacral', 'Heart'],
      element:   ['Fire', 'Earth'],
      planet:    ['Mars', 'Saturn'],
      archetype: ['The Blood Guardian', 'The Warrior\'s Heart'],
      zodiac:    ['Aries', 'Scorpio', 'Virgo'],
      numerology: 4,
      angel_number: 444,
      intention: 'I am fully alive. I am rooted in the fire of my own blood.',
      traditions: [
        'Ancient Egyptian funerary jewellery — found in pharaonic tombs',
        'Roman military tradition — garnet carried for protection in battle',
        'Medieval European tradition — the "carbuncle" gem of heraldry',
        'Vedic astrology — hessonite garnet as substitute (same family)',
        'Western crystal healing — the classic root chakra garnet',
      ],
      properties: [
        'The most common garnet species — found worldwide in metamorphic schists and gneisses',
        'The original "garnet" of antiquity — the blood-red gem in Egyptian, Roman, and Medieval jewellery',
        'Named after Alabanda, a region in Turkey, where fine garnets were traded in antiquity',
        'Deeply grounding and energising — activates the root chakra with fire rather than earth',
        'Used in protection grids, especially around the physical body and home',
        'Supports those recovering from illness, trauma, or extreme energy depletion',
        'The isometric crystal system (cubic symmetry) gives almandine its perfectly rounded dodecahedral habit — a sphere in stone form',
      ],
      gaia_resonance: 'AnchorPrism + SovereignCore',
      safety_warning: null,
    },
  },

];

export default BATCH_A2;
