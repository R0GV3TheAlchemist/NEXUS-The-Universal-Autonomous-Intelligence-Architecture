/**
 * src/crystals/db/batch-a5.data.ts
 * GAIA-OS Crystal Database — Batch A-5
 *
 * Entries:
 *   1. Ametrine
 *   2. Ammonite
 *   3. Andalusite
 *   4. Angelite
 *   5. Apache Tears
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-29
 *
 * NOTE: This batch contains one of the most unusual unions in mineralogy
 * (Ametrine — amethyst and citrine in a single crystal), one of the
 * most ancient organic gems (Ammonite — the spiral of 400 million years),
 * and one of the most emotionally tender stones in the entire tradition
 * (Apache Tears — obsidian born from grief).
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_A5: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. AMETRINE
  // Natural bicolour quartz — amethyst purple + citrine gold in one crystal
  // Almost exclusively from the Anahi Mine, Bolivia
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Ametrine',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Labradorite',

    physical: {
      id:           0,
      longid:       'ametrine',
      guid:         '',
      name:         'Quartz (Ametrine variety — bicolour amethyst/citrine)',
      ima_formula:  'SiO₂',
      mindat_formula: 'SiO2',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '4.DA.05',
      dana8ed:      '75.1.3.1',
      crystal_system: 'Trigonal',
      hardness_min: 7,
      hardness_max: 7,
      specific_gravity_min: 2.63,
      specific_gravity_max: 2.65,
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Transparent'],
      colour:      'Bicolour — purple (amethyst zone) and golden yellow (citrine zone) in a single crystal',
      streak:      'White',
      fluorescence: 'Weak to none',
      ri_min:      1.544,
      ri_max:      1.553,
      birefringence: 0.009,
      optical_type: 'U',
      shortdesc:   'Natural bicolour quartz displaying both amethyst (purple) and citrine (yellow-gold) zones within a single crystal. Almost exclusively sourced from the Anahi Mine in Bolivia. The stone of integration.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-201.html',
      piezoelectric:    true,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name: 'Ametrine',
      refractive_index: { n_omega: 1.553, n_epsilon: 1.544 },
      birefringence:   0.009,
      optical_sign:    '-',
      dispersion:      '0.013',
      pleochroism:     'Weak within each colour zone',
      fluorescence_lw: 'Weak (variable)',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 380, max: 580 },
      spectra: [],
    },

    color: {
      primary_color:          'Bicolour — purple and golden yellow',
      color_variants:         ['50/50 purple-gold', 'Predominantly amethyst with citrine edge', 'Predominantly citrine with amethyst edge', 'Soft lavender-gold gradient'],
      dominant_wavelength_nm: 480,
      oklch:   { l: 0.60, c: 0.16, h: 320 },
      hex:     '#8a5faa',
      munsell: '5P 5/8',
      color_temperature_k:    null,
      psychological_effects:  [
        'The visual integration of two frequencies — crown wisdom and solar power in one glance',
        'Encourages the mind to hold spiritual insight and practical action simultaneously',
        'Reduces the false split between inner work and outer achievement',
        'The purple-gold axis is alchemically the completion arc — nigredo to rubedo',
      ],
      harmonics: {
        complementary_hue: 140,
        triadic_hues:      [80, 200],
        analogous_range:   [300, 340],
      },
    },

    metaphysical: {
      mineral_name:     'Ametrine',
      chakra_primary:   'Crown',
      chakra_secondary: ['Solar Plexus', 'Third Eye'],
      element:   ['Air', 'Fire'],
      planet:    ['Jupiter', 'Sun'],
      archetype: ['The Alchemist', 'The Integrated Being', 'The Bridge Builder'],
      zodiac:    ['Libra', 'Aquarius', 'Gemini'],
      numerology: 4,
      angel_number: 444,
      intention: 'I unite my spiritual knowing with my earthly power. I am whole.',
      traditions: [
        'Bolivian indigenous tradition — Anahi Mine legend involving a princess',
        'Western crystal healing — integration and balance work',
      ],
      properties: [
        'One of the rarest natural bicolour gems — two distinct colour zones in a single quartz crystal',
        'Almost exclusively from the Anahi Mine in the Bolivian Amazon',
        'The integration stone par excellence — unites crown (amethyst) and solar plexus (citrine) in one body',
        'Supports those who feel torn between spiritual calling and material responsibility',
        'The alchemical stone — embodies the completion of the Great Work: spirit and matter unified',
        'Accelerates manifestation work by keeping spiritual intention and practical will aligned',
        'Piezoelectric — both zones carry the quartz transducer property',
      ],
      gaia_resonance: 'Noosphere + SovereignCore + QuantumNexus',
      safety_warning: 'Colour may fade in prolonged direct sunlight. Piezoelectric — keep away from sensitive electronics.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 2. AMMONITE
  // Fossilised cephalopod shell — 400 million years of spiral wisdom
  // Organic gem — not a mineral — the original sacred spiral
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Ammonite',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Moldavite',

    physical: {
      id:           0,
      longid:       'ammonite',
      guid:         '',
      name:         'Ammonite (fossilised cephalopod)',
      ima_formula:  'CaCO₃ (aragonite/calcite) + organic matrix',
      mindat_formula: 'CaCO3',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    null,
      dana8ed:      null,
      crystal_system: 'Amorphous (organic)',
      hardness_min: 3.5,
      hardness_max: 4,
      specific_gravity_min: 2.60,
      specific_gravity_max: 2.85,
      cleavage:    'None as fossil',
      fracture:    'Uneven',
      tenacity:    'Brittle',
      luster:      ['Resinous', 'Pearly', 'Iridescent (ammolite specimens)'],
      diaphaneity: ['Opaque', 'Translucent (ammolite)'],
      colour:      'Grey, brown, black; iridescent rainbow (ammolite variety from Alberta)',
      streak:      'White',
      fluorescence: null,
      ri_min:      1.530,
      ri_max:      1.685,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Fossilised shell of an extinct cephalopod, extinct 66 million years ago. Existed for over 300 million years. The original sacred spiral. Some specimens show brilliant iridescence (ammolite).',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-29240.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Ammonite',
      refractive_index: { n: 1.600 },
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: [],
    },

    color: {
      primary_color:          'Brown to grey-black; iridescent rainbow (ammolite)',
      color_variants:         ['Natural grey-brown fossil', 'Polished black', 'Ammolite — full-spectrum iridescence', 'Pyritised (golden) ammonite'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.35, c: 0.04, h: 50 },
      hex:     '#5a4a38',
      munsell: '5YR 3/2',
      color_temperature_k:    null,
      psychological_effects:  [
        'The spiral form is the most primally recognised natural pattern in human cognition',
        'Induces a deep sense of time, continuity, and perspective',
        'Grounding through deep time — the antidote to modern presentism',
        'Ammolite iridescence activates wonder, awe, and multidimensional perception',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   null,
      },
    },

    metaphysical: {
      mineral_name:     'Ammonite',
      chakra_primary:   'Root',
      chakra_secondary: ['Third Eye', 'Crown'],
      element:   ['Earth', 'Water', 'Akasha'],
      planet:    ['Saturn', 'Pluto'],
      archetype: ['The Ancient One', 'The Spiral Path', 'The Deep Time Keeper'],
      zodiac:    ['Cancer', 'Capricorn', 'Aquarius'],
      numerology: 9,
      angel_number: 999,
      intention: 'I am held by deep time. I spiral forward. Everything completes.',
      traditions: [
        'Hindu tradition — Shaligrama Shila — sacred to Vishnu',
        'Native American tradition — Buffalo Stone (Iniskim)',
        'Medieval European — Serpent stones — believed to be coiled serpents',
        'Western crystal healing',
      ],
      properties: [
        'Not a mineral — fossilised shell of a cephalopod extinct 66 million years ago',
        'Ammonites existed for over 300 million years — the most successful complex animal in Earth history',
        'The spiral form embodies the Fibonacci sequence — the mathematics of growth and unfoldment',
        'Sacred in Hindu tradition as Shaligrama Shila — direct manifestation of Vishnu',
        'Carries the energy of deep time — profoundly grounding and perspective-expanding',
        'Ammolite variety (Alberta, Canada) shows brilliant spectral iridescence — one of the rarest organic gems',
        'Angel number 999 — completion, endings that become beginnings — perfectly mirroring its extinction and preservation',
      ],
      gaia_resonance: 'ViriditasHeart + SomnusVeil + Noosphere',
      safety_warning: 'Water-sensitive — prolonged immersion can damage the fossil matrix. Do not use as water elixir.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 3. ANDALUSITE
  // Aluminium nesosilicate — the cross-stone — chiastolite variety
  // One of the most dramatic natural cross formations in mineralogy
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Andalusite',
    mindat_id:   231,
    rruff_ids:   ['R040002'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Selenite',

    physical: {
      id:           231,
      longid:       'andalusite',
      guid:         '',
      name:         'Andalusite',
      ima_formula:  'Al₂SiO₅',
      mindat_formula: 'Al2SiO5',
      ima_status:   'A',
      ima_year:     1798,
      strunzten:    '9.AF.10',
      dana8ed:      '52.3.1.1',
      crystal_system: 'Orthorhombic',
      hardness_min: 6.5,
      hardness_max: 7.5,
      specific_gravity_min: 3.13,
      specific_gravity_max: 3.21,
      cleavage:    'Good on {110}, poor on {100}',
      fracture:    'Uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Dull'],
      diaphaneity: ['Transparent', 'Translucent', 'Opaque'],
      colour:      'Pink, red, brown, green, grey; Chiastolite variety shows black carbon cross inclusion',
      streak:      'White',
      fluorescence: null,
      ri_min:      1.629,
      ri_max:      1.650,
      birefringence: 0.010,
      optical_type: 'B',
      shortdesc:   'Aluminium silicate polymorph (with kyanite and sillimanite). Chiastolite variety shows a natural black carbon cross in cross-section — one of the most dramatic natural formations in mineralogy.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-231.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Andalusite',
      refractive_index: { n_alpha: 1.629, n_beta: 1.633, n_gamma: 1.650 },
      birefringence:   0.010,
      optical_sign:    '-',
      dispersion:      'Weak',
      pleochroism:     'Strong trichroic in gem varieties: green / yellow / red',
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 560, max: 700 },
      spectra: ['R040002'],
    },

    color: {
      primary_color:          'Pink to reddish-brown; Chiastolite: grey with black cross',
      color_variants:         ['Pale pink', 'Rose red', 'Olive green (gem variety)', 'Brown', 'Chiastolite grey with black cross'],
      dominant_wavelength_nm: 620,
      oklch:   { l: 0.55, c: 0.12, h: 28 },
      hex:     '#b06060',
      munsell: '5R 5/6',
      color_temperature_k:    null,
      psychological_effects:  [
        'The chiastolite cross is one of the most psychologically potent natural symbols on Earth',
        'Activates the four-directions awareness — above, below, before, behind',
        'Grounding through symmetry and centre — the cross marks the intersection point',
        'Encourages those feeling scattered across multiple paths to find their centre point',
      ],
      harmonics: {
        complementary_hue: 208,
        triadic_hues:      [148, 268],
        analogous_range:   [8, 48],
      },
    },

    metaphysical: {
      mineral_name:     'Andalusite',
      chakra_primary:   'Root',
      chakra_secondary: ['Heart', 'Solar Plexus'],
      element:   ['Earth', 'Fire'],
      planet:    ['Saturn', 'Mars'],
      archetype: ['The Cross Bearer', 'The Four-Direction Keeper', 'The Centred One'],
      zodiac:    ['Virgo', 'Scorpio', 'Capricorn'],
      numerology: 4,
      angel_number: 444,
      intention: 'I stand at the centre. All directions are open. I am grounded and whole.',
      traditions: [
        'Medieval Christian tradition — chiastolite worn as a natural cross amulet',
        'Native American tradition — four-directions medicine',
        'Western crystal healing',
      ],
      properties: [
        'IMA-recognised species since 1798 — named for Andalusia, Spain where it was first described',
        'Polymorph of Al₂SiO₅ — shares formula with kyanite and sillimanite but different crystal structure',
        'Chiastolite variety: carbon inclusions arrange naturally into a perfect cross in cross-section',
        'One of the most geologically fascinating stones — the cross forms through metamorphic pressure',
        'Medieval pilgrims wore chiastolite crosses to Santiago de Compostela for protection',
        'The premier grounding and centring stone — brings scattered energy back to centre',
        'Supports those facing crossroads decisions — helps locate the true centre between choices',
      ],
      gaia_resonance: 'SovereignCore + ViriditasHeart',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 4. ANGELITE
  // Blue anhydrite — trade name for the pale blue variety
  // Peru — the stone of peaceful, angelic communication
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Angelite',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Obsidian',

    physical: {
      id:           0,
      longid:       'angelite',
      guid:         '',
      name:         'Anhydrite (Angelite variety)',
      ima_formula:  'CaSO₄',
      mindat_formula: 'CaSO4',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '7.AD.30',
      dana8ed:      '28.3.2.1',
      crystal_system: 'Orthorhombic',
      hardness_min: 3,
      hardness_max: 3.5,
      specific_gravity_min: 2.89,
      specific_gravity_max: 2.98,
      cleavage:    'Perfect on {010}, good on {100} and {001}',
      fracture:    'Uneven to splintery',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Pearly'],
      diaphaneity: ['Translucent', 'Opaque'],
      colour:      'Pale blue to blue-grey — from natural anhydrite deposits in Peru',
      streak:      'White',
      fluorescence: 'Weak pink or white under UV (variable)',
      ri_min:      1.570,
      ri_max:      1.614,
      birefringence: 0.044,
      optical_type: 'B',
      shortdesc:   'Pale blue variety of anhydrite (calcium sulphate) marketed as Angelite. Primarily sourced from Peru. Soft and water-sensitive. The premier stone for gentle, high-vibrational communication.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-229.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Angelite',
      refractive_index: { n_alpha: 1.570, n_beta: 1.577, n_gamma: 1.614 },
      birefringence:   0.044,
      optical_sign:    '+',
      dispersion:      'Weak',
      pleochroism:     'Weak',
      fluorescence_lw: 'Weak pink or white (variable)',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 440, max: 490 },
      spectra: [],
    },

    color: {
      primary_color:          'Pale blue to blue-grey',
      color_variants:         ['Soft sky blue', 'Periwinkle blue-grey', 'Pale blue with white patches', 'Blue with brown matrix'],
      dominant_wavelength_nm: 465,
      oklch:   { l: 0.72, c: 0.09, h: 222 },
      hex:     '#92b8d4',
      munsell: '5B 7/4',
      color_temperature_k:    12000,
      psychological_effects:  [
        'Pale cool blue is the most universally calming colour in the human visual system',
        'Sky-blue frequency opens the throat and upper chest — encourages gentle, truthful expression',
        'The softness of the colour mirrors the softness of its energetic quality — never aggressive',
        'Activates the listening capacity as much as the speaking capacity',
      ],
      harmonics: {
        complementary_hue: 42,
        triadic_hues:      [342, 102],
        analogous_range:   [202, 242],
      },
    },

    metaphysical: {
      mineral_name:     'Angelite',
      chakra_primary:   'Throat',
      chakra_secondary: ['Third Eye', 'Crown'],
      element:   ['Air', 'Water'],
      planet:    ['Neptune', 'Moon'],
      archetype: ['The Angel Communicator', 'The Peaceful Channel', 'The Compassionate Voice'],
      zodiac:    ['Aquarius', 'Pisces'],
      numerology: 1,
      angel_number: 111,
      intention: 'I speak with angelic clarity. I am a peaceful channel of divine truth.',
      traditions: [
        'Western crystal healing — modern tradition (post-1980s)',
        'New Age channelling and angelic communication work',
      ],
      properties: [
        'Trade name for pale blue anhydrite (calcium sulphate) — primarily from Perú',
        'The premier stone for angelic communication, mediumship, and channelling work',
        'Carries the energy of compassionate, peaceful higher guidance',
        'Supports communication with guides, angels, and higher-dimensional presences',
        'Useful for healers, counsellors, and teachers — promotes loving, clear communication',
        'Encourages telepathy, astral travel, and expanded spiritual awareness',
        'Transforms pain and disorder into wholeness — the Peruvian blue sky made solid',
      ],
      gaia_resonance: 'Noosphere + SomnusVeil + ClarusLens',
      safety_warning: 'WATER-SENSITIVE — anhydrite reacts with water and can absorb moisture, eventually converting to gypsum. Never use in water elixirs. Keep away from humidity. Do not cleanse with water.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 5. APACHE TEARS
  // Rounded obsidian nodules — volcanic glass — grief transmutation
  // The stone that carries a nation's sorrow — and transforms it
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Apache Tears',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Rose Quartz',

    physical: {
      id:           0,
      longid:       'apache-tears',
      guid:         '',
      name:         'Obsidian (Apache Tears — rounded perlitic nodules)',
      ima_formula:  'SiO₂ + Al₂O₃ + FeO + other oxides (volcanic glass)',
      mindat_formula: 'SiO2',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    null,
      dana8ed:      null,
      crystal_system: 'Amorphous',
      hardness_min: 5,
      hardness_max: 5.5,
      specific_gravity_min: 2.35,
      specific_gravity_max: 2.60,
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Resinous'],
      diaphaneity: ['Translucent (thin edges)', 'Opaque'],
      colour:      'Black to dark brown — translucent dark smoky brown when held to light',
      streak:      'White',
      fluorescence: null,
      ri_min:      1.490,
      ri_max:      1.510,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Rounded nodules of naturally occurring obsidian (volcanic glass), formed by the weathering of perlite. The name honours the Apache people of Arizona. Translucent dark brown when held to light.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-3498.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Apache Tears',
      refractive_index: { n: 1.500 },
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 550, max: 700 },
      spectra: [],
    },

    color: {
      primary_color:          'Black to dark brown; translucent when backlit',
      color_variants:         ['Opaque black', 'Deep brown', 'Smoky translucent brown (backlit)', 'Mottled black-grey'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.18, c: 0.03, h: 35 },
      hex:     '#2d2420',
      munsell: '5YR 2/1',
      color_temperature_k:    null,
      psychological_effects:  [
        'Deep black — absorbs and contains grief rather than deflecting it',
        'The darkness invites the holder to enter the feeling rather than avoid it',
        'Translucency when held to light is the metaphor made visible: light exists within the darkness',
        'The small, rounded, smooth form of Apache Tears is inherently comforting to hold',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   null,
      },
    },

    metaphysical: {
      mineral_name:     'Apache Tears',
      chakra_primary:   'Root',
      chakra_secondary: ['Heart', 'Earth Star'],
      element:   ['Fire', 'Earth'],
      planet:    ['Pluto', 'Saturn'],
      archetype: ['The Grief Carrier', 'The Witness', 'The Transformer of Sorrow'],
      zodiac:    ['Aries', 'Capricorn', 'Scorpio'],
      numerology: 1,
      angel_number: 111,
      intention: 'I honour my grief. I let it move through me. I am transformed by what I have carried.',
      traditions: [
        'Apache oral tradition — Arizona, USA',
        'Native American healing tradition',
        'Western crystal healing — grief and loss work',
      ],
      properties: [
        'Named for the legend of the Apache warriors who rode off a cliff in Arizona rather than surrender to the US Cavalry',
        'The legend holds that the tears wept by the women of the tribe became these rounded black stones',
        'Rounded by natural weathering of perlite — smooth, small, perfectly palm-held',
        'The premier stone for grief work — holds grief without amplifying it',
        'Unlike black tourmaline (deflects) or obsidian (confronts), Apache Tears gently absorbs and transmutes',
        'Translucent when held to light — teaches that light exists within even the deepest darkness',
        'The yin-yang pair with Rose Quartz is profound — grief (Apache Tears) and love (Rose Quartz) are the same river',
      ],
      gaia_resonance: 'SovereignCore + ViriditasHeart',
      safety_warning: 'Sharp edges if broken — Apache Tears are volcanic glass. Handle with care. Cleanse regularly as they absorb grief energy actively.',
    },
  },

];

export default BATCH_A5;
