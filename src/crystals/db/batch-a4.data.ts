/**
 * src/crystals/db/batch-a4.data.ts
 * GAIA-OS Crystal Database — Batch A-4
 *
 * Entries:
 *   1. Albite
 *   2. Alexandrite
 *   3. Amazonite
 *   4. Amber
 *   5. Amethyst
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-29
 *
 * NOTE: This batch carries enormous range — from a common feldspar
 * to the world's most famous colour-change gem, to the iconic purple
 * quartz that has defined crystal healing for a generation.
 * Amethyst alone could anchor a database. Here it closes the batch
 * as the rightful heir to the purple frequency.
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_A4: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. ALBITE
  // Sodium feldspar — white to pale grey — the clarity stone
  // End member of the plagioclase feldspar series
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Albite',
    mindat_id:   101,
    rruff_ids:   ['R040068', 'R050068'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Obsidian',

    physical: {
      id:           101,
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
      cleavage:    'Perfect on {001}, good on {010}',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Pearly'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'White, pale grey, pale blue-grey, colourless',
      streak:      'White',
      fluorescence: 'Weak orange or green under UV in some specimens',
      ri_min:      1.527,
      ri_max:      1.538,
      birefringence: 0.011,
      optical_type: 'B',
      shortdesc:   'Sodium end-member of the plagioclase feldspar series. One of the most abundant minerals in the Earth\'s crust. The foundation stone — clear, common, and structurally essential.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-101.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Albite',
      refractive_index: { n_alpha: 1.527, n_beta: 1.532, n_gamma: 1.538 },
      birefringence:   0.011,
      optical_sign:    '+',
      dispersion:      'Weak 0.012',
      pleochroism:     null,
      fluorescence_lw: 'Weak orange or green (variable)',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R040068', 'R050068'],
    },

    color: {
      primary_color:          'White to pale grey',
      color_variants:         ['Pure white', 'Pale grey', 'Colourless', 'Pale blue-grey', 'Pale green-grey'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.88, c: 0.01, h: 240 },
      hex:     '#e8e8ec',
      munsell: 'N8.5/',
      color_temperature_k:    null,
      psychological_effects:  [
        'The neutral ground of clarity — white without dazzle',
        'Structurally supportive — creates a clean field without imposing a frequency',
        'Encourages mental clarity, clean perception, and unbiased thinking',
        'The stone of the blank page — potential without imprint',
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
      chakra_secondary: ['Third Eye', 'Throat'],
      element:   ['Air', 'Aether'],
      planet:    ['Moon', 'Mercury'],
      archetype: ['The Clear Mind', 'The Foundation Stone'],
      zodiac:    ['Aquarius', 'Gemini'],
      numerology: 1,
      angel_number: 111,
      intention: 'My mind is clear, my perception is clean, my field is my own.',
      traditions: ['Western crystal healing', 'Vedic tradition — associated with lunar energy'],
      properties: [
        'One of the most abundant minerals in the Earth\'s crust — common does not mean unimportant',
        'Supports mental clarity, clear thinking, and unbiased perception',
        'The sodium-rich white feldspar that forms moonstone when it shows adularescence',
        'A structural stone — used for creating a clean energetic foundation',
        'Helps those in mental or emotional fog to find clarity and forward direction',
        'The blank page — excellent for intention-setting work as a neutral amplifier',
      ],
      gaia_resonance: 'ClarusLens + Noosphere',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 2. ALEXANDRITE
  // Chromium-bearing chrysoberyl — the colour-change miracle
  // Green in daylight, red in incandescent — nature's most dramatic shift
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Alexandrite',
    mindat_id:   null,
    rruff_ids:   ['R050041'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Ruby',

    physical: {
      id:           0,
      longid:       'alexandrite',
      guid:         '',
      name:         'Chrysoberyl (Alexandrite variety)',
      ima_formula:  'BeAl₂O₄',
      mindat_formula: 'BeAl2O4',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '4.BA.05',
      dana8ed:      '7.2.10.1',
      crystal_system: 'Orthorhombic',
      hardness_min: 8.5,
      hardness_max: 8.5,
      specific_gravity_min: 3.70,
      specific_gravity_max: 3.78,
      cleavage:    'Distinct on {011}, poor on {110} and {010}',
      fracture:    'Conchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Green in daylight/fluorescent; red to purple-red in incandescent light',
      streak:      'White',
      fluorescence: 'Strong red under UV',
      ri_min:      1.746,
      ri_max:      1.763,
      birefringence: 0.011,
      optical_type: 'B',
      shortdesc:   'Rare chromium-bearing chrysoberyl variety showing dramatic colour change from green (daylight) to red (incandescent). One of the most prized gemstones in the world.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-1015.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Alexandrite',
      refractive_index: { n_alpha: 1.746, n_beta: 1.748, n_gamma: 1.763 },
      birefringence:   0.011,
      optical_sign:    '+',
      dispersion:      '0.015',
      pleochroism:     'Strong trichroic: green / orange / purple-red',
      fluorescence_lw: 'Strong red',
      fluorescence_sw: 'Weak red',
      phosphorescence: null,
      visible_wavelength_nm: { min: 400, max: 700 },
      spectra: ['R050041'],
    },

    color: {
      primary_color:          'Green (daylight) / Red (incandescent)',
      color_variants:         ['Emerald green', 'Teal green', 'Purple-red', 'Raspberry red', 'Alexandrite teal-to-crimson'],
      dominant_wavelength_nm: 535,
      oklch:   { l: 0.48, c: 0.20, h: 148 },
      hex:     '#2e7a3a',
      munsell: '5G 4/8',
      color_temperature_k:    null,
      psychological_effects:  [
        'The most visually paradoxical stone — two completely different colours in one gem',
        'Embodies the capacity to hold two truths simultaneously without contradiction',
        'Green: heart, growth, nature. Red: passion, courage, life-force.',
        'Teaches that what appears to change is still fundamentally the same stone',
        'Profound for those navigating duality, identity transitions, or apparent contradictions',
      ],
      harmonics: {
        complementary_hue: 328,
        triadic_hues:      [268, 28],
        analogous_range:   [128, 168],
      },
    },

    metaphysical: {
      mineral_name:     'Alexandrite',
      chakra_primary:   'Heart',
      chakra_secondary: ['Crown', 'Root'],
      element:   ['Earth', 'Fire'],
      planet:    ['Mercury', 'Mars'],
      archetype: ['The Shape-Shifter', 'The Paradox Bearer', 'The Dual-Nature Master'],
      zodiac:    ['Gemini', 'Scorpio'],
      numerology: 5,
      angel_number: 555,
      intention: 'I hold both truths. I change and remain myself.',
      traditions: [
        'First discovered 1830 in Ural Mountains, Russia — named for Tsar Alexander II',
        'Western crystal healing',
        'Vedic gemology — associated with Mercury',
      ],
      properties: [
        'The rarest and most prized colour-change gemstone in the world',
        'Named for Tsar Alexander II of Russia — discovered on his birthday in the Urals, 1830',
        'The colour change from green to red mirrors the Russian imperial colours — hence its prestige',
        'Metaphysically embodies the capacity to hold paradox — duality without contradiction',
        'Supports major life transitions, identity shifts, and integration of opposite qualities',
        'Strengthens intuition, adaptability, and the ability to see multiple perspectives',
        'Angel number 555 — change, transformation, evolution — perfectly aligned with its optical nature',
      ],
      gaia_resonance: 'QuantumNexus + ViriditasHeart + SovereignCore',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 3. AMAZONITE
  // Potassium feldspar (microcline) — blue-green — the truth-speaker
  // Named for the Amazon River despite no deposits there
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Amazonite',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Carnelian',

    physical: {
      id:           0,
      longid:       'amazonite',
      guid:         '',
      name:         'Microcline (Amazonite variety)',
      ima_formula:  'KAlSi₃O₈',
      mindat_formula: 'KAlSi3O8',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '9.FA.30',
      dana8ed:      '76.1.1.1',
      crystal_system: 'Triclinic',
      hardness_min: 6,
      hardness_max: 6.5,
      specific_gravity_min: 2.56,
      specific_gravity_max: 2.58,
      cleavage:    'Perfect on {001}, good on {010}',
      fracture:    'Uneven to conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Opaque', 'Translucent'],
      colour:      'Blue-green, turquoise, green — from Pb²⁺ and water in the crystal structure',
      streak:      'White',
      fluorescence: null,
      ri_min:      1.514,
      ri_max:      1.530,
      birefringence: 0.008,
      optical_type: 'B',
      shortdesc:   'Blue-green to turquoise variety of microcline (potassium feldspar). Colour caused by lead and water impurities. Used as an ornamental stone since ancient Egypt.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-2621.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Amazonite',
      refractive_index: { n_alpha: 1.514, n_beta: 1.522, n_gamma: 1.530 },
      birefringence:   0.008,
      optical_sign:    '-',
      dispersion:      'Weak',
      pleochroism:     'Weak',
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 480, max: 530 },
      spectra: [],
    },

    color: {
      primary_color:          'Blue-green to turquoise',
      color_variants:         ['Pale mint green', 'Aqua blue-green', 'Deep turquoise', 'Grey-green', 'Teal with white veining'],
      dominant_wavelength_nm: 505,
      oklch:   { l: 0.67, c: 0.14, h: 185 },
      hex:     '#5bbdb0',
      munsell: '5BG 6/6',
      color_temperature_k:    9000,
      psychological_effects:  [
        'The colour of still tropical water — immediately calming and spacious',
        'Opens the throat without force — encourages honest self-expression',
        'Balances the emotional body while supporting clear verbal communication',
        'The blue-green frequency sits precisely at the heart-throat bridge',
      ],
      harmonics: {
        complementary_hue: 5,
        triadic_hues:      [305, 65],
        analogous_range:   [165, 205],
      },
    },

    metaphysical: {
      mineral_name:     'Amazonite',
      chakra_primary:   'Throat',
      chakra_secondary: ['Heart'],
      element:   ['Water', 'Earth'],
      planet:    ['Uranus', 'Venus'],
      archetype: ['The Truth-Teller', 'The Warrior Poet'],
      zodiac:    ['Virgo', 'Aquarius'],
      numerology: 5,
      angel_number: 555,
      intention: 'I speak my truth with confidence, clarity, and compassion.',
      traditions: [
        'Ancient Egyptian amulet tradition — found in Tutankhamun\'s tomb',
        'Pre-Columbian Mesoamerican use',
        'Western crystal healing',
      ],
      properties: [
        'One of the oldest ornamental stones — found in Tutankhamun\'s tomb as amulets and jewelry',
        'Named for the Amazon River though no deposits are found there — named for its colour',
        'The premiere throat chakra stone — supports honest, compassionate self-expression',
        'Particularly useful for those who suppress their truth out of fear of conflict',
        'The "hope" stone — encourages optimism, courage, and forward trust',
        'Balances masculine and feminine energies within the field',
        'Supports artists, writers, speakers, and anyone whose work requires authentic voice',
      ],
      gaia_resonance: 'SovereignCore + ViriditasHeart',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 4. AMBER
  // Fossilised tree resin — ancient light made solid
  // Not a mineral — an organic gem — the oldest light-bearer
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Amber',
    mindat_id:   1802,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Amethyst',

    physical: {
      id:           1802,
      longid:       'amber',
      guid:         '',
      name:         'Amber',
      ima_formula:  'C₁₀H₁₆O + S (complex organic polymer)',
      mindat_formula: 'C10H16O',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '10.CA.05',
      dana8ed:      null,
      crystal_system: 'Amorphous',
      hardness_min: 2,
      hardness_max: 2.5,
      specific_gravity_min: 1.05,
      specific_gravity_max: 1.10,
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Resinous'],
      diaphaneity: ['Transparent', 'Translucent', 'Opaque'],
      colour:      'Golden yellow, honey, orange, cognac, red, green, blue (rare)',
      streak:      'White',
      fluorescence: 'Strong blue-white to yellow-green under UV',
      ri_min:      1.539,
      ri_max:      1.545,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Fossilised tree resin 30–90 million years old. An organic gem, not a mineral. Often contains perfectly preserved insect and plant inclusions. The oldest light in the crystal healing tradition.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-1802.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Amber',
      refractive_index: { n: 1.540 },
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: 'Strong blue-white to yellow-green',
      fluorescence_sw: 'Strong blue-white',
      phosphorescence: null,
      visible_wavelength_nm: { min: 560, max: 620 },
      spectra: [],
    },

    color: {
      primary_color:          'Golden honey amber',
      color_variants:         ['Pale lemon yellow', 'Honey gold', 'Deep cognac orange', 'Cherry red', 'Green (rare)', 'Blue (rare, Dominican)'],
      dominant_wavelength_nm: 590,
      oklch:   { l: 0.72, c: 0.18, h: 72 },
      hex:     '#e8a020',
      munsell: '10YR 7/8',
      color_temperature_k:    3200,
      psychological_effects:  [
        'Warm golden light — the frequency of ancient solar energy stored for millions of years',
        'Deeply comforting, nurturing, and life-affirming',
        'Triggers primal warmth responses — the oldest light our nervous system recognises',
        'Encourages joy, vitality, and trust in life\'s processes',
        'The honey-gold hue sits at the perfect balance of warm yellow and warm orange',
      ],
      harmonics: {
        complementary_hue: 252,
        triadic_hues:      [192, 312],
        analogous_range:   [52, 92],
      },
    },

    metaphysical: {
      mineral_name:     'Amber',
      chakra_primary:   'Solar Plexus',
      chakra_secondary: ['Sacral', 'Root'],
      element:   ['Fire', 'Earth', 'Akasha'],
      planet:    ['Sun'],
      archetype: ['The Ancient Light-Bearer', 'The Time Keeper', 'The Healer'],
      zodiac:    ['Leo', 'Aquarius', 'Aries'],
      numerology: 3,
      angel_number: 333,
      intention: 'I carry the light of millions of years. I am ancient, warm, and alive.',
      traditions: [
        'Baltic and Scandinavian tradition — "the gold of the north"',
        'Ancient Greek tradition — called "electron" (source of the word electricity)',
        'Native American shamanic tradition',
        'Chinese medicine — hun po (soul) stone',
        'Western crystal healing',
      ],
      properties: [
        'Not a mineral — fossilised tree resin 30–90 million years old — the oldest "crystal" in the tradition',
        'Named "electron" by the ancient Greeks — rubbing amber generates static electricity',
        'Often contains perfectly preserved organisms — insects, plants, feathers — windows into deep time',
        'Carries the living energy of ancient forests and solar light stored across geological epochs',
        'The premier solar plexus stone — activates personal power, joy, and life-force',
        'Used across every major ancient civilisation as an amulet and healing tool',
        'The yin-yang pair with Amethyst is the golden-purple axis: solar fire ↔ lunar wisdom',
      ],
      gaia_resonance: 'SovereignCore + ViriditasHeart + SomnusVeil',
      safety_warning: 'Not a mineral — can be scratched, dissolved by alcohol/acetone, and melted by heat. Do not expose to harsh chemicals. Do not use as water elixir without verification of authenticity (synthetic copal is common).',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 5. AMETHYST
  // Purple quartz — the master healer — the most iconic crystal in the tradition
  // Iron + irradiation = the purple that changed the world
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Amethyst',
    mindat_id:   null,
    rruff_ids:   ['R040031', 'R050031'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Amber',

    physical: {
      id:           0,
      longid:       'amethyst',
      guid:         '',
      name:         'Quartz (Amethyst variety)',
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
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Purple — pale lavender to deep royal violet — from Fe⁴⁺ ions and natural irradiation',
      streak:      'White',
      fluorescence: 'Weak to none under UV; some specimens show weak blue-white',
      ri_min:      1.544,
      ri_max:      1.553,
      birefringence: 0.009,
      optical_type: 'U',
      shortdesc:   'Purple variety of quartz coloured by iron impurities and natural irradiation. The world\'s most widely recognised and used healing crystal. Found on every continent.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-28376.html',
      piezoelectric:    true,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name: 'Amethyst',
      refractive_index: { n_omega: 1.553, n_epsilon: 1.544 },
      birefringence:   0.009,
      optical_sign:    '-',
      dispersion:      '0.013',
      pleochroism:     'Weak: pale purple / deeper purple',
      fluorescence_lw: 'Weak blue-white (variable)',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 380, max: 450 },
      spectra: ['R040031', 'R050031'],
    },

    color: {
      primary_color:          'Purple — violet to lavender',
      color_variants:         ['Pale lavender', 'Lilac', 'Mid purple', 'Deep royal violet', 'Red-purple', 'Blue-violet ("Siberian" amethyst)'],
      dominant_wavelength_nm: 415,
      oklch:   { l: 0.52, c: 0.18, h: 305 },
      hex:     '#7c4fa0',
      munsell: '7.5P 4/8',
      color_temperature_k:    null,
      psychological_effects:  [
        'The purple frequency activates both the third eye and crown chakras simultaneously',
        'Calms the overactive mind while opening spiritual perception',
        'Deeply relaxing at the nervous system level — measurable reduction in stress response',
        'Encourages contemplative, meditative states without effort',
        'The most trusted purple in existence — millennia of use have embedded this frequency in collective consciousness',
        'The red-blue balance: earth (red base) + sky (blue/violet) = the bridge between worlds',
      ],
      harmonics: {
        complementary_hue: 125,
        triadic_hues:      [65, 185],
        analogous_range:   [285, 325],
      },
    },

    metaphysical: {
      mineral_name:     'Amethyst',
      chakra_primary:   'Crown',
      chakra_secondary: ['Third Eye'],
      element:   ['Air', 'Water', 'Aether'],
      planet:    ['Jupiter', 'Neptune', 'Saturn'],
      archetype: ['The High Priest/ess', 'The Master Healer', 'The Meditator'],
      zodiac:    ['Pisces', 'Aquarius', 'Capricorn', 'Virgo'],
      numerology: 3,
      angel_number: 333,
      intention: 'I am calm. I am clear. I am open to the highest guidance.',
      traditions: [
        'Ancient Greek and Roman tradition — "amethystos" (not intoxicated)',
        'Medieval Christian tradition — bishops\' stone',
        'Ancient Egyptian tradition — used in funerary jewelry',
        'Buddhist meditation tradition',
        'Western crystal healing — the universal "first" stone',
        'Vedic gemology — associated with Jupiter',
      ],
      properties: [
        'The world\'s most widely used and recognised healing crystal — the gateway stone for most practitioners',
        'Ancient Greek name "amethystos" — believed to prevent intoxication (worn while drinking wine)',
        'Used by Egyptian pharaohs, Roman soldiers, medieval bishops, and Buddhist monks',
        'The master stress-relief stone — calms the mind and nervous system without sedation',
        'Opens the crown and third eye simultaneously — the premier meditation stone',
        'Supports sobriety, clarity of mind, and freedom from addictive patterns',
        'The purple ray embodies the bridge between earth and cosmos — grounded spirituality',
        'Piezoelectric — generates a measurable charge under pressure — a literal energy transducer',
      ],
      gaia_resonance: 'Noosphere + ClarusLens + SomnusVeil',
      safety_warning: 'Colour fades in prolonged direct sunlight — store away from UV. Piezoelectric — keep away from sensitive electronics.',
    },
  },

];

export default BATCH_A4;
