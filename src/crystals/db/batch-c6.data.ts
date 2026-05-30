/**
 * src/crystals/db/batch-c6.data.ts
 * GAIA-OS Crystal Database — Batch C-6
 *
 * Entries:
 *   1. Citrine          — Fe³⁺-bearing quartz; yellow to orange; mostly heat-treated
 *   2. Cobaltite        — CoAsS; cobalt arsenide sulphide — TOXIC
 *   3. Cobalto-Calcite  — Co-bearing calcite; hot pink — TOXIC
 *   4. Copal            — subfossil tree resin; trade name; proto-amber
 *   5. Copper (Native)  — Cu; native element copper — TOXIC in water
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-30
 *
 * SAFETY NOTE: Cobaltite (Co+As), Cobalto-Calcite (Co), and Native Copper are
 * toxic in water. Cobaltite contains arsenic — handle with care.
 * Copal is organic resin — not a mineral; trade_name: true.
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_C6: CrystalRecord[] = [

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 1. CITRINE
  // SiO₂ with Fe³⁺ colour centres — trigonal
  // Named from French citron (lemon)
  // Natural citrine rare; most market citrine = heat-treated amethyst or smoky quartz
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {
    name:         'Citrine',
    mindat_id:    1062,
    rruff_ids:    ['R050125'],
    last_synced:  '2026-05-30T00:00:00Z',
    trade_name:   false,
    color_layer:  'natural',
    yin_yang_pair: 'Amethyst',

    physical: {
      id:           1062,
      longid:       'citrine',
      guid:         '',
      name:         'Citrine (Fe³⁺-bearing quartz — SiO₂)',
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
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Pale lemon-yellow to deep golden-orange to reddish-orange (Madeira citrine). Colour from Fe³⁺ colour centres. Natural citrine is pale yellow; deep orange-red "citrine" is almost always heat-treated amethyst or smoky quartz. Colour fades with prolonged UV exposure.',
      streak:      'White',
      fluorescence: 'None to weak',
      ri_min:      1.544,
      ri_max:      1.553,
      birefringence: 0.009,
      optical_type: 'U',
      shortdesc:   'Citrine — Fe³⁺-bearing quartz (SiO₂). Yellow to golden-orange; colour from Fe³⁺ colour centres. Named from French citron. Natural citrine is pale yellow and rare; most market citrine (especially deep orange "Madeira" or "Spanish" citrine) is heat-treated amethyst or smoky quartz. Piezoelectric.',
      updttime:    '2026-05-30T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-1062.html',
      piezoelectric:     true,
      safe_for_water:    true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Citrine',
      refractive_index: { n_omega: 1.553, n_epsilon: 1.544 },
      birefringence:   0.009,
      optical_sign:    '+',
      dispersion:      '0.013',
      pleochroism:     'Weak: pale yellow / yellow',
      fluorescence_lw: 'None to weak',
      fluorescence_sw: 'None',
      phosphorescence: null,
      visible_wavelength_nm: { min: 570, max: 590 },
      spectra: ['R050125'],
    },

    color: {
      primary_color:         'Pale lemon-yellow to deep golden-orange — sunlight held in quartz',
      color_variants: [
        'Pale lemon-yellow (natural citrine — rare and most mineralogically authentic)',
        'Golden-yellow (moderate Fe³⁺ or mild heat treatment)',
        'Deep amber-orange (Madeira citrine — almost always heat-treated amethyst)',
        'Reddish-orange (Spanish citrine — heavily heat-treated)',
        'Smoky-yellow (ametrine border zones)',
        'Bicolour purple-yellow (ametrine — amethyst + citrine in one crystal, Bolivia)',
      ],
      dominant_wavelength_nm: 580,
      oklch:   { l: 0.78, c: 0.22, h: 85 },
      hex:     '#f0c040',
      munsell: '2.5Y 8/10',
      color_temperature_k: 5500,
      psychological_effects: [
        'Yellow-gold is the colour of sunlight and warmth — one of the most universally positive colour associations across cultures',
        'The transparency of citrine means the colour is luminous rather than surface — light passes through and is transformed',
        'Natural pale yellow citrine has a delicacy that deep orange market citrine lacks — the authentic colour rewards knowledge of the mineral',
        'Ametrine (purple + yellow in one crystal) is a natural demonstration of the amethyst-citrine relationship and the Fe²⁺/Fe³⁺ colour centre duality',
        'The heat-treatment awareness creates a teaching moment: most of what is sold as citrine is transformed amethyst — both are real, but different',
      ],
      harmonics: {
        complementary_hue: 265,
        triadic_hues:      [205, 325],
        analogous_range:   [65, 105],
      },
    },

    metaphysical: {
      mineral_name:     'Citrine',
      chakra_primary:   'Solar Plexus',
      chakra_secondary: ['Sacral', 'Crown'],
      element:   ['Fire', 'Air'],
      planet:    ['Sun', 'Jupiter', 'Mercury'],
      archetype: ['The Merchant\'s Stone', 'The Sun\'s Quartz', 'The Golden Will'],
      zodiac:    ['Leo', 'Aries', 'Libra', 'Gemini'],
      numerology: 6,
      angel_number: 666,
      intention: 'I hold the light that does not fade. My will is warm and clear like afternoon sun through amber.',
      traditions: [
        'Named from French citron (lemon) — for its lemon-yellow colour; known as a gem since antiquity',
        'Ancient Rome — yellow quartz (likely citrine and yellow smoky quartz) used for intaglios and cameos',
        'Art Deco — citrine became extremely fashionable in the 1920s–30s; large step-cut citrines in platinum and gold settings',
        'The "Merchant\'s Stone" — modern crystal healing tradition associates citrine with abundance, manifestation, and prosperity',
        'Heat treatment tradition — recognised since the 19th century that heating amethyst/smoky quartz produces citrine colour; modern market is almost entirely heat-treated',
      ],
      properties: [
        'Fe³⁺-bearing quartz (SiO₂) — colour from Fe³⁺ colour centres in the crystal lattice',
        'Natural citrine is pale yellow and rare; most market citrine = heat-treated amethyst (was purple → orange-red) or smoky quartz (was grey-brown → yellow)',
        'Ametrine: natural bicolour crystal with amethyst (Fe²⁺, purple) and citrine (Fe³⁺, yellow) zones — primary source Anahi Mine, Bolivia',
        'Colour fades with prolonged direct UV/sunlight — store away from strong light',
        'Piezoelectric — keep away from hard drives and sensitive electronics',
        'Safe for water — SiO₂; chemically stable; no toxic elements',
        'Major localities: Brazil (Minas Gerais, Rio Grande do Sul), Bolivia (ametrine — Anahi Mine), Madagascar, Spain, USA (natural pale citrine)',
      ],
      gaia_resonance: 'SovereignCore + ClarusLens + ViriditasHeart',
      safety_warning:  '⚠️ PIEZOELECTRIC — keep away from hard drives and sensitive electronics. Safe for water. Keep out of prolonged direct sunlight — colour may fade. No toxic elements.',
    },
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 2. COBALTITE
  // CoAsS — cobalt arsenide sulphide; orthorhombic (pseudo-cubic)
  // Named for cobalt content
  // Primary cobalt ore; metallic silver-grey with red tint; TOXIC (As)
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {
    name:         'Cobaltite',
    mindat_id:    1071,
    rruff_ids:    ['R061014'],
    last_synced:  '2026-05-30T00:00:00Z',
    trade_name:   false,
    color_layer:  'natural',
    yin_yang_pair: 'Skutterudite',

    physical: {
      id:           1071,
      longid:       'cobaltite',
      guid:         '',
      name:         'Cobaltite',
      ima_formula:  'CoAsS',
      mindat_formula: 'CoAsS',
      ima_status:   'A',
      ima_year:     1832,
      strunzten:    '2.EB.05',
      dana8ed:      '2.12.1.1',
      crystal_system: 'Orthorhombic (pseudo-cubic habit)',
      hardness_min: 5.5,
      hardness_max: 6,
      specific_gravity_min: 6.10,
      specific_gravity_max: 6.40,
      cleavage:    'Perfect cubic on {100}, {010}, {001}',
      fracture:    'Uneven',
      tenacity:    'Brittle',
      luster:      ['Metallic'],
      diaphaneity: ['Opaque'],
      colour:      'Silver-grey to tin-white with a reddish or violet tint on fresh surfaces. Metallic lustre. Tarnishes to pinkish-violet on exposure. Streak: greyish-black.',
      streak:      'Greyish-black',
      fluorescence: 'None',
      ri_min:      null,
      ri_max:      null,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Cobaltite — CoAsS, orthorhombic cobalt arsenide sulphide. TOXIC (arsenic + cobalt). IMA 1832. Primary cobalt ore. Silver-grey metallic with pink-violet tint. SG 6.1–6.4 — heavy. Pseudo-cubic crystal habit. Major localities: Tunaberg (Sweden), Cobalt (Ontario, Canada), Broken Hill (Australia).',
      updttime:    '2026-05-30T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-1071.html',
      piezoelectric:     false,
      safe_for_water:    false,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Cobaltite',
      refractive_index: null,
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: 'None',
      fluorescence_sw: 'None',
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R061014'],
    },

    color: {
      primary_color:         'Silver-grey metallic with a characteristic pink-violet tint — the cobalt blush',
      color_variants: [
        'Fresh silver-white metallic (freshly broken surface)',
        'Silver-grey with pink-violet tint (most common — characteristic cobalt blush)',
        'Pinkish-violet tarnish (oxidised surface)',
        'Tin-white (low tarnish specimens)',
      ],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.55, c: 0.08, h: 310 },
      hex:     '#8a7a9a',
      munsell: '5P 5/4',
      color_temperature_k: null,
      psychological_effects: [
        'The pink-violet tint on a metallic silver ground is an unusual combination — simultaneously industrial and delicate',
        'The pseudo-cubic crystal habit creates perfectly geometric forms in a metallic mineral — nature\'s precision engineering at small scale',
        'SG 6.1–6.4 gives a density that immediately communicates substance — this is a heavy, concentrated mineral',
        'The cobalt connection links this mineral to the entire history of blue pigment — cobalt blue, smalt, and the blue of porcelain all come from cobalt chemistry',
        'Cobalt is named after the Kobold (German gnome/goblin) — miners blamed the mischievous spirits when cobalt ore yielded no copper and made workers ill',
      ],
      harmonics: {
        complementary_hue: 130,
        triadic_hues:      [70, 190],
        analogous_range:   [290, 330],
      },
    },

    metaphysical: {
      mineral_name:     'Cobaltite',
      chakra_primary:   'Third Eye',
      chakra_secondary: ['Crown', 'Root'],
      element:   ['Metal', 'Earth', 'Fire'],
      planet:    ['Saturn', 'Mars', 'Uranus'],
      archetype: ['The Kobold Ore', 'The Blue Metal', 'The Industrial Gnome'],
      zodiac:    ['Capricorn', 'Aquarius', 'Scorpio'],
      numerology: 4,
      angel_number: 444,
      intention: 'I am the ore the miners blamed the gnomes for. My cobalt built the blue of ten thousand porcelain vessels.',
      traditions: [
        'Kobold etymology — cobalt named from German Kobold (goblin/gnome); medieval miners blamed invisible spirits when cobalt arsenide ore yielded no copper and caused illness (arsenic poisoning)',
        'Swedish mining tradition — Tunaberg, Sweden was a major early source; cobalt mining drove early Swedish industrial chemistry',
        'Cobalt, Ontario (Canada) — the town of Cobalt named after cobaltite deposits discovered 1903 during railway construction; sparked a major mining rush',
        'Blue pigment lineage — cobalt from cobaltite was the source of smalt (cobalt blue glass pigment) used in European painting from the 15th century; also the source of cobalt blue (CoAl₂O₄) used since the 19th century',
        'Modern — cobalt from cobaltite and other Co minerals is essential for lithium-ion battery cathodes; one of the most strategically critical metals of the 21st century',
      ],
      properties: [
        'IMA 1832 — formula CoAsS; orthorhombic cobalt arsenide sulphide; pseudo-cubic habit',
        'TOXIC — contains arsenic (As) and cobalt (Co); DO NOT use in water; wash hands after handling',
        'Primary cobalt ore; also contains arsenic which is a co-product at some refineries',
        'SG 6.1–6.4 — very heavy; dense metallic feel',
        'H5.5–6 — moderate hardness; collector mineral',
        'Major localities: Tunaberg (Sweden), Cobalt (Ontario, Canada), Broken Hill (NSW, Australia), Bou Azzer (Morocco)',
      ],
      gaia_resonance: 'SovereignCore + AnchorPrism',
      safety_warning:  '🚨 TOXIC — cobalt arsenide sulphide. Contains ARSENIC. DO NOT use in water. Wash hands thoroughly after handling. Do not inhale dust. Keep away from children and food. Collector and display use only.',
    },
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 3. COBALTO-CALCITE (Cobaltoan Calcite)
  // Co-bearing calcite — CaCO₃ with Co²⁺ substituting Ca²⁺
  // Trade name commonly used; also called Cobaltoan Calcite (IMA preferred)
  // Vivid hot pink to rose-red; rhombohedral; Congo primary source
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {
    name:         'Cobalto-Calcite',
    mindat_id:    1050,
    rruff_ids:    ['R060499'],
    last_synced:  '2026-05-30T00:00:00Z',
    trade_name:   true,
    color_layer:  'natural',
    yin_yang_pair: 'Smithsonite (pink)',

    physical: {
      id:           1050,
      longid:       'cobalto-calcite',
      guid:         '',
      name:         'Cobaltoan Calcite (trade name: Cobalto-Calcite) — CaCO₃ with Co²⁺',
      ima_formula:  'Ca(Co)CO₃',
      mindat_formula: 'Ca(Co)CO3',
      ima_status:   'A (variety of calcite)',
      ima_year:     null,
      strunzten:    '5.AB.05',
      dana8ed:      '14.1.1.1',
      crystal_system: 'Trigonal (rhombohedral)',
      hardness_min: 3,
      hardness_max: 3,
      specific_gravity_min: 2.70,
      specific_gravity_max: 2.90,
      cleavage:    'Perfect rhombohedral on {10-14} — three directions; classic calcite cleavage',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Pearly (on cleavage)'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Vivid hot pink to rose-red to cerise; colour from Co²⁺ substituting Ca²⁺ in the calcite lattice. The most vivid natural pink of any carbonate mineral. Colour is stable and does not fade.',
      streak:      'White to pale pink',
      fluorescence: 'Strong red under LW UV; moderate red under SW UV',
      ri_min:      1.530,
      ri_max:      1.685,
      birefringence: 0.172,
      optical_type: 'U',
      shortdesc:   'Cobaltoan Calcite (Cobalto-Calcite) — CaCO₃ with Co²⁺ substitution. TOXIC (cobalt). Vivid hot pink to rose-red; the most vivid natural pink carbonate. Strong red UV fluorescence. Primary source: Katanga (Kolwezi), DRC. H3 — soft. Yin pair to pink Smithsonite.',
      updttime:    '2026-05-30T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-1050.html',
      piezoelectric:     false,
      safe_for_water:    false,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Cobaltoan Calcite',
      refractive_index: { n_omega: 1.685, n_epsilon: 1.530 },
      birefringence:   0.172,
      optical_sign:    '-',
      dispersion:      null,
      pleochroism:     'Moderate: deep pink / pale pink',
      fluorescence_lw: 'Strong red',
      fluorescence_sw: 'Moderate red',
      phosphorescence: null,
      visible_wavelength_nm: { min: 520, max: 560 },
      spectra: ['R060499'],
    },

    color: {
      primary_color:         'Vivid hot pink to rose-red — the most saturated natural pink in the carbonate mineral family',
      color_variants: [
        'Hot pink / cerise (high Co²⁺ — most prized)',
        'Rose pink (moderate Co²⁺)',
        'Pale baby pink (low Co²⁺)',
        'Pink-red (highest Co²⁺ concentration)',
        'Pink on white calcite matrix (typical display form)',
      ],
      dominant_wavelength_nm: 530,
      oklch:   { l: 0.62, c: 0.28, h: 355 },
      hex:     '#e0408a',
      munsell: '5RP 5/14',
      color_temperature_k: null,
      psychological_effects: [
        'Hot pink is one of the most emotionally activating colours in the visible spectrum — it reads as joy, vitality, and unconditional warmth',
        'The strong red UV fluorescence means cobalto-calcite transforms dramatically under UV light — a teaching in hidden dimensions',
        'The rhombohedral cleavage produces perfect parallelogram fragments — geometry as natural as the colour',
        'Co²⁺ in a calcite lattice is a single ion substitution producing this entire pink experience — chemistry made visible as joy',
        'The Congo origin (Kolwezi, Katanga) connects it to one of the most mineralogically rich and historically complex regions on Earth',
      ],
      harmonics: {
        complementary_hue: 175,
        triadic_hues:      [115, 235],
        analogous_range:   [335, 15],
      },
    },

    metaphysical: {
      mineral_name:     'Cobalto-Calcite',
      chakra_primary:   'Heart',
      chakra_secondary: ['Higher Heart (Thymus)', 'Crown', 'Sacral'],
      element:   ['Fire', 'Water', 'Akasha'],
      planet:    ['Venus', 'Moon', 'Neptune'],
      archetype: ['The Hot Pink Heart', 'The Congo Rose', 'The Joy Carbonate'],
      zodiac:    ['Taurus', 'Cancer', 'Libra'],
      numerology: 6,
      angel_number: 666,
      intention: 'My pink is not soft — it is vivid, alive, and unconditional. I am the joy that arrives before the question.',
      traditions: [
        'Katanga / Kolwezi, DRC — the world\'s primary source of gem-quality cobaltoan calcite; the copper-cobalt belt of the Congo Basin',
        'Modern crystal healing — introduced to Western markets primarily in the 1980s–90s alongside other Congolese minerals; rapidly became a premier Heart chakra stone',
        'Cobalt\'s cultural lineage — the Co²⁺ that colours this pink also colours cobalt blue glass, smalt pigment, and the blue of Meissen porcelain',
        'UV fluorescence — the strong red glow under UV is a striking demonstration of hidden energy; used in UV lamp demonstrations',
        'Named trade variants — "Cobalto-Calcite" is the crystal market name; mineralogically it is "cobaltoan calcite" or "cobaltian calcite"',
      ],
      properties: [
        'Trade name: Cobalto-Calcite — mineralogically "cobaltoan calcite"; CaCO₃ with Co²⁺ partially substituting Ca²⁺',
        'TOXIC — cobalt mineral; DO NOT use in water elixirs; cobalt compounds are toxic',
        'H3 — soft; scratches easily; handle with care; store separately from harder stones',
        'Strong red fluorescence under LW UV — one of the most vivid carbonate fluorescence responses',
        'Primary source: Kolwezi, Katanga, DRC — most market material from this single region',
        'Colour stable — does not fade in light (unlike some other pink minerals)',
        'Also found: Morocco, Spain, California (USA)',
      ],
      gaia_resonance: 'ViriditasHeart + QuantumNexus + ClarusLens',
      safety_warning:  '⚠️ TOXIC — cobalt-bearing carbonate. DO NOT use in water elixirs. Wash hands after handling. H3 — very soft; handle gently. Keep away from children and food.',
    },
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 4. COPAL
  // Subfossil tree resin — NOT a mineral; organic material
  // Trade name for young (thousands of years old) amber-like resin
  // Primarily from East Africa (Congo, Tanzania) and Colombia
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {
    name:         'Copal',
    mindat_id:    null,
    rruff_ids:    [],
    last_synced:  '2026-05-30T00:00:00Z',
    trade_name:   true,
    color_layer:  'natural',
    yin_yang_pair: 'Amber',

    physical: {
      id:           null,
      longid:       'copal',
      guid:         '',
      name:         'Copal (subfossil tree resin — NOT a mineral)',
      ima_formula:  'Not applicable — organic resin (poly-terpenoid)',
      mindat_formula: null,
      ima_status:   'Not IMA — organic material; not a mineral',
      ima_year:     null,
      strunzten:    null,
      dana8ed:      null,
      crystal_system: 'Amorphous (organic)',
      hardness_min: 1.5,
      hardness_max: 2,
      specific_gravity_min: 1.03,
      specific_gravity_max: 1.10,
      cleavage:    'None',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Resinous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Pale yellow to golden-yellow to orange-brown; clear to cloudy. Similar to amber but generally paler and clearer. Some Colombian copal has green or blue fluorescence. May contain insect or plant inclusions — younger than amber inclusions.',
      streak:      'White (powders white)',
      fluorescence: 'Variable: weak to moderate blue-white or green (LW UV); stronger than amber in some specimens',
      ri_min:      1.539,
      ri_max:      1.545,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Copal — subfossil tree resin; NOT a mineral. Trade name for young tree resin (hundreds to thousands of years old, as opposed to amber which is millions of years old). Primarily from East Africa (Tanzania, DRC) and Colombia. Golden-yellow; often contains inclusions. Yin pair to Amber.',
      updttime:    '2026-05-30T00:00:00Z',
      mindat_url:  null,
      piezoelectric:     false,
      safe_for_water:    true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Copal (Subfossil Resin)',
      refractive_index: { n_mean: 1.540 },
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: 'Variable blue-white to green (often stronger than amber)',
      fluorescence_sw: 'Weak',
      phosphorescence: null,
      visible_wavelength_nm: { min: 570, max: 600 },
      spectra: [],
    },

    color: {
      primary_color:         'Pale golden-yellow to warm amber — the living resin before geological time transforms it',
      color_variants: [
        'Pale clear yellow (youngest copal — most transparent)',
        'Golden-yellow (classic Congo/Tanzania copal)',
        'Warm amber-orange (older, more polymerised)',
        'Cloudy pale yellow (gas bubble inclusions)',
        'Clear with insect/plant inclusions (most prized collector form)',
      ],
      dominant_wavelength_nm: 585,
      oklch:   { l: 0.82, c: 0.16, h: 90 },
      hex:     '#f0d870',
      munsell: '2.5Y 8/8',
      color_temperature_k: 4500,
      psychological_effects: [
        'Copal is amber in the making — working with copal is working with time at an earlier stage of the same transformation',
        'The resinous lustre and warm golden colour create an impression of preserved sunlight — organic, warm, and luminous',
        'Insect inclusions in copal connect directly to the living world — these are real organisms preserved in real time, just more recent than amber inclusions',
        'The smell of copal resin (burned as incense) is one of the most ancient ritual scents in Mesoamerican and African traditions',
        'Copal\'s softness (H1.5–2) makes it warm to touch and easy to work — the most human-scale of the resin stones',
      ],
      harmonics: {
        complementary_hue: 270,
        triadic_hues:      [210, 330],
        analogous_range:   [70, 110],
      },
    },

    metaphysical: {
      mineral_name:     'Copal',
      chakra_primary:   'Sacral',
      chakra_secondary: ['Solar Plexus', 'Crown', 'Root'],
      element:   ['Fire', 'Earth', 'Akasha'],
      planet:    ['Sun', 'Jupiter', 'Moon'],
      archetype: ['The Living Amber', 'The Young Resin', 'The Incense of the Ancestors'],
      zodiac:    ['Leo', 'Sagittarius', 'Cancer'],
      numerology: 3,
      angel_number: 333,
      intention: 'I am amber before amber. I am time still warm. What I hold has not yet been translated by geological patience.',
      traditions: [
        'Mesoamerican tradition — copal (from Nahuatl copalli, "incense") is one of the most sacred ritual resins in Aztec, Maya, and other Mesoamerican cultures; burned as an offering to the gods; still central to Day of the Dead ceremonies',
        'East African tradition — Congo basin and Tanzania copal used in local resin trade and ceremony for centuries; the great Congo copal forests were a significant 19th century trade commodity',
        'Colombian copal — Hymenaea resin from Colombia; golden and clear; sometimes contains insect inclusions; exported internationally as both copal incense and crystal healing material',
        'Incense tradition — burned copal resin produces a clean, warm, slightly sweet smoke used for purification, ceremony, and ancestor connection across multiple continents',
        'Modern crystal healing — used similarly to amber but considered more accessible, younger, and more dynamically connected to the living tree consciousness',
      ],
      properties: [
        'NOT a mineral — subfossil tree resin; organic poly-terpenoid material; hundreds to thousands of years old (amber is millions)',
        'Primary sources: Tanzania/DRC (East African copal — Hymenaea verrucosa, Trachylobium), Colombia (H. courbaril), Madagascar, New Zealand (kauri copal)',
        'May contain insect or plant inclusions — younger and less well-preserved than amber inclusions',
        'Can be distinguished from amber: acetone test (copal surface becomes tacky/sticky; amber does not), UV fluorescence, and inclusions',
        'Safe for brief water contact — organic resin; avoid prolonged soaking',
        'H1.5–2 — very soft; easily scratched; store carefully',
        'Burned as incense: the aromatic smoke is the primary use in traditional cultures',
      ],
      gaia_resonance: 'ViriditasHeart + Noosphere + AnchorPrism',
      safety_warning:  'NOT a mineral — organic resin. Safe for brief water contact (avoid prolonged soaking). H1.5–2 — very soft. No toxic elements. When burned as incense, use in well-ventilated space. May cause resin allergy in sensitive individuals.',
    },
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // 5. COPPER (NATIVE)
  // Cu — native element copper; cubic
  // IMA recognised — the original metal of human civilisation
  // Dendritic, wire, and massive forms; TOXIC in water
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {
    name:         'Copper (Native)',
    mindat_id:    1209,
    rruff_ids:    ['R040090'],
    last_synced:  '2026-05-30T00:00:00Z',
    trade_name:   false,
    color_layer:  'natural',
    yin_yang_pair: 'Native Silver',

    physical: {
      id:           1209,
      longid:       'copper-native',
      guid:         '',
      name:         'Copper (Native Element — Cu)',
      ima_formula:  'Cu',
      mindat_formula: 'Cu',
      ima_status:   'A',
      ima_year:     null,
      strunzten:    '1.AA.05',
      dana8ed:      '1.1.1.3',
      crystal_system: 'Cubic (isometric)',
      hardness_min: 2.5,
      hardness_max: 3,
      specific_gravity_min: 8.90,
      specific_gravity_max: 8.94,
      cleavage:    'None',
      fracture:    'Hackly (jagged metallic)',
      tenacity:    'Ductile and malleable — the defining quality of copper',
      luster:      ['Metallic'],
      diaphaneity: ['Opaque'],
      colour:      'Fresh: distinctive salmon-pink to orange-red (unique copper colour). Tarnishes rapidly to brown, then dark brown-black, then develops green patina (malachite/atacamite) on long exposure. The copper colour is unmistakable and unique among native metals.',
      streak:      'Metallic copper-red (shiny)',
      fluorescence: 'None',
      ri_min:      null,
      ri_max:      null,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Native Copper — Cu, cubic native element. The first metal worked by humans; foundation of the Copper and Bronze Ages. Salmon-pink to orange-red metallic; unique colour. Ductile and malleable. SG 8.9 — very heavy. TOXIC in water. Major locality: Keweenaw Peninsula, Michigan (USA) — the world\'s largest native copper deposit.',
      updttime:    '2026-05-30T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-1209.html',
      piezoelectric:     false,
      safe_for_water:    false,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name:    'Native Copper',
      refractive_index: null,
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: 'None',
      fluorescence_sw: 'None',
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R040090'],
    },

    color: {
      primary_color:         'Salmon-pink to orange-red — the colour so distinctive it is named after the metal itself',
      color_variants: [
        'Fresh salmon-pink to copper-orange (unoxidised — the true colour)',
        'Brown to dark brown (early tarnish — cuprite surface)',
        'Dark brown-black (advanced tarnish)',
        'Green patina (malachite/atacamite — long weathering)',
        'Multicolour tarnish rainbow (thin-film interference, similar to chalcopyrite)',
      ],
      dominant_wavelength_nm: 600,
      oklch:   { l: 0.52, c: 0.22, h: 45 },
      hex:     '#c86a30',
      munsell: '5YR 5/10',
      color_temperature_k: null,
      psychological_effects: [
        'Copper colour is so distinctive it gave its name to the hue — one of very few minerals that named a colour rather than the reverse',
        'The warm salmon-pink to orange-red is simultaneously metallic and warm — one of the most human-feeling of the metal colours',
        'Ductility and malleability — copper bends without breaking, stretches into wire — communicates a quality of yielding strength that is rare in minerals',
        'The transformation from salmon-pink to green patina (as on the Statue of Liberty) tells a complete story of chemical transformation over time',
        'SG 8.9 — nearly as heavy as lead — the unexpected weight of copper in hand is always striking; it is heavier than it looks',
      ],
      harmonics: {
        complementary_hue: 225,
        triadic_hues:      [165, 285],
        analogous_range:   [25, 65],
      },
    },

    metaphysical: {
      mineral_name:     'Copper (Native)',
      chakra_primary:   'Sacral',
      chakra_secondary: ['Root', 'Heart', 'Solar Plexus'],
      element:   ['Fire', 'Metal', 'Earth'],
      planet:    ['Venus', 'Mars', 'Sun'],
      archetype: ['The First Metal', 'The Foundation of Civilisation', 'The Venus Metal'],
      zodiac:    ['Taurus', 'Libra', 'Aries'],
      numerology: 1,
      angel_number: 111,
      intention: 'I am the first metal the human hand shaped. Every circuit, every wire, every bell and mirror that came after me began here.',
      traditions: [
        'The first metal — copper was the first metal worked by humans (>10,000 BCE in the Middle East); the Copper Age (Chalcolithic) precedes the Bronze Age',
        'Venus metal — in classical alchemy and astrology, copper is the metal of Venus; associated with beauty, love, art, and the feminine principle',
        'Keweenaw Peninsula, Michigan (USA) — the world\'s largest native copper deposit; Lake Superior copper worked by Native Americans for over 7,000 years',
        'Cyprus — so much copper came from Cyprus that the Latin word cuprum (copper) derives from the island name; the island\'s identity was defined by its copper',
        'Electrical civilisation — copper\'s electrical conductivity (second only to silver among common metals) makes it the foundation of all electrical infrastructure',
        'Alchemical tradition — copper + tin = bronze; copper + zinc = brass; the alloys of copper defined the metallurgical ages of human civilisation',
      ],
      properties: [
        'IMA recognised — formula Cu; cubic (isometric) native element; one of a few metals found in native (pure elemental) form in nature',
        'TOXIC in water — copper ions (Cu²⁺) leach into water; copper is toxic to aquatic organisms and potentially harmful in drinking water at elevated levels; DO NOT use in water elixirs',
        'Most ductile and malleable red metal — can be drawn into wire thinner than a human hair; hammered into sheets without fracturing',
        'SG 8.9 — very heavy; the weight-to-volume ratio is always surprising',
        'Electrical conductivity: 59.6×10⁶ S/m — second only to silver; the foundation of all electrical wiring',
        'Tarnish sequence: salmon-pink → brown cuprite → black tenorite → green malachite/atacamite',
        'Major localities: Keweenaw Peninsula (MI, USA), Ray Mine (AZ, USA), Namibia, DRC, Russia (Ural Mountains), Chile',
      ],
      gaia_resonance: 'SovereignCore + AnchorPrism + ViriditasHeart',
      safety_warning:  '⚠️ TOXIC IN WATER — copper ions (Cu²⁺) leach into water. DO NOT use in water elixirs. Wash hands after handling. Safe for dry handling and display. H2.5–3 — soft; easily scratched. Keep away from food and children.',
    },
  },

];

export default BATCH_C6;
