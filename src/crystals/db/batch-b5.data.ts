/**
 * src/crystals/db/batch-b5.data.ts
 * GAIA-OS Crystal Database — Batch B-5
 *
 * Entries:
 *   1. Black Aragonite
 *   2. Blue Kyanite
 *   3. Blue Lace Agate
 *   4. Blue Opal
 *   5. Blue Quartz
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-29
 *
 * NOTE: A batch of quiet power. Black Aragonite is an unusual dark form
 * of the carbonate polymorph found in hot-spring deposits — earthy, raw,
 * and deeply grounding. Blue Kyanite is one of the few minerals that never
 * needs cleansing — it does not accumulate negative charge. Blue Lace Agate
 * is one of the gentlest stones in the entire tradition — the communicator's
 * stone of soft courage. Blue Opal bridges the Peruvian and Andean traditions
 * with Paracas culture and Pacific consciousness. Blue Quartz is the opaque,
 * inclusion-bearing twin of clear quartz — same SiO₂, completely different
 * personality.
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_B5: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. BLACK ARAGONITE
  // Calcium carbonate (orthorhombic polymorph) — dark iron/organic-stained form
  // Hot-spring, cave, and marine sediment deposits worldwide
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Black Aragonite',
    mindat_id:   307,
    rruff_ids:   ['R040078'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'White Aragonite',

    physical: {
      id:           307,
      longid:       'black-aragonite',
      guid:         '',
      name:         'Aragonite (dark/black colour form — iron oxide or organic matter staining)',
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
      fracture:    'Subconchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Resinous'],
      diaphaneity: ['Translucent', 'Opaque'],
      colour:      'Black to dark grey-brown — from iron oxide inclusions or incorporated organic matter in carbonate deposits',
      streak:      'White',
      fluorescence: 'Variable: weak yellow, green, or inert',
      ri_min:      1.530,
      ri_max:      1.686,
      birefringence: 0.156,
      optical_type: 'B',
      shortdesc:   'Black/dark variety of aragonite — the orthorhombic CaCO₃ polymorph. Colour from iron oxide or organic inclusions. Found in hot-spring sinters, cave deposits, and oxidised ore zones. IMA-recognised species since 1797, named after Aragón, Spain.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-307.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Black Aragonite',
      refractive_index: { n_alpha: 1.530, n_beta: 1.682, n_gamma: 1.686 },
      birefringence:   0.156,
      optical_sign:    '-',
      dispersion:      'Weak',
      pleochroism:     null,
      fluorescence_lw: 'Variable: weak yellow or green; some specimens inert',
      fluorescence_sw: 'Variable',
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R040078'],
    },

    color: {
      primary_color:          'Black to dark charcoal-grey',
      color_variants:         [
        'Jet black (strongly organic- or iron-stained)',
        'Dark grey-black banded (Millard County, Utah — layered with white)',
        'Dark brown-black (iron oxide dominant)',
        'Black with translucent white banding (common trade form)',
      ],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.15, c: 0.01, h: 60 },
      hex:     '#252220',
      munsell: 'N 2/',
      color_temperature_k:    null,
      psychological_effects:  [
        'The dark earthy tone of black aragonite anchors without the severity of black tourmaline — softer darkness',
        'The contrast of black and white banding (common in Utah specimens) visualises the integration of shadow and light',
        'The carbonate origin — the same mineral as shells, coral, and bone — gives it a biological intimacy that pure silicates lack',
        'Encourages acceptance of the shadow self — the hidden, unprocessed, or unconscious material — without fear',
        'The earthy, matte surface communicates humility and groundedness rather than power or drama',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   null,
      },
    },

    metaphysical: {
      mineral_name:     'Black Aragonite',
      chakra_primary:   'Earth Star',
      chakra_secondary: ['Root', 'Sacral'],
      element:   ['Earth', 'Water'],
      planet:    ['Saturn', 'Pluto'],
      archetype: ['The Shadow Integrator', 'The Ancient Earth', 'The Calm Anchor'],
      zodiac:    ['Capricorn', 'Scorpio', 'Taurus'],
      numerology: 4,
      angel_number: 404,
      intention: 'I embrace all parts of myself — light and shadow — and find peace in the whole.',
      traditions: [
        'Western crystal healing — modern tradition',
        'Named after Molina de Aragón, Spain — type locality of the first described specimens (1797)',
        'Cave and hot-spring contexts give it an ancient Earth association across global indigenous traditions near travertine formations',
      ],
      properties: [
        'IMA-recognised species since 1797 — named after Aragón (Molina de Aragón), Spain, its type locality',
        'The orthorhombic polymorph of CaCO₃ — calcite is the trigonal polymorph. Aragonite converts slowly to calcite at surface conditions',
        'Extremely high birefringence (0.156) — one of the highest of any common mineral — creates vivid interference colours in thin section',
        'The dark colour in black aragonite is from iron oxide inclusions or incorporated organic matter — not a separate species from white aragonite',
        'Found in hot-spring sinters (travertine), cave speleothems, marine bivalve shells, and oxidised ore zones',
        'Aragonite is the primary mineral of mollusk shells, coral skeletons, and Pearl (nacre is aragonite + conchiolin)',
        'The black-and-white banded form from Millard County, Utah is among the most striking trade specimens',
        'Softer than quartz (H3.5-4) — requires careful handling and protection from water immersion (dissolves slowly)',
        'The yin-yang of white aragonite and black aragonite is a natural teaching on the integration of light and shadow within the same substance',
      ],
      gaia_resonance: 'AnchoredRoot + SovereignCore',
      safety_warning: '⚠️ ACID-SENSITIVE — aragonite dissolves in dilute hydrochloric acid with vigorous effervescence. Do NOT use in water elixirs. Avoid prolonged water contact — will slowly etch. Soft (H3.5-4) — store separately from harder minerals. Handle with care.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 2. BLUE KYANITE
  // Aluminium silicate — anisotropic hardness, the alignment stone
  // One of the few minerals believed to never need energetic cleansing
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Blue Kyanite',
    mindat_id:   2303,
    rruff_ids:   ['R040030'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Black Kyanite',

    physical: {
      id:           2303,
      longid:       'blue-kyanite',
      guid:         '',
      name:         'Kyanite (blue colour variety)',
      ima_formula:  'Al₂(SiO₄)O',
      mindat_formula: 'Al2(SiO4)O',
      ima_status:   'A',
      ima_year:     1789,
      strunzten:    '9.AF.25',
      dana8ed:      '52.3.2.1',
      crystal_system: 'Triclinic',
      hardness_min: 4.5,
      hardness_max: 7,
      specific_gravity_min: 3.53,
      specific_gravity_max: 3.67,
      cleavage:    'Perfect on {100}, good on {010}',
      fracture:    'Splintery',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Pearlescent on cleavage'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Blue, white, light grey, green, rarely yellow, orange, pink — blue variety most prized',
      streak:      'White',
      fluorescence: 'None to very weak red under UV',
      ri_min:      1.710,
      ri_max:      1.734,
      birefringence: 0.017,
      optical_type: 'B',
      shortdesc:   'Kyanite — blue aluminosilicate with strongly anisotropic hardness: H4.5 along the length of bladed crystals but H6.5-7 across. Named from Greek kyanos (blue). Found in metamorphic rocks. A GIA indicator mineral for high-pressure metamorphism.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-2303.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Blue Kyanite',
      refractive_index: { n_alpha: 1.710, n_beta: 1.719, n_gamma: 1.724 },
      birefringence:   0.017,
      optical_sign:    '-',
      dispersion:      '0.020',
      pleochroism:     'Trichroic: colourless / violet-blue / blue',
      fluorescence_lw: 'None to very weak red',
      fluorescence_sw: 'None',
      phosphorescence: null,
      visible_wavelength_nm: { min: 450, max: 480 },
      spectra: ['R040030'],
    },

    color: {
      primary_color:          'Blue — from cornflower to deep sapphire, often with white streaks',
      color_variants:         [
        'Cornflower blue with white matrix streaks (Nepal — classic form)',
        'Deep sapphire blue (Brazil)',
        'Pale ice blue (translucent, Kenya)',
        'Blue with strong colour zoning (colour bands along crystal length)',
        'Blue-grey (common)',
        'Teal-blue (rare)',
      ],
      dominant_wavelength_nm: 470,
      oklch:   { l: 0.50, c: 0.22, h: 258 },
      hex:     '#4a6fa5',
      munsell: '10B 5/8',
      color_temperature_k:    null,
      psychological_effects:  [
        'The bladed crystal form — long, flat, striated — creates a natural sense of directional alignment',
        'The blue colour with frequent white matrix streaks creates a sky-and-cloud imagery — expansiveness',
        'Trichroism means the crystal appears differently coloured from three directions — encourages multi-perspectival thinking',
        'The extreme hardness anisotropy is a teaching in itself: strength is not uniform — it depends on direction and context',
        'The tradition of kyanite never needing cleansing creates a profound trust — a consistent, self-regulating presence',
      ],
      harmonics: {
        complementary_hue: 78,
        triadic_hues:      [18, 138],
        analogous_range:   [238, 278],
      },
    },

    metaphysical: {
      mineral_name:     'Blue Kyanite',
      chakra_primary:   'Throat',
      chakra_secondary: ['Third Eye', 'Crown'],
      element:   ['Air', 'Akasha'],
      planet:    ['Jupiter', 'Uranus'],
      archetype: ['The Aligner', 'The Channel', 'The Bridge'],
      zodiac:    ['Libra', 'Aries', 'Taurus'],
      numerology: 4,
      angel_number: 444,
      intention: 'I align with truth. My voice carries clarity, and my mind bridges worlds.',
      traditions: [
        'Western crystal healing — one of the few stones universally described as self-cleansing',
        'Named from Greek kyanos (blue) — same root as cyan',
        'Used by geologists as a pressure-temperature indicator mineral for high-pressure metamorphic terrains',
        'Nepal and Tibet — blue kyanite found in the Himalayan metamorphic belt; associated with mountain spiritual traditions',
      ],
      properties: [
        'IMA-recognised since 1789 — named from Greek kyanos (blue)',
        'One of only two common minerals with strongly anisotropic (directional) hardness: H4.5 parallel to the crystal length, H6.5-7 across it — the same crystal, two different hardnesses',
        'This hardness anisotropy is the result of the triclinic crystal structure and Al-O bond directionality',
        'Found in high-pressure metamorphic rocks — a key P-T indicator mineral for petrologists mapping ancient subduction zones',
        'Trichroic: colourless, violet-blue, and blue — three different colours visible from three crystal directions',
        'The crystal healing tradition holds kyanite as one of the few stones that never accumulates negative energy and never needs cleansing — attributed to its self-aligning electromagnetic properties',
        'Blue kyanite blades from Nepal and Brazil are the most prized — long, flat, striated crystals in cornflower to sapphire blue',
        'Associated with bridging — between chakras, between people, between the conscious and unconscious',
        'The yin pair with black kyanite: blue aligns and opens communication; black grounds and cuts cords',
      ],
      gaia_resonance: 'ClarusLens + Noosphere',
      safety_warning: 'Generally safe for water (brief contact). The anisotropic hardness means the crystal can cleave or splinter easily when pressure is applied along the length — handle bladed specimens carefully along that axis. No toxic components.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 3. BLUE LACE AGATE
  // Microcrystalline quartz (chalcedony) — lace-patterned blue-white banding
  // Primary source: Ysterputs farm, Namibia — one of the world's finest agates
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Blue Lace Agate',
    mindat_id:   955,
    rruff_ids:   ['R040031'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Fire Agate',

    physical: {
      id:           955,
      longid:       'blue-lace-agate',
      guid:         '',
      name:         'Chalcedony (Blue Lace Agate — pale blue and white lace-patterned banded agate)',
      ima_formula:  'SiO₂',
      mindat_formula: 'SiO2',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '4.DA.05',
      dana8ed:      '75.1.3.1',
      crystal_system: 'Trigonal (cryptocrystalline)',
      hardness_min: 6.5,
      hardness_max: 7,
      specific_gravity_min: 2.58,
      specific_gravity_max: 2.65,
      cleavage:    'None',
      fracture:    'Conchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Waxy', 'Vitreous'],
      diaphaneity: ['Translucent'],
      colour:      'Pale blue and white, with intricate lace-patterned banding — blue from iron or titanium trace elements in the silica matrix',
      streak:      'White',
      fluorescence: 'None to weak',
      ri_min:      1.530,
      ri_max:      1.540,
      birefringence: 0.004,
      optical_type: 'U',
      shortdesc:   'Blue Lace Agate — a pale blue and white, lace-patterned banded agate (chalcedony). Primary source: Ysterputs farm (Namibia), a vein agate in Jurassic dolerite. A trade variety name. One of the softest-toned and most intricate agates in the tradition.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-955.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Blue Lace Agate',
      refractive_index: { n: 1.535 },
      birefringence:   0.004,
      optical_sign:    '-',
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: 'None to very weak',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: { min: 460, max: 490 },
      spectra: ['R040031'],
    },

    color: {
      primary_color:          'Pale sky blue and white — soft, intricate lace banding',
      color_variants:         [
        'Pale sky blue with white lace (Namibia — classic)',
        'Powder blue with very fine white threading',
        'Soft blue-grey with translucent bands',
        'Blue with subtle purple undertone (rare)',
        'Similar material from Malawi (slightly deeper blue)',
      ],
      dominant_wavelength_nm: 480,
      oklch:   { l: 0.72, c: 0.08, h: 232 },
      hex:     '#a8c4db',
      munsell: '5B 7/4',
      color_temperature_k:    null,
      psychological_effects:  [
        'The pale, soft blue is one of the most psychologically calming colour-mineral combinations in the tradition',
        'The intricate lace banding creates a sense of natural complexity within serenity — like looking at cloud patterns',
        'The translucency allows light to pass through — a glowing quality unique among opaque stones',
        'Encourages gentle speech, careful communication, and the expression of difficult truths with softness',
        'The extreme delicacy of the pattern communicates precision and care — nothing accidental about its beauty',
      ],
      harmonics: {
        complementary_hue: 52,
        triadic_hues:      [352, 112],
        analogous_range:   [212, 252],
      },
    },

    metaphysical: {
      mineral_name:     'Blue Lace Agate',
      chakra_primary:   'Throat',
      chakra_secondary: ['Third Eye', 'Crown'],
      element:   ['Air', 'Water'],
      planet:    ['Mercury', 'Neptune'],
      archetype: ['The Gentle Communicator', 'The Soft Voice', 'The Peacemaker'],
      zodiac:    ['Gemini', 'Pisces', 'Aquarius'],
      numerology: 5,
      angel_number: 555,
      intention: 'I speak my truth with gentleness and grace. My words carry the frequency of peace.',
      traditions: [
        'Western crystal healing — THE gentle Throat chakra stone; the communicator for sensitive souls',
        'Namibian origin — Ysterputs farm (meaning "iron holes"), adjacent to Blinkpan shallow lake, Namibia',
        'Until 2017, the Ysterputs mine was the sole primary source — the original mine is now closed, making original Namibian specimens increasingly rare',
        'Malawi and South Africa now produce similar material; Namibian specimens remain the benchmark',
      ],
      properties: [
        'Trade name: "Blue Lace Agate" — a variety of banded chalcedony (microcrystalline quartz)',
        'A vein agate: formed in fractures within Jurassic-age dolerite in Namibia — the host rock is crucial to the formation of the lace pattern',
        'The original and primary source — Ysterputs farm (farm 254), Namibia — has historically been the benchmark for quality; the mine closed around 2017',
        'The intricate lace pattern forms from alternating growth bands of slightly different silica compositions during hydrothermal deposition',
        'Pale blue colour attributed to iron or titanium trace inclusions within the microcrystalline quartz matrix',
        'H6.5-7 and good toughness — one of the more durable stones for jewellery despite its delicate appearance',
        'THE gentlest and most consistently recommended Throat chakra stone in the modern crystal tradition',
        'Particularly recommended for those who struggle to speak their truth, those with throat conditions, and those in communication-sensitive roles',
        'The yin pair with fire agate: the fierce, flashing protector and the soft, clear communicator — action and speech',
      ],
      gaia_resonance: 'ClarusLens + Noosphere',
      safety_warning: 'Safe for water. Safe for daily wear at H6.5-7. No toxicity concerns. The pale colour can fade with prolonged intense UV exposure — avoid long-term direct sunlight display.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 4. BLUE OPAL
  // Translucent blue opal — no play-of-colour; colour from light scattering
  // Andean/Peruvian opal — the most significant variety
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Blue Opal',
    mindat_id:   5725,
    rruff_ids:   ['R050080'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Fire Opal',

    physical: {
      id:           5725,
      longid:       'blue-opal',
      guid:         '',
      name:         'Blue Opal (Opal — translucent blue, no play-of-colour; Andean/Peruvian opal)',
      ima_formula:  'SiO₂·nH₂O',
      mindat_formula: 'SiO2·nH2O',
      ima_status:   'A',
      ima_year:     1813,
      strunzten:    '4.DA.10',
      dana8ed:      '75.2.1.1',
      crystal_system: 'Amorphous (mineraloid)',
      hardness_min: 5.5,
      hardness_max: 6.5,
      specific_gravity_min: 1.98,
      specific_gravity_max: 2.20,
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Waxy', 'Vitreous', 'Resinous'],
      diaphaneity: ['Translucent'],
      colour:      'Translucent blue — from light scattering (Rayleigh/Tyndall effect) or from microscopic admixture of chrysocolla or other Cu minerals',
      streak:      'White',
      fluorescence: 'Variable: green or white under UV; some inert',
      ri_min:      1.370,
      ri_max:      1.470,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Blue Opal — translucent blue opal with no play-of-colour. Blue caused by light scattering or chrysocolla admixture. Andean (Peruvian) opal is the most significant variety — national stone of Peru, associated with Paracas and Andean textile cultures.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-5725.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name: 'Blue Opal',
      refractive_index: { n: 1.420 },
      birefringence:   null,
      optical_sign:    null,
      dispersion:      'None (no play-of-colour)',
      pleochroism:     null,
      fluorescence_lw: 'Variable: green or white; some inert',
      fluorescence_sw: 'Variable',
      phosphorescence: 'Possible in some specimens',
      visible_wavelength_nm: { min: 460, max: 500 },
      spectra: ['R050080'],
    },

    color: {
      primary_color:          'Translucent blue — from pale sky to deep ocean blue',
      color_variants:         [
        'Pale sky blue (Peruvian/Andean opal — most prized)',
        'Blue-green teal (chrysocolla-stained)',
        'Deep ocean blue (Oregon blue opal)',
        'Medium powder blue with matrix (common trade form)',
        'Blue-grey translucent',
      ],
      dominant_wavelength_nm: 480,
      oklch:   { l: 0.62, c: 0.14, h: 228 },
      hex:     '#7fb3cc',
      munsell: '5B 6/6',
      color_temperature_k:    null,
      psychological_effects:  [
        'Blue opal without play-of-colour has a completely different psychological register than precious opal — steady, serene, unwavering',
        'The translucency creates depth without fire — you can look into the stone, not at it',
        'The Andean/Peruvian origin evokes high-altitude lake environments — Titicaca, Andean sky, pre-Inca culture',
        'The absence of flash or drama makes it a stone of inner calm rather than outer show',
        'Its connection to water and the Pacific creates a vast, oceanic sense of consciousness',
      ],
      harmonics: {
        complementary_hue: 48,
        triadic_hues:      [348, 108],
        analogous_range:   [208, 248],
      },
    },

    metaphysical: {
      mineral_name:     'Blue Opal',
      chakra_primary:   'Throat',
      chakra_secondary: ['Third Eye', 'Heart'],
      element:   ['Water', 'Air'],
      planet:    ['Venus', 'Neptune', 'Moon'],
      archetype: ['The Serene Depth', 'The Andean Sky', 'The Pacific Consciousness'],
      zodiac:    ['Cancer', 'Scorpio', 'Pisces'],
      numerology: 2,
      angel_number: 222,
      intention: 'I am a vessel of calm, depth, and clear communication. My still waters run deep.',
      traditions: [
        'Andean tradition — Peruvian blue opal is the national stone of Peru; associated with pre-Columbian Andean cultures including Paracas and Nazca',
        'Paracas culture (700 BCE–200 CE) — high-quality textiles used blue dyes matching the opal\'s colour; connection to the Pacific and sky',
        'Western crystal healing — gentle, non-dramatic Throat and Third Eye stone',
        'Oregon (USA) — blue common opal from Opal Butte, Morrow County, Oregon; distinct North American variety',
      ],
      properties: [
        'Mindat-recognised variety (min-5725) — translucent blue opal with no play-of-colour',
        'The blue colour has two different causes: (1) Rayleigh/Tyndall light scattering in the silica structure — the same physics as the blue sky, and (2) microscopic admixture of chrysocolla or other copper minerals',
        'Andean (Peruvian) opal — the most commercially significant variety; found in the Andes of Peru, national stone of Peru',
        'The Peruvian blue opal is formed in volcanic environments at high altitude — one of the world's only significant opal deposits outside Australia',
        'Contains 3-21% water — all opals are sensitive to dehydration and rapid temperature changes',
        'Unlike precious opal, blue opal has no play-of-colour — its beauty is in the depth and translucency of the blue itself',
        'Oregon blue opal (Opal Butte, Morrow County) is a distinct and prized North American variety — hyalite and contra luz also found at the same locality',
        'The chrysocolla-admixed form (Blue Andes Opal) has a more intense blue-green teal colour',
        'The yin pair with fire opal: calm blue translucent water energy vs. fierce orange-red fire — ocean and flame',
      ],
      gaia_resonance: 'ClarusLens + ViriditasHeart',
      safety_warning: '⚠️ DEHYDRATION-SENSITIVE — contains 3-21% water. Never expose to extreme heat, prolonged direct sun, or ultrasonic cleaners. Do not use in water elixirs — soft and porous. Avoid prolonged water immersion. Store in a stable, moderate-humidity environment. Handle with care — conchoidal fracture and low hardness (H5.5-6.5).',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 5. BLUE QUARTZ
  // SiO₂ — opaque to translucent blue variety; colour from mineral inclusions
  // The grounded, opaque twin of clear quartz — inclusion-bearing and earthy
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Blue Quartz',
    mindat_id:   28957,
    rruff_ids:   ['R040031'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Clear Quartz',

    physical: {
      id:           28957,
      longid:       'blue-quartz',
      guid:         '',
      name:         'Quartz (Blue Quartz — opaque to translucent, colour from fibrous magnesioriebeckite, crocidolite, or tourmaline inclusions)',
      ima_formula:  'SiO₂',
      mindat_formula: 'SiO2',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '4.DA.05',
      dana8ed:      '75.1.3.1',
      crystal_system: 'Trigonal',
      hardness_min: 7,
      hardness_max: 7,
      specific_gravity_min: 2.65,
      specific_gravity_max: 2.65,
      cleavage:    'None (conchoidal fracture dominant)',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Waxy (massive form)'],
      diaphaneity: ['Opaque', 'Translucent'],
      colour:      'Opaque to translucent blue — from fibrous magnesioriebeckite or crocidolite (blue asbestos) inclusions, or from tourmaline inclusions',
      streak:      'White',
      fluorescence: 'None to very weak',
      ri_min:      1.544,
      ri_max:      1.553,
      birefringence: 0.009,
      optical_type: 'U',
      shortdesc:   'Blue Quartz — an opaque to translucent blue variety of quartz, coloured by fibrous magnesioriebeckite, crocidolite, or tourmaline inclusions. Distinct from dumortierite quartz and blue rose quartz. Found in metamorphic, igneous, and pegmatitic contexts.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-26723.html',
      piezoelectric:    true,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name: 'Blue Quartz',
      refractive_index: { n_omega: 1.553, n_epsilon: 1.544 },
      birefringence:   0.009,
      optical_sign:    '+',
      dispersion:      '0.013',
      pleochroism:     'Weak (from inclusion fibres in some specimens)',
      fluorescence_lw: 'None to very weak',
      fluorescence_sw: 'None',
      phosphorescence: null,
      visible_wavelength_nm: { min: 450, max: 480 },
      spectra: ['R040031'],
    },

    color: {
      primary_color:          'Opaque to translucent blue — from milky slate to rich periwinkle',
      color_variants:         [
        'Pale milky blue (magnesioriebeckite-included — most common)',
        'Slate blue-grey (metamorphic variety)',
        'Periwinkle blue (tourmaline-included)',
        'Denim blue (crocidolite-included — note safety)',
        'Blue with aventurescence (rare — from platy inclusions)',
      ],
      dominant_wavelength_nm: 470,
      oklch:   { l: 0.55, c: 0.12, h: 248 },
      hex:     '#7a96b8',
      munsell: '10B 6/6',
      color_temperature_k:    null,
      psychological_effects:  [
        'Blue quartz is the accessible, everyday blue of the quartz family — grounded and wearable where blue kyanite is rare and bladed',
        'The opaque body prevents looking through — this stone keeps its interior private, teaching appropriate boundaries',
        'The combination of quartz hardness and durability with a soft blue creates a rare sense of both strength and gentleness',
        'The knowledge that the blue comes from tiny fibre inclusions — a mineral within a mineral — resonates with the idea of inner gifts and hidden dimensions',
        'The massive, non-crystalline form often feels more accessible than transparent gems — undemanding, quiet, present',
      ],
      harmonics: {
        complementary_hue: 68,
        triadic_hues:      [8, 128],
        analogous_range:   [228, 268],
      },
    },

    metaphysical: {
      mineral_name:     'Blue Quartz',
      chakra_primary:   'Throat',
      chakra_secondary: ['Third Eye', 'Crown'],
      element:   ['Air', 'Water'],
      planet:    ['Mercury', 'Uranus'],
      archetype: ['The Quiet Clarity', 'The Grounded Communicator', 'The Inner Sky'],
      zodiac:    ['Libra', 'Aquarius', 'Virgo'],
      numerology: 7,
      angel_number: 777,
      intention: 'My clarity is quiet and deep. I communicate from a place of inner knowing.',
      traditions: [
        'Western crystal healing — modern tradition; less common than clear quartz but valued for its grounded Throat energy',
        'Named and classified by Mindat as a distinct quartz variety (min-26723)',
        'Llano County, Texas (USA) — one of the most notable localities for blue quartz in metamorphic basement rocks',
        'Global occurrence in granitic, metamorphic, and pegmatitic terrains worldwide',
      ],
      properties: [
        'Mindat-recognised variety (min-26723) — blue quartz: opaque to translucent, colour from fibrous magnesioriebeckite, crocidolite, or tourmaline inclusions',
        'Distinct from dumortierite quartz (which is specifically coloured by dumortierite inclusions) and from blue rose quartz (a trade marketing term of questionable geological basis)',
        'The inclusion fibres responsible for the blue colour are frequently magnesioriebeckite — a member of the riebeckite/crocidolite family',
        'Same SiO₂ composition and H7 hardness as clear quartz — but opaque rather than transparent, with completely different metaphysical character',
        'Piezoelectric — all quartz is piezoelectric; blue quartz retains this property',
        'Found in metamorphic terrains, granitic rocks, and pegmatites worldwide — Llano County Texas, Virginia USA, Brazil, and many others',
        'The accessible, wearable blue of the quartz family — H7 durability means it can be used in any jewellery setting',
        'Carries the amplification property of quartz with the communicative, calming energy of blue',
        'The yin pair with clear quartz: opaque blue vs. transparent clear — hidden depth vs. visible clarity',
      ],
      gaia_resonance: 'ClarusLens + Noosphere',
      safety_warning: '⚠️ FIBRE INCLUSION NOTE — some blue quartz coloured by crocidolite (blue asbestos) fibres. In rough, unpolished form, do NOT sand, grind, or cut without respiratory protection — the fibres are hazardous if inhaled. Polished, tumbled, and cabochon specimens are safe to handle normally. Safe for water in finished form. Keep away from hard drives due to piezoelectric properties.',
    },
  },

];

export default BATCH_B5;
