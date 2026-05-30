/**
 * src/crystals/db/batch-b8.data.ts
 * GAIA-OS Crystal Database — Batch B-8
 *
 * Entries:
 *   1. Brookite              — rare TiO₂ polymorph; orthorhombic titanium oxide
 *   2. Brucite               — Mg(OH)₂; pearlescent magnesium hydroxide
 *   3. Bumblebee Calcite     — yellow-orange banded calcite from Indonesia
 *   4. Bumblebee Jasper      — volcanic rock with realgar/orpiment — HIGHLY TOXIC
 *   5. Butter Jasper         — warm golden-yellow chalcedony/jasper
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-29
 *
 * NOTE: Bumblebee Jasper is NOT a true jasper — it is a volcanic fumarolic
 * deposit containing realgar (AsS) and orpiment (As₂S₃), both highly toxic
 * arsenic sulphides. Bustamite deferred to B-9 as first entry.
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_B8: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. BROOKITE
  // Orthorhombic TiO₂ polymorph — rarest of the three (rutile, anatase, brookite)
  // Named after Henry James Brooke (1771–1857), English crystallographer
  // IMA 1825 — found as sharp, blade-like crystals in Alpine metamorphic veins
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Brookite',
    mindat_id:   820,
    rruff_ids:   ['R060493'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Rutile',

    physical: {
      id:           820,
      longid:       'brookite',
      guid:         '',
      name:         'Brookite',
      ima_formula:  'TiO₂',
      mindat_formula: 'TiO2',
      ima_status:   'A',
      ima_year:     1825,
      strunzten:    '4.DB.05',
      dana8ed:      '4.4.4.1',
      crystal_system: 'Orthorhombic',
      hardness_min: 5.5,
      hardness_max: 6,
      specific_gravity_min: 3.99,
      specific_gravity_max: 4.10,
      cleavage:    'Imperfect on {120} and {001}',
      fracture:    'Subconchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Sub-adamantine', 'Metallic', 'Resinous'],
      diaphaneity: ['Transparent', 'Translucent', 'Opaque'],
      colour:      'Brown to reddish-brown, yellowish-brown, iron-black; thin crystals translucent deep amber or reddish-orange when backlit',
      streak:      'White to pale yellowish',
      fluorescence: 'None',
      ri_min:      2.583,
      ri_max:      2.741,
      birefringence: 0.158,
      optical_type: 'B',
      shortdesc:   'Brookite — TiO₂, orthorhombic titanium dioxide. The rarest of the three TiO₂ polymorphs (rutile = tetragonal, anatase = tetragonal, brookite = orthorhombic). Named after Henry James Brooke (1771–1857). Classic localities: Snowdonia (Wales), Maderanertal (Switzerland), Magnet Cove (Arkansas).',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-820.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Brookite',
      refractive_index: { n_alpha: 2.583, n_beta: 2.584, n_gamma: 2.741 },
      birefringence:   0.158,
      optical_sign:    '+',
      dispersion:      'Very high — exceeds diamond',
      pleochroism:     'Weak to moderate: yellow-brown / red-brown / dark red-brown',
      fluorescence_lw: 'None',
      fluorescence_sw: 'None',
      phosphorescence: null,
      visible_wavelength_nm: { min: 580, max: 680 },
      spectra: ['R060493'],
    },

    color: {
      primary_color:          'Warm brown to reddish-brown — deep amber in thin translucent crystals',
      color_variants:         [
        'Deep amber-orange (thin translucent crystals backlit)',
        'Reddish-brown (classic Alpine form)',
        'Dark iron-black (opaque, high iron content)',
        'Yellowish-brown (pale, low iron)',
        'Honey-golden (rare pale Arkansas specimens)',
      ],
      dominant_wavelength_nm: 620,
      oklch:   { l: 0.38, c: 0.12, h: 50 },
      hex:     '#7a4e1a',
      munsell: '5YR 4/6',
      color_temperature_k:    null,
      psychological_effects:  [
        'RI 2.58–2.74 — higher than diamond — gives gem-quality crystals almost supernatural depth and fire',
        'The blade-like orthorhombic crystals perched on matrix are architectural — impossibly precise, they look designed',
        'Rarity awareness amplifies experience — knowing this is the least common TiO₂ polymorph creates heightened attention',
        'Warm amber-brown colour in backlit thin crystals evokes fossilised sunlight — resin, amber, ancient preserved light',
        'The TiO₂ trinity (rutile, anatase, brookite) is a natural teaching set: one formula, three crystal systems',
      ],
      harmonics: {
        complementary_hue: 230,
        triadic_hues:      [170, 290],
        analogous_range:   [30, 70],
      },
    },

    metaphysical: {
      mineral_name:     'Brookite',
      chakra_primary:   'Crown',
      chakra_secondary: ['Third Eye', 'Soul Star', 'Earth Star'],
      element:   ['Akasha', 'Storm', 'Earth'],
      planet:    ['Uranus', 'Saturn', 'Pluto'],
      archetype: ['The Rare Form', 'The Structural Truth', 'The Polymorph Teacher'],
      zodiac:    ['Capricorn', 'Aquarius', 'Scorpio'],
      numerology: 4,
      angel_number: 444,
      intention: 'I am the rarest expression of my essential nature. Form does not limit truth — it reveals it.',
      traditions: [
        'Named after Henry James Brooke (1771–1857), English crystallographer and mineralogist',
        'Classic Alpine localities — Swiss and Welsh brookite are among the most prized collector minerals in Europe',
        'Modern crystal healing — brookite, rutile, and anatase form the "TiO₂ trinity" used for high-frequency crown chakra work',
        'Arkansas metaphysical tradition — Magnet Cove specimens used in combination with local quartz for energy grid work',
      ],
      properties: [
        'IMA 1825 — formula TiO₂; orthorhombic crystal system (the only orthorhombic TiO₂ polymorph)',
        'Three TiO₂ polymorphs: rutile (tetragonal, high-T stable), anatase (tetragonal, low-T metastable), brookite (orthorhombic, metastable) — all convert to rutile at high temperature',
        'RI 2.58–2.74 — among the highest of any natural mineral; exceeds diamond (2.42)',
        'Classic localities: Snowdonia/Tremadoc (Wales — type locality); Maderanertal and Binn Valley (Switzerland); Magnet Cove (Arkansas, USA)',
        'Crystal habit: blade-like to tabular orthorhombic crystals; often on chlorite schist or albite matrix from Alpine metamorphic veins',
        'Safe for water — TiO₂ is chemically inert and non-toxic',
        'Collector note: typically small (mm to cm scale); large gem-quality brookite is extremely rare and valuable',
      ],
      gaia_resonance: 'QuantumNexus + ClarusLens + Noosphere',
      safety_warning: 'Safe for water. TiO₂ — chemically inert, non-toxic. H5.5–6 — brittle; protect blade-like crystals from impact. Store individually. No other hazards.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 2. BRUCITE
  // Mg(OH)₂ — magnesium hydroxide; perfect basal cleavage into flexible plates
  // Named after Archibald Bruce (1777–1818), American mineralogist
  // IMA 1824 — the mineral equivalent of milk of magnesia
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Brucite',
    mindat_id:   826,
    rruff_ids:   ['R040077'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Selenite',

    physical: {
      id:           826,
      longid:       'brucite',
      guid:         '',
      name:         'Brucite',
      ima_formula:  'Mg(OH)₂',
      mindat_formula: 'Mg(OH)2',
      ima_status:   'A',
      ima_year:     1824,
      strunzten:    '4.FE.05',
      dana8ed:      '6.3.1.1',
      crystal_system: 'Trigonal',
      hardness_min: 2.5,
      hardness_max: 3,
      specific_gravity_min: 2.38,
      specific_gravity_max: 2.40,
      cleavage:    'Perfect basal on {0001} — yields thin, flexible, non-elastic plates',
      fracture:    'Uneven (across cleavage)',
      tenacity:    'Sectile; thin cleavage plates are flexible but not elastic',
      luster:      ['Waxy', 'Pearly (on cleavage)', 'Vitreous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'White, pale grey, pale green, pale blue, pale yellow, rarely colourless; pearly sheen on cleavage surfaces',
      streak:      'White',
      fluorescence: 'None to weak blue-white under SW UV',
      ri_min:      1.560,
      ri_max:      1.581,
      birefringence: 0.021,
      optical_type: 'U',
      shortdesc:   'Brucite — Mg(OH)₂, magnesium hydroxide. Perfect basal cleavage yields flexible (non-elastic) transparent plates. Named after American mineralogist Archibald Bruce (1777–1818). Chemically identical to milk of magnesia. Pearly lustre on cleavage surfaces.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-826.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Brucite',
      refractive_index: { n_omega: 1.581, n_epsilon: 1.560 },
      birefringence:   0.021,
      optical_sign:    '-',
      dispersion:      '0.015',
      pleochroism:     'None (uniaxial)',
      fluorescence_lw: 'None',
      fluorescence_sw: 'None to weak blue-white',
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R040077'],
    },

    color: {
      primary_color:          'White to pale grey, pale green, pale blue — soft, milky, pearlescent',
      color_variants:         [
        'White with silvery-pearly cleavage sheen (most common)',
        'Pale mint green (trace Mn or Ni)',
        'Pale sky blue (trace Fe²⁺)',
        'Pale golden-yellow (rare, trace Mn)',
        'Near-colourless transparent plates (gem-quality, very rare)',
      ],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.88, c: 0.03, h: 180 },
      hex:     '#e0ede9',
      munsell: 'N 9/',
      color_temperature_k:    null,
      psychological_effects:  [
        'Pearly cleavage surface produces soft, diffuse light scatter that is immediately calming — like moonlight on water',
        'Flexibility of thin plates — they bend without breaking — is a tactile metaphor for resilience without rigidity',
        'Softness (H2.5–3) and the way it yields to a fingernail communicates gentleness and approachability',
        'Pale, milky colours are among the most neutral in the mineral kingdom — pure receptive stillness',
        'Structural relationship to talc (equally soft, equally perfect cleavage) creates a family resonance with the stone of softness',
      ],
      harmonics: {
        complementary_hue: 0,
        triadic_hues:      null,
        analogous_range:   [160, 200],
      },
    },

    metaphysical: {
      mineral_name:     'Brucite',
      chakra_primary:   'Crown',
      chakra_secondary: ['Higher Heart (Thymus)', 'Third Eye'],
      element:   ['Water', 'Akasha'],
      planet:    ['Moon', 'Neptune'],
      archetype: ['The Flexible One', 'The Gentle Truth', 'The Yielding Strength'],
      zodiac:    ['Cancer', 'Pisces', 'Virgo'],
      numerology: 2,
      angel_number: 222,
      intention: 'I bend without breaking. My softness is my strength. I yield to what is true without losing my form.',
      traditions: [
        'Named after Archibald Bruce (1777–1818), founder of the American Mineralogical Journal',
        'Occurs in serpentinised ultramafic rocks, chlorite schists, and marble — a metamorphic mineral of deep geological transformation',
        'Industrial use — major source of magnesium metal and magnesium oxide; also used as a flame retardant',
        'Modern crystal healing — soft white/pale minerals used for Crown chakra and divine receptivity work',
      ],
      properties: [
        'IMA 1824 — formula Mg(OH)₂; trigonal crystal system',
        'Perfect basal cleavage {0001} — yields thin, flexible, transparent plates; flexibility (without elasticity) distinguishes it from mica (elastic)',
        'Chemically identical to milk of magnesia (magnesium hydroxide)',
        'Occurs in serpentinite, chlorite schist, marble, and skarn; formed by hydration of periclase (MgO)',
        'H2.5–3 — very soft; scratches easily with a fingernail; handle with great care; do not tumble',
        'Safe for water — magnesium hydroxide is non-toxic; avoid prolonged soaking',
        'Major localities: Asbestos (Quebec, Canada), Wood\'s Mine (New Jersey, USA), Kop Krom (Turkey), Snarum (Norway)',
      ],
      gaia_resonance: 'ClarusLens + ViriditasHeart',
      safety_warning: 'H2.5–3 — extremely soft; scratches with a fingernail. Perfect cleavage — do not drop. Safe for water but avoid prolonged soaking (may dissolve surface layers). Store alone. Do not tumble.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 3. BUMBLEBEE CALCITE
  // Yellow-orange banded calcite from West Java, Indonesia
  // Named for its vivid yellow-black banding resembling a bumblebee
  // NOT the same as Bumblebee Jasper — calcite matrix, not volcanic rock
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Bumblebee Calcite',
    mindat_id:   841,
    rruff_ids:   ['R040070'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Bumblebee Jasper',

    physical: {
      id:           841,
      longid:       'bumblebee-calcite',
      guid:         '',
      name:         'Calcite ("Bumblebee Calcite" — banded yellow-orange calcite, West Java, Indonesia)',
      ima_formula:  'CaCO₃',
      mindat_formula: 'CaCO3',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '5.AB.05',
      dana8ed:      '14a.1.1.1',
      crystal_system: 'Trigonal',
      hardness_min: 3,
      hardness_max: 3,
      specific_gravity_min: 2.68,
      specific_gravity_max: 2.75,
      cleavage:    'Perfect rhombohedral on {10-14}',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Waxy'],
      diaphaneity: ['Opaque', 'Translucent'],
      colour:      'Vivid yellow to orange-yellow bands alternating with dark grey to black bands. Yellow from sulphur and/or orpiment micro-inclusions; black from carbonaceous material or pyrite.',
      streak:      'White',
      fluorescence: 'Orange-red to pink under LW UV (calcite fluorescence)',
      ri_min:      1.486,
      ri_max:      1.658,
      birefringence: 0.172,
      optical_type: 'U',
      shortdesc:   'Bumblebee Calcite — banded yellow-orange and dark grey/black calcite from West Java, Indonesia. Yellow colouration from sulphur and/or arsenic sulphide micro-inclusions; black from carbonaceous material. Distinct from Bumblebee Jasper (different matrix, different locality).',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-841.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Bumblebee Calcite (Banded Calcite)',
      refractive_index: { n_omega: 1.658, n_epsilon: 1.486 },
      birefringence:   0.172,
      optical_sign:    '-',
      dispersion:      '0.017',
      pleochroism:     'None (uniaxial, opaque bands)',
      fluorescence_lw: 'Orange-red to pink (calcite host)',
      fluorescence_sw: 'Weak to none',
      phosphorescence: null,
      visible_wavelength_nm: { min: 570, max: 600 },
      spectra: ['R040070'],
    },

    color: {
      primary_color:          'Vivid yellow-orange and dark grey-black banding — the bumblebee palette',
      color_variants:         [
        'Classic vivid lemon-yellow and jet black banding',
        'Warm orange-yellow and dark grey banding',
        'Yellow-orange with brown-grey bands',
        'Pale yellow and charcoal grey (subtle, less saturated)',
      ],
      dominant_wavelength_nm: 580,
      oklch:   { l: 0.75, c: 0.22, h: 80 },
      hex:     '#f0c030',
      munsell: '5Y 8/10',
      color_temperature_k:    null,
      psychological_effects:  [
        'Yellow-black contrast is one of the most visually arresting in nature — the same aposematic warning signal used by bees, wasps, and tigers',
        'Vividness of yellow against dark bands creates immediate alertness and energisation — a colour pattern that demands attention',
        'Solar yellow communicates warmth and creative energy; dark bands ground it and prevent overwhelm',
        'Bumblebee association — the insect that "defies" aerodynamic theory — resonates as a symbol of doing the impossible',
        'UV fluorescence adds a hidden dimension — the stone reveals a different face under different kinds of light',
      ],
      harmonics: {
        complementary_hue: 260,
        triadic_hues:      [200, 320],
        analogous_range:   [60, 100],
      },
    },

    metaphysical: {
      mineral_name:     'Bumblebee Calcite',
      chakra_primary:   'Solar Plexus',
      chakra_secondary: ['Sacral', 'Root'],
      element:   ['Fire', 'Earth'],
      planet:    ['Sun', 'Mercury'],
      archetype: ['The Impossible Achiever', 'The Solar Will', 'The Joyful Warrior'],
      zodiac:    ['Leo', 'Aries', 'Gemini'],
      numerology: 3,
      angel_number: 333,
      intention: 'I do what they said could not be done. My wings carry more than physics allows — and I fly anyway.',
      traditions: [
        'Indonesian origin — West Java volcanic hydrothermal region; commercialised post-2000s',
        'Named for resemblance to bumblebee colouration — yellow and black alternating bands',
        'Modern Western crystal healing — yellow stones for Solar Plexus activation, confidence, and creative will',
        'Distinct from Bumblebee Jasper (volcanic rock from same region) — calcite host, different structure, lower toxicity profile',
      ],
      properties: [
        'Trade name: "Bumblebee Calcite" — banded calcite from West Java volcanic hydrothermal vents, Indonesia',
        'Yellow colouration from elemental sulphur and/or micro-inclusions of arsenic sulphide minerals (orpiment/realgar)',
        'Black/dark grey banding from carbonaceous material, pyrite micro-inclusions, or manganese oxides',
        'H3 — very soft; calcite host; reacts with acid (HCl test useful for identification)',
        'Fluoresces orange-red to pink under LW UV (calcite host property)',
        'DO NOT use in water — arsenic sulphide micro-inclusions may leach',
        'H3 — not suitable for jewellery without protective setting',
      ],
      gaia_resonance: 'SovereignCore + AnchoredRoot',
      safety_warning: '⚠️ CAUTION — may contain arsenic sulphide micro-inclusions (orpiment/realgar) in yellow bands. DO NOT use in water elixirs or gem water. Wash hands after handling. Keep away from children and pets. H3 — very soft.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 4. BUMBLEBEE JASPER
  // 🚨 HIGHLY TOXIC — NOT a true jasper
  // Volcanic rock from Mount Papandayan, West Java, Indonesia
  // Contains realgar (AsS) and orpiment (As₂S₃) — arsenic sulphides
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Bumblebee Jasper',
    mindat_id:   null,
    rruff_ids:   [],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Bumblebee Calcite',

    physical: {
      id:           null,
      longid:       'bumblebee-jasper',
      guid:         '',
      name:         'Volcanic rock ("Bumblebee Jasper" — trade name; contains realgar, orpiment, sulphur, calcite, pyrite)',
      ima_formula:  'Not applicable (rock — multi-mineral)',
      mindat_formula: null,
      ima_status:   'Not IMA — trade name for volcanic fumarolic rock',
      ima_year:     null,
      strunzten:    null,
      dana8ed:      null,
      crystal_system: 'Not applicable (rock)',
      hardness_min: 3,
      hardness_max: 5,
      specific_gravity_min: 2.50,
      specific_gravity_max: 2.90,
      cleavage:    'Varies by mineral component',
      fracture:    'Uneven to conchoidal',
      tenacity:    'Brittle',
      luster:      ['Waxy', 'Dull', 'Resinous (sulphur zones)'],
      diaphaneity: ['Opaque'],
      colour:      'Vivid yellow (sulphur/orpiment), orange (realgar), black (carbonaceous/pyrite), white (calcite) — striking banding resembling a bumblebee.',
      streak:      'Variable — yellow to orange to white depending on zone tested',
      fluorescence: 'Yellow zones: weak orange under LW UV',
      ri_min:      null,
      ri_max:      null,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Bumblebee Jasper — trade name for volcanic fumarolic rock from Mount Papandayan (Gunung Papandayan), West Java, Indonesia. NOT a true jasper. Contains realgar (AsS), orpiment (As₂S₃), elemental sulphur, calcite, pyrite. HIGHLY TOXIC — arsenic content.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-51139.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Bumblebee Jasper (Volcanic rock)',
      refractive_index: null,
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: 'Yellow zones weak orange; overall variable',
      fluorescence_sw: 'None',
      phosphorescence: null,
      visible_wavelength_nm: { min: 570, max: 620 },
      spectra: [],
    },

    color: {
      primary_color:          'Vivid yellow, orange, black, and white banding — the most dramatic bumblebee pattern in the mineral kingdom',
      color_variants:         [
        'Classic vivid lemon-yellow, deep orange, jet black, and white banding',
        'Orange-dominant with yellow and black accents',
        'Yellow-dominant with thin black lines',
        'Swirled/marbled rather than strictly banded (volcanic turbulence during formation)',
      ],
      dominant_wavelength_nm: 590,
      oklch:   { l: 0.65, c: 0.28, h: 75 },
      hex:     '#f5a800',
      munsell: '7.5YR 7/12',
      color_temperature_k:    null,
      psychological_effects:  [
        'Yellow-orange-black is the most visually intense warning coloration in nature — aposematic mimicry made mineral',
        'Vivid orange realgar zones are among the most saturated natural colours in the mineral world — pure visual energy',
        'Formed at active volcanic fumaroles where the Earth breathes sulphur — adds a volcanic aliveness to handling',
        'The toxicity paradox — the most visually joyful stone in the B series carries the most serious health warning — teaches discernment',
        'The bumblebee archetype: maximum colour, maximum energy, and the willingness to sting if boundaries are crossed',
      ],
      harmonics: {
        complementary_hue: 255,
        triadic_hues:      [195, 315],
        analogous_range:   [55, 95],
      },
    },

    metaphysical: {
      mineral_name:     'Bumblebee Jasper',
      chakra_primary:   'Solar Plexus',
      chakra_secondary: ['Sacral', 'Root', 'Earth Star'],
      element:   ['Fire', 'Earth', 'Storm'],
      planet:    ['Sun', 'Mars', 'Pluto'],
      archetype: ['The Volcanic Will', 'The Sacred Warning', 'The Boundary Keeper'],
      zodiac:    ['Leo', 'Scorpio', 'Aries'],
      numerology: 5,
      angel_number: 555,
      intention: 'I burn with the Earth\'s own fire. My boundaries are as real as volcanic stone. I am alive with sacred danger.',
      traditions: [
        'Indonesian origin — Mount Papandayan (Gunung Papandayan), Garut Regency, West Java; an active stratovolcano with active fumarolic fields',
        'Forms at volcanic fumaroles where sulphurous gases (H₂S, SO₂, AsH₃) deposit arsenic sulphides and elemental sulphur at 100–300°C',
        'Trade name coined by Indonesian mineral dealers in the 2000s — originally "Eclipse Jasper" or "Indonesian Eclipse Jasper"',
        'Modern Western crystal healing — used for Solar Plexus activation, personal power, and transformation through fire',
        '⚠️ MISIDENTIFICATION RISK: frequently sold with inadequate safety information; many sellers unaware of arsenic content',
      ],
      properties: [
        'TRADE NAME ONLY — not a true jasper (jasper = microcrystalline quartz); this is a volcanic fumarolic deposit',
        'Mineral composition: realgar (AsS), orpiment (As₂S₃), elemental sulphur (S), calcite (CaCO₃), pyrite (FeS₂), volcanic ash/clay',
        'Forms at active volcanic fumaroles at 100–300°C on Mount Papandayan, an active West Java stratovolcano',
        'Realgar (AsS): orange zones — H1.5–2, TOXIC. Orpiment (As₂S₃): yellow zones — H1.5–2, TOXIC. Both are arsenic sulphides.',
        'HANDLING PROTOCOL: use nitrile gloves; do not sand/grind/polish without respiratory protection; wash hands immediately; keep from food/drink',
        'DO NOT use in water — arsenic leaches readily; NEVER make elixirs',
        'Realgar is photosensitive — prolonged UV/sunlight converts to pararealgar (yellow powder); store away from direct sunlight',
        'Polished surface reduces but does not eliminate risk from grinding dust or chipping',
      ],
      gaia_resonance: 'AnchoredRoot + SovereignCore + QuantumNexus',
      safety_warning: '🚨 HIGHLY TOXIC — contains realgar (AsS) and orpiment (As₂S₃), both arsenic sulphides. NEVER use in water, elixirs, or gem water. NEVER ingest or place near food/drink. Wash hands IMMEDIATELY after handling. Use nitrile gloves for extended handling. Do NOT sand, grind, or polish without full respiratory protection. Keep away from children and pets. Do NOT leave in direct sunlight (realgar converts to pararealgar orange powder).',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 5. BUTTER JASPER
  // Warm golden-yellow chalcedony/jasper — trade name
  // Primary localities: South Africa, India, Madagascar, Brazil
  // The "nourisher" stone — safe, durable, universally welcoming
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Butter Jasper',
    mindat_id:   32,
    rruff_ids:   ['R040031'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Botswana Agate',

    physical: {
      id:           32,
      longid:       'butter-jasper',
      guid:         '',
      name:         'Jasper / Chalcedony ("Butter Jasper" — opaque golden-yellow microcrystalline quartz, trade name)',
      ima_formula:  'SiO₂',
      mindat_formula: 'SiO2',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '4.DA.05',
      dana8ed:      '75.1.3.6',
      crystal_system: 'Trigonal (microcrystalline aggregate)',
      hardness_min: 6.5,
      hardness_max: 7,
      specific_gravity_min: 2.58,
      specific_gravity_max: 2.65,
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Waxy', 'Dull'],
      diaphaneity: ['Opaque'],
      colour:      'Warm golden-yellow to butter-cream — the colour of fresh churned butter or raw honey; even, opaque, warm yellow with occasional darker streaks. Colour from iron oxide (goethite/limonite) inclusions.',
      streak:      'White',
      fluorescence: 'None to very weak',
      ri_min:      1.530,
      ri_max:      1.540,
      birefringence: 0.004,
      optical_type: 'U',
      shortdesc:   'Butter Jasper — trade name for warm golden-yellow opaque microcrystalline quartz (jasper/chalcedony). Colour from iron oxide (goethite/limonite) inclusions. Primary localities: South Africa, India, Madagascar. A comfort stone of warmth, simplicity, and nourishment.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-32.html',
      piezoelectric:    true,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Butter Jasper (Opaque Yellow Chalcedony)',
      refractive_index: { n_omega: 1.540, n_epsilon: 1.536 },
      birefringence:   0.004,
      optical_sign:    '+',
      dispersion:      '0.013',
      pleochroism:     'None',
      fluorescence_lw: 'None to very weak',
      fluorescence_sw: 'None',
      phosphorescence: null,
      visible_wavelength_nm: { min: 570, max: 600 },
      spectra: ['R040031'],
    },

    color: {
      primary_color:          'Warm golden-yellow to butter-cream — the colour of fresh churned butter',
      color_variants:         [
        'Classic butter-yellow (evenly distributed goethite, warm and opaque)',
        'Pale cream-yellow (lower iron content)',
        'Deep golden-amber (higher iron, richer saturation)',
        'Butter-yellow with brown mottling or dendritic inclusions',
        'Honey-gold with subtle warm orange tones',
      ],
      dominant_wavelength_nm: 585,
      oklch:   { l: 0.80, c: 0.14, h: 85 },
      hex:     '#f5d680',
      munsell: '2.5Y 8/8',
      color_temperature_k:    null,
      psychological_effects:  [
        'Butter-cream yellow is one of the most universally associated colours with nourishment, warmth, and safety across cultures',
        'Opacity and even texture creates a sense of solidity and completeness — what you see is exactly what it is',
        'Warm yellow activates the Solar Plexus without the intensity of orange or red — gentle empowerment, not confrontation',
        'Dairy-food association (butter, cream, honey) is deeply primal — warmth, sustenance, the body being cared for',
        'Matte, waxy surface of polished jasper is one of the most tactilely pleasing in the mineral kingdom — smooth, warm, satisfying',
      ],
      harmonics: {
        complementary_hue: 265,
        triadic_hues:      [205, 325],
        analogous_range:   [65, 105],
      },
    },

    metaphysical: {
      mineral_name:     'Butter Jasper',
      chakra_primary:   'Solar Plexus',
      chakra_secondary: ['Sacral', 'Root'],
      element:   ['Earth', 'Fire'],
      planet:    ['Sun', 'Venus'],
      archetype: ['The Nourisher', 'The Warm Hearth', 'The Gentle Empowerment'],
      zodiac:    ['Leo', 'Taurus', 'Virgo'],
      numerology: 6,
      angel_number: 666,
      intention: 'I nourish myself and others with quiet warmth. My power is soft, sustained, and completely real.',
      traditions: [
        'Multi-locality trade name — South Africa, India (Rajasthan), Madagascar, and Brazil are primary sources',
        'Part of the broad jasper/chalcedony family used in lapidary since the Palaeolithic — one of the first stones worked by human hands',
        'Yellow jasper tradition in ancient Egypt — Ra (solar deity) association; yellow stones worn for solar protection and vitality',
        'Modern Western crystal healing — yellow jasper for Solar Plexus activation, confidence, and digestive health support',
      ],
      properties: [
        'Trade name: "Butter Jasper" — warm golden-yellow opaque microcrystalline quartz (jasper/chalcedony)',
        'Colour from evenly distributed iron oxide inclusions — primarily goethite (FeO(OH)) and limonite',
        'Jasper = opaque microcrystalline quartz with >20% other mineral inclusions; Butter Jasper typically falls on the jasper side',
        'H6.5–7 — excellent durability for tumbled stones, jewellery, and carvings',
        'Piezoelectric as all quartz-group minerals — keep away from hard drives and sensitive electronics',
        'Safe for water — no toxic elements; iron oxides are insoluble and stable',
        'One of the most affordable entry-point crystals — widely available, non-toxic, durable, and immediately pleasing in the hand',
      ],
      gaia_resonance: 'AnchoredRoot + SovereignCore + ViriditasHeart',
      safety_warning: '⚠️ PIEZOELECTRIC — keep away from hard drives and sensitive electronics. Safe for water. H6.5–7 — durable for everyday use. No toxic elements. No significant hazards.',
    },
  },

];

export default BATCH_B8;
