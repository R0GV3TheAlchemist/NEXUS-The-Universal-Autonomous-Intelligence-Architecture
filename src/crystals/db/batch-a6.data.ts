/**
 * src/crystals/db/batch-a6.data.ts
 * GAIA-OS Crystal Database — Batch A-6
 *
 * Entries:
 *   1. Apatite
 *   2. Apophyllite
 *   3. Aquamarine
 *   4. Aragonite
 *   5. Astrophyllite
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-29
 *
 * NOTE: This batch brings extraordinary range — from the mineral that
 * literally builds human bones (Apatite), to the most transparent
 * third-eye activator in the tradition (Apophyllite), to the stone
 * of the sea that graced Roman emperors (Aquamarine), to the blade-star
 * mineral that looks like something from another dimension (Astrophyllite).
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_A6: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. APATITE
  // Calcium phosphate mineral group — blue, green, yellow, violet
  // The mineral that builds teeth and bones — the body’s own stone
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Apatite',
    mindat_id:   290,
    rruff_ids:   ['R040098', 'R050098'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Garnet',

    physical: {
      id:           290,
      longid:       'apatite',
      guid:         '',
      name:         'Apatite (group)',
      ima_formula:  'Ca₅(PO₄)₃(F,Cl,OH)',
      mindat_formula: 'Ca5(PO4)3(F,Cl,OH)',
      ima_status:   'A',
      ima_year:     1786,
      strunzten:    '8.BN.05',
      dana8ed:      '41.8.1.1',
      crystal_system: 'Hexagonal',
      hardness_min: 5,
      hardness_max: 5,
      specific_gravity_min: 3.16,
      specific_gravity_max: 3.23,
      cleavage:    'Imperfect on {0001} and {10−1‐0}',
      fracture:    'Conchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Resinous'],
      diaphaneity: ['Transparent', 'Translucent', 'Opaque'],
      colour:      'Blue, green, yellow, violet, colourless, pink — wide colour range depending on trace elements',
      streak:      'White',
      fluorescence: 'Variable: yellow, blue, pink, or none under UV depending on variety',
      ri_min:      1.628,
      ri_max:      1.649,
      birefringence: 0.003,
      optical_type: 'U',
      shortdesc:   'Calcium phosphate mineral group — the primary mineral in vertebrate teeth and bones. Hardness 5 is the Mohs reference mineral. Occurs in blue, green, yellow, and violet gem varieties.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-290.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Apatite',
      refractive_index: { n_omega: 1.649, n_epsilon: 1.642 },
      birefringence:   0.003,
      optical_sign:    '-',
      dispersion:      '0.013',
      pleochroism:     'Weak to moderate in coloured varieties',
      fluorescence_lw: 'Variable by variety: yellow, blue, pink, none',
      fluorescence_sw: 'Variable',
      phosphorescence: null,
      visible_wavelength_nm: { min: 400, max: 560 },
      spectra: ['R040098'],
    },

    color: {
      primary_color:          'Blue to blue-green (most common gem variety)',
      color_variants:         ['Neon blue (Paraiba-type)', 'Teal blue-green', 'Apple green', 'Golden yellow', 'Violet', 'Colourless', 'Pink'],
      dominant_wavelength_nm: 490,
      oklch:   { l: 0.58, c: 0.18, h: 210 },
      hex:     '#4ab0c0',
      munsell: '5B 5/8',
      color_temperature_k:    10000,
      psychological_effects:  [
        'The blue-green frequency activates both throat and heart simultaneously',
        'Neon blue varieties carry an electric, activating quality unlike any other mineral',
        'Stimulates creative expression, intellectual clarity, and authentic communication',
        'The yellow variety activates solar plexus motivation and personal confidence',
      ],
      harmonics: {
        complementary_hue: 30,
        triadic_hues:      [330, 90],
        analogous_range:   [190, 230],
      },
    },

    metaphysical: {
      mineral_name:     'Apatite',
      chakra_primary:   'Throat',
      chakra_secondary: ['Third Eye', 'Heart'],
      element:   ['Water', 'Air'],
      planet:    ['Mercury', 'Venus'],
      archetype: ['The Visionary Communicator', 'The Body Wisdom Keeper'],
      zodiac:    ['Gemini', 'Libra'],
      numerology: 9,
      angel_number: 999,
      intention: 'I speak my vision clearly. My body and soul are in alignment.',
      traditions: [
        'Western crystal healing',
        'Named from Greek "apatein" (to deceive) — long confused with other minerals',
      ],
      properties: [
        'The mineral that literally builds human bones and teeth — a primary component of hydroxyapatite in the body',
        'Named from Greek "apatein" (to deceive) — was frequently mistaken for other minerals before classification',
        'The Mohs hardness 5 reference mineral — every hardness scale in geology uses apatite as the H5 benchmark',
        'Neon blue varieties from Madagascar and Brazil rival Paraiba tourmaline in vibrancy',
        'Supports communication, creative expression, and the articulation of inner vision',
        'The blue variety supports the throat chakra; yellow supports solar plexus motivation',
        'Energetically aligned with intellectual pursuits, learning, and the pursuit of truth',
      ],
      gaia_resonance: 'ClarusLens + SovereignCore',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 2. APOPHYLLITE
  // Phyllosilicate — clear to pale green — the akashic mirror
  // The most transparent third-eye activator in the crystal tradition
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Apophyllite',
    mindat_id:   35858,
    rruff_ids:   ['R040054'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Black Tourmaline',

    physical: {
      id:           35858,
      longid:       'apophyllite',
      guid:         '',
      name:         'Apophyllite-(KF)',
      ima_formula:  'KCa₄Si₈O₂₀(F,OH)·8H₂O',
      mindat_formula: 'KCa4Si8O20(F,OH)·8H2O',
      ima_status:   'A',
      ima_year:     1806,
      strunzten:    '9.EA.15',
      dana8ed:      '72.3.1.1',
      crystal_system: 'Tetragonal',
      hardness_min: 4.5,
      hardness_max: 5,
      specific_gravity_min: 2.33,
      specific_gravity_max: 2.37,
      cleavage:    'Perfect on {001}',
      fracture:    'Uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Pearly on {001}'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Colourless, white, pale green, pale pink, pale yellow',
      streak:      'White',
      fluorescence: 'Weak yellow or green under UV (variable)',
      ri_min:      1.535,
      ri_max:      1.537,
      birefringence: 0.002,
      optical_type: 'U',
      shortdesc:   'Hydrated potassium calcium silicate. Forms perfect cubic or pyramidal crystals of exceptional transparency. The name derives from Greek "apo" (away) + "phyllon" (leaf) — it exfoliates on heating.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-35858.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Apophyllite',
      refractive_index: { n_omega: 1.537, n_epsilon: 1.535 },
      birefringence:   0.002,
      optical_sign:    '-',
      dispersion:      'Very weak',
      pleochroism:     null,
      fluorescence_lw: 'Weak yellow or green',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R040054'],
    },

    color: {
      primary_color:          'Colourless to pale green',
      color_variants:         ['Water-clear colourless', 'Pale mint green', 'Pale pink', 'White', 'Pale yellow'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.90, c: 0.04, h: 155 },
      hex:     '#d8ede5',
      munsell: '5G 9/2',
      color_temperature_k:    null,
      psychological_effects:  [
        'Crystal clarity — the most optically transparent of the light-working stones',
        'The absence of colour makes it a pure amplifier — it carries whatever intention is placed within it',
        'Pale green variety activates the heart alongside the third eye — compassionate clarity',
        'Induces a still, receptive state in the mind — ideal for deep meditation and inner listening',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   [135, 175],
      },
    },

    metaphysical: {
      mineral_name:     'Apophyllite',
      chakra_primary:   'Third Eye',
      chakra_secondary: ['Crown', 'Heart'],
      element:   ['Aether', 'Air'],
      planet:    ['Moon', 'Uranus'],
      archetype: ['The Akashic Mirror', 'The Crystal Seer', 'The Silent Witness'],
      zodiac:    ['Gemini', 'Libra', 'Aquarius'],
      numerology: 4,
      angel_number: 444,
      intention: 'I see clearly. I receive truth in stillness. The Akashic Record is open.',
      traditions: [
        'Western crystal healing — third eye and channelling work',
        'New Age tradition — Akashic Record access',
        'Reiki and energy healing — used to open treatment spaces',
      ],
      properties: [
        'Named from Greek: apo (away from) + phyllon (leaf) — it exfoliates into leaf-like layers on heating',
        'Forms perfect cubic and pyramidal crystals of extraordinary transparency — among the clearest natural minerals',
        'The premier Akashic Record stone — used to access higher-dimensional information in meditation',
        'Excellent for creating a high-vibrational space — many healers place clusters at the head of treatment tables',
        'Supports astral travel, past-life recall, and deep meditative states',
        'Pale green variety bridges heart and third eye — adds love and compassion to psychic perception',
        'Its extraordinary internal light-play makes it one of the most visually captivating meditation objects',
      ],
      gaia_resonance: 'Noosphere + SomnusVeil + ClarusLens',
      safety_warning: 'Water-sensitive — contains structural water; prolonged immersion may damage the crystal. Do not use in water elixirs. Handle with care as it cleaves perfectly on {001}.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 3. AQUAMARINE
  // Blue beryl — the sea stone — the stone of courage and clarity
  // Favoured by Roman sailors, Renaissance emperors, and NASA
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Aquamarine',
    mindat_id:   null,
    rruff_ids:   ['R050031'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Carnelian',

    physical: {
      id:           0,
      longid:       'aquamarine',
      guid:         '',
      name:         'Beryl (Aquamarine variety)',
      ima_formula:  'Be₃Al₂Si₆O₁₈',
      mindat_formula: 'Be3Al2Si6O18',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '9.CJ.05',
      dana8ed:      '61.1.1.1',
      crystal_system: 'Hexagonal',
      hardness_min: 7.5,
      hardness_max: 8,
      specific_gravity_min: 2.68,
      specific_gravity_max: 2.74,
      cleavage:    'Imperfect on {0001}',
      fracture:    'Conchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Pale to deep blue, blue-green — from Fe²⁺ (blue) and Fe²⁺/Fe³⁺ charge transfer (blue-green)',
      streak:      'White',
      fluorescence: 'None to very weak',
      ri_min:      1.567,
      ri_max:      1.590,
      birefringence: 0.006,
      optical_type: 'U',
      shortdesc:   'Blue variety of beryl coloured by iron. The name means "water of the sea" in Latin. One of the most prized gems in antiquity. Brazil is the world\'s primary source for fine aquamarine.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-783.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Aquamarine',
      refractive_index: { n_omega: 1.590, n_epsilon: 1.567 },
      birefringence:   0.006,
      optical_sign:    '-',
      dispersion:      '0.014',
      pleochroism:     'Weak to moderate: pale blue / deeper blue',
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 450, max: 500 },
      spectra: ['R050031'],
    },

    color: {
      primary_color:          'Sky blue to sea blue-green',
      color_variants:         ['Pale ice blue', 'Clear sky blue', 'Sea blue-green', 'Deep Santa Maria blue', 'Teal (heat-treated)'],
      dominant_wavelength_nm: 475,
      oklch:   { l: 0.70, c: 0.14, h: 218 },
      hex:     '#6bbcd8',
      munsell: '5B 6/6',
      color_temperature_k:    11000,
      psychological_effects:  [
        'The pale blue frequency is universally associated with expansive calm — open sky, open sea',
        'Aquamarine blue holds the quality of courage within serenity — the calm before the voyage',
        'Deeply clarifying to the mental body — removes fog, indecision, and mental noise',
        'The sea-glass quality of fine aquamarine is one of the most emotionally resonant colours in the natural world',
      ],
      harmonics: {
        complementary_hue: 38,
        triadic_hues:      [338, 98],
        analogous_range:   [198, 238],
      },
    },

    metaphysical: {
      mineral_name:     'Aquamarine',
      chakra_primary:   'Throat',
      chakra_secondary: ['Heart', 'Third Eye'],
      element:   ['Water'],
      planet:    ['Neptune', 'Moon'],
      archetype: ['The Sailor\'s Stone', 'The Courageous Speaker', 'The Sea Keeper'],
      zodiac:    ['Pisces', 'Aquarius', 'Aries'],
      numerology: 1,
      angel_number: 111,
      intention: 'I move through uncertainty with calm courage. My voice is clear as open water.',
      traditions: [
        'Ancient Roman tradition — sailors\' amulet against storms and drowning',
        'Ancient Greek tradition — sacred to Poseidon',
        'Medieval tradition — the stone of courage and foresight',
        'Western crystal healing',
      ],
      properties: [
        'Name from Latin "aqua" (water) + "mare" (sea) — the water of the sea',
        'Roman sailors carried aquamarine as protection from storms and as a guarantee of safe return',
        'The world\'s largest faceted aquamarine — the Dom Pedro (10,363 carats) — resides at the Smithsonian',
        'The stone of courage: supports those about to embark on a new journey, challenge, or truth',
        'The premier throat chakra gem: clear, precise, courageous expression of inner truth',
        'Aligns the emotional and mental bodies — brings calm clarity to emotionally charged situations',
        'Sacred to Poseidon/Neptune — one of the oldest mythologically documented gemstones',
      ],
      gaia_resonance: 'SovereignCore + ClarusLens',
      safety_warning: null,
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 4. ARAGONITE
  // Calcium carbonate polymorph — the earth-star stabiliser
  // The structural mineral of pearl, coral, and mollusk shell
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Aragonite',
    mindat_id:   308,
    rruff_ids:   ['R040078'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Amethyst',

    physical: {
      id:           308,
      longid:       'aragonite',
      guid:         '',
      name:         'Aragonite',
      ima_formula:  'CaCO₃',
      mindat_formula: 'CaCO3',
      ima_status:   'A',
      ima_year:     1797,
      strunzten:    '5.AB.15',
      dana8ed:      '14.1.3.1',
      crystal_system: 'Orthorhombic',
      hardness_min: 3.5,
      hardness_max: 4,
      specific_gravity_min: 2.93,
      specific_gravity_max: 2.95,
      cleavage:    'Distinct on {010}, imperfect on {110} and {011}',
      fracture:    'Subconchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Resinous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'White, colourless, yellow, orange, brown, blue, green — the star-burst aragonite clusters are orange-brown',
      streak:      'White',
      fluorescence: 'Weak to moderate yellow, green, or pink under UV',
      ri_min:      1.530,
      ri_max:      1.685,
      birefringence: 0.155,
      optical_type: 'B',
      shortdesc:   'Calcium carbonate polymorph (with calcite and vaterite). Forms the shell of mollusks, the structure of coral reefs, and the nacre of pearls. The orthorhombic sputnik/star-burst clusters are iconic.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-308.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Aragonite',
      refractive_index: { n_alpha: 1.530, n_beta: 1.682, n_gamma: 1.685 },
      birefringence:   0.155,
      optical_sign:    '-',
      dispersion:      'Weak',
      pleochroism:     null,
      fluorescence_lw: 'Weak yellow, green, or pink',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R040078'],
    },

    color: {
      primary_color:          'White to orange-brown (clusters); wide natural range',
      color_variants:         ['Pure white bladed crystals', 'Orange-brown star-burst clusters', 'Yellow', 'Blue (rare)', 'Green (rare)', 'Colourless'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.75, c: 0.08, h: 60 },
      hex:     '#d4b870',
      munsell: '2.5Y 7/4',
      color_temperature_k:    3500,
      psychological_effects:  [
        'The star-burst form activates a sense of energetic radiation outward from a central point',
        'Orange-brown clusters carry warm, earthy, stabilising energy',
        'Encourages patience, reliability, and the capacity to show up consistently',
        'One of the most grounding forms in the mineral kingdom — literally the structure of coral and pearl',
      ],
      harmonics: {
        complementary_hue: 240,
        triadic_hues:      [180, 300],
        analogous_range:   [40, 80],
      },
    },

    metaphysical: {
      mineral_name:     'Aragonite',
      chakra_primary:   'Root',
      chakra_secondary: ['Earth Star', 'Sacral'],
      element:   ['Earth'],
      planet:    ['Saturn', 'Earth'],
      archetype: ['The Earth Star Keeper', 'The Structural Foundation', 'The Patience Teacher'],
      zodiac:    ['Capricorn', 'Taurus', 'Virgo'],
      numerology: 9,
      angel_number: 999,
      intention: 'I am rooted. I build steadily. My foundation is the living Earth.',
      traditions: [
        'Named for Molina de Aragón, Spain — described by Werner in 1797',
        'Western crystal healing',
      ],
      properties: [
        'IMA-recognised since 1797 — named for Molina de Aragón in Spain',
        'CaCO₃ polymorph with calcite — forms at lower temperatures and pressures',
        'The biological carbonate: aragonite builds mollusk shells, coral reefs, and the nacre of pearls',
        'The orthorhombic sputnik/star-burst clusters radiate energy equally in all directions',
        'The premier Earth Star chakra stone — grounds the practitioner below the feet into the living Earth',
        'Teaches patience, persistence, and structural reliability — the energy of coral building a reef over centuries',
        'Excellent for those feeling ungrounded, scattered, or overwhelmed by too much spiritual energy',
      ],
      gaia_resonance: 'ViriditasHeart + SovereignCore',
      safety_warning: 'Acid-sensitive — dissolves in dilute HCl. Do not use in water elixirs. Keep away from acidic cleaners. Relatively soft (H3.5-4) — handle with care.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 5. ASTROPHYLLITE
  // Titanium potassium iron silicate — golden star blades
  // One of the most visually otherworldly minerals on Earth
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Astrophyllite',
    mindat_id:   383,
    rruff_ids:   ['R040139'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Moonstone',

    physical: {
      id:           383,
      longid:       'astrophyllite',
      guid:         '',
      name:         'Astrophyllite',
      ima_formula:  'K₂NaFe⁷²⁺Ti₂Si₈O₂₆(OH)₄F',
      mindat_formula: 'K2NaFe7Ti2Si8O26(OH)4F',
      ima_status:   'A',
      ima_year:     1854,
      strunzten:    '9.DE.20',
      dana8ed:      '72.5.1.1',
      crystal_system: 'Triclinic',
      hardness_min: 3,
      hardness_max: 3.5,
      specific_gravity_min: 3.30,
      specific_gravity_max: 3.40,
      cleavage:    'Perfect on {001}',
      fracture:    'Uneven',
      tenacity:    'Brittle',
      luster:      ['Metallic', 'Submetallic', 'Pearly on cleavage'],
      diaphaneity: ['Opaque', 'Translucent on thin blades'],
      colour:      'Bronze-gold, golden-brown to dark brown — forms radiating star-burst blades in dark matrix',
      streak:      'Yellowish-brown',
      fluorescence: null,
      ri_min:      1.678,
      ri_max:      1.733,
      birefringence: 0.055,
      optical_type: 'B',
      shortdesc:   'Complex titanium potassium iron inosilicate. Forms radiating bronze-gold blade clusters in dark syenite matrix. Name from Greek "astron" (star) + "phyllon" (leaf). One of the most visually spectacular minerals.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-383.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Astrophyllite',
      refractive_index: { n_alpha: 1.678, n_beta: 1.703, n_gamma: 1.733 },
      birefringence:   0.055,
      optical_sign:    '+',
      dispersion:      'Strong',
      pleochroism:     'Strong: yellow-brown / dark brown / bronze-gold',
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 560, max: 660 },
      spectra: ['R040139'],
    },

    color: {
      primary_color:          'Bronze-gold to dark brown blades in black matrix',
      color_variants:         ['Bright bronze-gold blades', 'Dark copper-brown', 'Golden-green iridescence on blades', 'Dark matrix with starburst inclusions'],
      dominant_wavelength_nm: 605,
      oklch:   { l: 0.42, c: 0.14, h: 58 },
      hex:     '#7a5a20',
      munsell: '7.5YR 4/6',
      color_temperature_k:    2800,
      psychological_effects:  [
        'The star-blade form radiating from a centre point in dark matrix is one of nature\'s most powerful visual symbols',
        'Bronze-gold against black — the archetype of light emerging from darkness',
        'Activates a sense of one\'s own luminosity against a dark background',
        'Strong pleochroism means the colour shifts as you move the stone — encourages multiple perspectives',
      ],
      harmonics: {
        complementary_hue: 238,
        triadic_hues:      [178, 298],
        analogous_range:   [38, 78],
      },
    },

    metaphysical: {
      mineral_name:     'Astrophyllite',
      chakra_primary:   'Crown',
      chakra_secondary: ['Third Eye', 'Solar Plexus', 'Earth Star'],
      element:   ['Aether', 'Earth', 'Fire'],
      planet:    ['Uranus', 'Pluto', 'Saturn'],
      archetype: ['The Star Soul', 'The Cosmic Traveller', 'The Golden Light in Darkness'],
      zodiac:    ['Scorpio', 'Capricorn', 'Aquarius'],
      numerology: 7,
      angel_number: 777,
      intention: 'I am a star soul in a physical body. My light radiates from my centre.',
      traditions: [
        'Named by Breithaupt 1854 from the Langesundsfjord, Norway',
        'Western crystal healing — cosmic consciousness and star soul work',
      ],
      properties: [
        'IMA-recognised since 1854 — named from Greek "astron" (star) + "phyllon" (leaf) for its star-blade form',
        'Complex titanium iron silicate — one of the most chemically unusual minerals in the tradition',
        'Found primarily in nepheline syenite in Norway, Russia, Colorado, and Greenland',
        'The radiating blade structure makes it one of the most visually otherworldly minerals in existence',
        'The premier "star soul" stone — works with those who feel they carry a cosmic rather than purely earthly origin',
        'Supports out-of-body experiences, cosmic consciousness, and the integration of stellar ancestry',
        'Angel number 777 — the highest mystical frequency — aligned with its extraordinary rarity and visual power',
      ],
      gaia_resonance: 'QuantumNexus + Noosphere + SomnusVeil',
      safety_warning: 'Contains iron and titanium — do not use in water elixirs. Perfect cleavage on {001} — blades can separate. Relatively soft (H3-3.5) — protect from hard surfaces.',
    },
  },

];

export default BATCH_A6;
