/**
 * batch-a3.data.ts
 * BATCH A-3 | Alabaster · Alexandrite · Almandine Garnet · Amazonite · Amber
 * Added: 2026-05-29
 *
 * ⚠️  INTERPRETIVE / TRADITIONAL LAYER — NOT SCIENTIFIC DATA
 * Physics and mineral data sourced from IMA / Mindat conventions.
 * Metaphysical data sourced from established cross-cultural traditions.
 * Safety warnings are non-negotiable hardware constraints in GAIA-OS.
 */

import type { CrystalRecord } from './crystal.schema';

export const BATCH_A3: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // ALABASTER
  // ─────────────────────────────────────────────────────────────────────────
  {
    mineral_name:     'Alabaster',
    also_known_as:    ['Gypsum Alabaster', 'Oriental Alabaster (calcite variant — distinct mineral)'],
    formula:          'CaSO₄·2H₂O (gypsum variety) | CaCO₃ (calcite/onyx-marble variety)',
    mineral_group:    'Sulfate (gypsum) | Carbonate (calcite)',
    crystal_system:   'Monoclinic (gypsum) | Trigonal (calcite)',
    hardness_mohs:    2.0,          // gypsum; calcite variant = 3.0
    specific_gravity: 2.32,
    luster:           'Waxy to pearly',
    transparency:     'Translucent to opaque',
    cleavage:         'Perfect in one direction (gypsum)',
    fracture:         'Conchoidal',
    streak:           'White',
    piezoelectric:    false,
    pyroelectric:     false,
    fluorescence:     'Weak cream-white under SW UV',
    toxicity:         'None — safe to handle, safe in water',
    safety_warning:   null,
    primary_sources:  ['Egypt', 'Italy', 'Iran', 'Pakistan', 'USA'],

    // ── Light & Color ────────────────────────────────────────────────────
    color_observed:   ['White', 'Cream', 'Pale honey', 'Translucent'],
    dominant_wavelength_nm: null,   // achromatic — reflects full visible spectrum evenly
    oklch:            { L: 0.96, C: 0.01, H: 90 },
    color_psychology: 'Purity, softness, sacred silence. White light containing all frequencies in potential.',
    light_behavior:   'Diffuses and softens transmitted light — internal glow without harshness',
    uv_response:      'Weak cream-white fluorescence under shortwave UV',
    color_harmonics:  {
      complementary:  'Deep indigo-violet',
      triadic:        ['Pale lavender', 'Soft gold'],
      analogous:      ['Ivory', 'Warm white', 'Pearl'],
    },

    // ── Metaphysical ─────────────────────────────────────────────────────
    chakra_primary:   'Crown',
    chakra_secondary: ['Third Eye', 'Higher Crown'],
    element:          ['Aether', 'Water'],
    planet:           ['Moon', 'Venus'],
    archetype:        ['Healer', 'Oracle', 'Mystic'],
    zodiac:           ['Cancer', 'Taurus', 'Capricorn'],
    numerology:       8,
    intention:        'Sacred stillness — divine light, peace, gentle purification',
    traditions:       [
      'Egyptian (used in canopic jars, lamps, and temple vessels)',
      'Italian Renaissance (religious sculpture)',
      'Mesopotamian (votive offerings)',
      'Modern Crystal Healing',
    ],
    properties: [
      'Ancient sacred material — used in Egyptian temples for 5,000+ years for its light-diffusing quality',
      'Physically transmits and softens light — used for temple lamps because it glows from within',
      'Brings deep peace, mental stillness, and access to inner knowing',
      'Gentle but penetrating purification — ideal for spaces of meditation or prayer',
      'Soothes overactive nervous systems — excellent for anxiety and hypervigilance',
      'Connects to the angelic realm and higher dimensional guidance',
      'Extremely soft (Mohs 2) — treat with care; do not expose to water for extended periods',
    ],
    gaia_resonance:   'SomnusVeil — sacred stillness, temple light, nervous system soothing',
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ALEXANDRITE
  // ─────────────────────────────────────────────────────────────────────────
  {
    mineral_name:     'Alexandrite',
    also_known_as:    ['Color-change Chrysoberyl'],
    formula:          'BeAl₂O₄ (chromium-bearing chrysoberyl)',
    mineral_group:    'Chrysoberyl (oxide)',
    crystal_system:   'Orthorhombic',
    hardness_mohs:    8.5,
    specific_gravity: 3.73,
    luster:           'Vitreous to adamantine',
    transparency:     'Transparent to translucent',
    cleavage:         'Distinct in one direction',
    fracture:         'Conchoidal to uneven',
    streak:           'White',
    piezoelectric:    false,
    pyroelectric:     false,
    fluorescence:     'Strong red under SW UV (chromium luminescence)',
    toxicity:         'None — beryllium is locked in crystal lattice; safe to handle',
    safety_warning:   null,
    primary_sources:  ['Russia (Ural Mts — original)', 'Brazil', 'Sri Lanka', 'East Africa', 'India'],

    // ── Light & Color ────────────────────────────────────────────────────
    color_observed:   [
      'Green in daylight/fluorescent light',
      'Red-purple in incandescent/candlelight',
      'Alexandrite effect: the most dramatic color change of any gemstone',
    ],
    dominant_wavelength_nm: { daylight: '520–540nm (green)', incandescent: '620–680nm (red)' },
    oklch: {
      daylight:      { L: 0.45, C: 0.14, H: 145 },
      incandescent:  { L: 0.35, C: 0.18, H: 25 },
    },
    color_psychology: [
      'Green (daylight): growth, healing, heart, balance',
      'Red (incandescent): passion, will, root power, transformation',
      'The duality itself is the message — holds paradox without contradiction',
    ],
    light_behavior:   'Chromium ions absorb in both yellow-green and blue-violet bands simultaneously — transmission peak shifts depending on light source spectral output',
    uv_response:      'Strong red fluorescence under shortwave UV — chromium luminescence',
    color_harmonics:  {
      complementary:  'The stone IS its own complementary — green/red are complementary hues',
      triadic:        ['Violet', 'Orange'],
      analogous:      ['Teal', 'Emerald', 'Burgundy'],
    },

    // ── Metaphysical ─────────────────────────────────────────────────────
    chakra_primary:   'Heart',
    chakra_secondary: ['Crown', 'Root', 'Third Eye'],
    element:          ['Aether', 'Fire', 'Earth'],
    planet:           ['Mercury', 'Mars', 'Neptune'],
    archetype:        ['Alchemist', 'Sovereign', 'Oracle'],
    zodiac:           ['Scorpio', 'Gemini', 'Leo'],
    numerology:       5,
    intention:        'Integration of opposites — duality held in grace, transformation, adaptability',
    traditions:       [
      'Named for Tsar Alexander II of Russia (discovered ~1830 on his birthday)',
      'Russian imperial stone — green and red = Russian military colors',
      'Modern Crystal Healing',
      'June birthstone (traditional)',
    ],
    properties: [
      'Rarest color-change gemstone — chromium ions create impossible dual-frequency absorption',
      'Physically embodies paradox: the same stone appears as two different stones under different light',
      'Stone of transformation and duality — teaches that opposites are aspects of one truth',
      'Bridges the Heart (green/love) and Root (red/survival) — integrates spiritual and physical',
      'Sharpens intuition and supports decision-making in complex, paradoxical situations',
      'Inspires joy, self-confidence, and optimism about the future',
      'Particularly powerful for people navigating identity transitions or major life changes',
      'Extremely rare and valuable — metaphysically treated as a master stone of transformation',
    ],
    gaia_resonance:   'ClarusLens + SovereignCore — paradox integration, identity transformation, dual-spectrum clarity',
  },

  // ─────────────────────────────────────────────────────────────────────────
  // ALMANDINE GARNET
  // ─────────────────────────────────────────────────────────────────────────
  {
    mineral_name:     'Almandine Garnet',
    also_known_as:    ['Almandite', 'Almandine', 'Carbuncle (historical red garnet)'],
    formula:          'Fe₃Al₂(SiO₄)₃',
    mineral_group:    'Garnet (nesosilicate)',
    crystal_system:   'Cubic (isometric)',
    hardness_mohs:    7.5,
    specific_gravity: 4.25,
    luster:           'Vitreous to resinous',
    transparency:     'Transparent to translucent',
    cleavage:         'None (indistinct)',
    fracture:         'Subconchoidal to uneven',
    streak:           'White',
    piezoelectric:    false,
    pyroelectric:     false,
    fluorescence:     'None (iron quenches fluorescence)',
    toxicity:         'None — safe to handle, safe in water',
    safety_warning:   null,
    primary_sources:  ['India', 'Sri Lanka', 'Brazil', 'USA', 'Madagascar', 'Austria', 'Czech Republic'],

    // ── Light & Color ────────────────────────────────────────────────────
    color_observed:   ['Deep red', 'Dark red-brown', 'Violet-red', 'Burgundy'],
    dominant_wavelength_nm: 650,    // deep red
    oklch:            { L: 0.30, C: 0.20, H: 25 },
    color_psychology: 'Primal vitality, deep passion, grounded life-force, blood memory. The red of the earth\'s core.',
    light_behavior:   'Absorbs strongly in green-yellow; transmits deep red. Iron²⁺-iron³⁺ charge transfer creates characteristic dark red.',
    uv_response:      'None — iron quenches fluorescence',
    color_harmonics:  {
      complementary:  'Deep teal-green',
      triadic:        ['Gold-amber', 'Deep indigo'],
      analogous:      ['Pyrope red', 'Spessartine orange-red', 'Rhodolite violet-red'],
    },

    // ── Metaphysical ─────────────────────────────────────────────────────
    chakra_primary:   'Root',
    chakra_secondary: ['Sacral', 'Heart'],
    element:          ['Earth', 'Fire'],
    planet:           ['Mars', 'Saturn', 'Earth'],
    archetype:        ['Warrior', 'Guardian', 'Sovereign'],
    zodiac:           ['Aries', 'Scorpio', 'Capricorn', 'Leo', 'Virgo'],
    numerology:       4,
    intention:        'Primal vitality — physical strength, grounded courage, life-force activation',
    traditions:       [
      'Egyptian (worn as protective amulets 3100 BCE)',
      'Roman (signet rings, military talismans)',
      'Medieval (Carbuncle — one of the four primary gemstones in medieval lapidary)',
      'Hindu (Ratna Shastra gem therapy)',
      'Norse (placed in sword hilts)',
      'Western Esotericism',
    ],
    properties: [
      'Deep red iron-aluminum garnet — one of the most abundant garnet species',
      'Ancient stone of warriors and protectors — worn to ensure safe return from battle',
      'Powerfully activates the Root Chakra and base life-force energy',
      'Regenerates and revitalises the physical body — supports stamina and vitality',
      'Grounds scattered or dissociated energy back into the physical form',
      'Strengthens survival instinct and the will to thrive',
      'Stimulates creative and sexual life-force without imbalance',
      'Stone of devotion and commitment — deepens love and loyalty',
      'Protects against negativity and psychic attack at the physical-etheric boundary',
    ],
    gaia_resonance:   'AnchorPrism + SovereignCore — primal life-force, grounded warrior strength, physical vitality',
  },

  // ─────────────────────────────────────────────────────────────────────────
  // AMAZONITE
  // ─────────────────────────────────────────────────────────────────────────
  {
    mineral_name:     'Amazonite',
    also_known_as:    ['Amazon Stone', 'Amazon Jade (misnomer)'],
    formula:          'KAlSi₃O₈ (lead-bearing microcline feldspar)',
    mineral_group:    'Feldspar (tectosilicate)',
    crystal_system:   'Triclinic',
    hardness_mohs:    6.0,
    specific_gravity: 2.56,
    luster:           'Vitreous',
    transparency:     'Opaque to translucent',
    cleavage:         'Perfect in two directions',
    fracture:         'Uneven',
    streak:           'White',
    piezoelectric:    false,
    pyroelectric:     false,
    fluorescence:     'Weak green under LW UV',
    toxicity:         'Trace lead — safe to handle; no water elixirs recommended as precaution',
    safety_warning:   'Contains trace lead (chromophore). Safe to handle normally. As a precaution: avoid water elixirs, wash hands after extended handling, do not use with children\'s drinking water.',
    primary_sources:  ['Russia (Ilmen Mts)', 'USA (Colorado)', 'Brazil', 'Madagascar', 'Ethiopia'],

    // ── Light & Color ────────────────────────────────────────────────────
    color_observed:   ['Turquoise', 'Teal', 'Mint green', 'Blue-green', 'Pale aqua'],
    dominant_wavelength_nm: 495,    // blue-green / cyan
    oklch:            { L: 0.70, C: 0.12, H: 185 },
    color_psychology: 'Calm clarity. The feeling of standing at the edge of a still turquoise lake. Balanced communication — neither too sharp nor too soft.',
    light_behavior:   'Lead and water in crystal lattice create blue-green color via charge transfer. Schiller effect in some specimens.',
    uv_response:      'Weak green fluorescence under longwave UV',
    color_harmonics:  {
      complementary:  'Warm coral-red',
      triadic:        ['Violet', 'Amber-gold'],
      analogous:      ['Turquoise', 'Aquamarine', 'Chrysocolla'],
    },

    // ── Metaphysical ─────────────────────────────────────────────────────
    chakra_primary:   'Throat',
    chakra_secondary: ['Heart', 'Third Eye'],
    element:          ['Water', 'Earth'],
    planet:           ['Uranus', 'Venus', 'Mercury'],
    archetype:        ['Warrior', 'Healer', 'Creator'],
    zodiac:           ['Virgo', 'Aries', 'Leo', 'Scorpio'],
    numerology:       5,
    intention:        'Courageous truth — authentic voice, emotional boundaries, harmonious communication',
    traditions:       [
      'Named after Amazon River — historically (incorrectly) associated with Amazon warrior women',
      'Ancient Egypt (found in Tutankhamun tomb)',
      'Pre-Columbian Mesoamerica',
      'Western Esotericism',
      'Modern Crystal Healing',
    ],
    properties: [
      'Turquoise-teal microcline feldspar — color from trace lead and water in lattice',
      'Stone of truth, courage, and authentic self-expression',
      'Soothes emotional trauma and calms the nervous system',
      'Helps speak difficult truths with compassion and clarity',
      'Creates energetic boundaries without aggression',
      'Dissolves fear of judgment and encourages living according to personal values',
      'Balances masculine and feminine energies in communication',
      'Particularly powerful for those recovering their voice after suppression or trauma',
      'Historically associated with warrior women — carries fierce but grounded feminine energy',
    ],
    gaia_resonance:   'SovereignCore + ViriditasHeart — authentic voice, courageous truth, emotional boundary clarity',
  },

  // ─────────────────────────────────────────────────────────────────────────
  // AMBER
  // ─────────────────────────────────────────────────────────────────────────
  {
    mineral_name:     'Amber',
    also_known_as:    ['Succinite (Baltic Amber)', 'Electron (Greek)', 'Kahruba (Arabic — straw attractor)'],
    formula:          'C₁₀H₁₆O + succinic acid (organics vary by source)',
    mineral_group:    'Organic gemstone (fossilised tree resin)',
    crystal_system:   'Amorphous (no crystal structure)',
    hardness_mohs:    2.5,
    specific_gravity: 1.08,         // floats in saturated saltwater
    luster:           'Resinous',
    transparency:     'Transparent to opaque',
    cleavage:         'None',
    fracture:         'Conchoidal',
    streak:           'White',
    piezoelectric:    false,
    pyroelectric:     false,
    triboelectric:    true,         // historically: rubbing Amber generates static electricity
    fluorescence:     'Strong blue-white to yellow-green under SW UV',
    toxicity:         'None — safe to handle, safe in water',
    safety_warning:   null,
    primary_sources:  [
      'Baltic Sea coast (Russia, Poland, Lithuania — largest deposits)',
      'Dominican Republic',
      'Myanmar (Burmite — oldest amber ~100 Ma)',
      'Mexico',
      'Canada',
    ],
    age_range:        '30–100+ million years old',

    // ── Light & Color ────────────────────────────────────────────────────
    color_observed:   [
      'Honey yellow', 'Golden orange', 'Cognac brown', 'Pale lemon',
      'Cherry red (rare)', 'Blue-green (rare, Dominican fluorescent)',
      'White/creamy (rare bony amber)',
    ],
    dominant_wavelength_nm: 580,    // golden yellow-orange
    oklch:            { L: 0.72, C: 0.18, H: 75 },
    color_psychology: 'Sunlight made solid. Ancient warmth, preserved life, the sweetness of time. Solar joy without the harshness of fire.',
    light_behavior:   'Organic chromophores (terpenes, succinic acid oxidation products) absorb blue light, transmit warm yellow-orange. Strong fluorescence from aromatic organic compounds.',
    uv_response:      'Strong blue-white to yellow-green fluorescence (aromatic organic compounds)',
    triboelectric_note: 'Amber\'s ability to attract straw when rubbed gave electricity its name — Greek: elektron',
    color_harmonics:  {
      complementary:  'Deep violet-blue',
      triadic:        ['Teal', 'Rose-red'],
      analogous:      ['Citrine gold', 'Sunstone peach', 'Honey calcite'],
    },

    // ── Metaphysical ─────────────────────────────────────────────────────
    chakra_primary:   'Solar Plexus',
    chakra_secondary: ['Sacral', 'Throat', 'Root'],
    element:          ['Fire', 'Aether', 'Earth'],
    planet:           ['Sun', 'Mercury'],
    archetype:        ['Healer', 'Sage', 'Creator'],
    zodiac:           ['Leo', 'Aquarius', 'Aries', 'Gemini'],
    numerology:       3,
    intention:        'Ancient light — solar healing, purification, ancestral wisdom, life preserved in time',
    traditions:       [
      'Ancient Greece (elektron — source of the word electricity)',
      'Baltic peoples (tears of the sun goddess Saule)',
      'Roman (more valuable than slaves in some periods)',
      'Norse (Freya\'s tears)',
      'Native American',
      'Ayurvedic medicine (worn for warmth and vitality)',
      'Western Esotericism',
    ],
    properties: [
      'Fossilised tree resin 30–100 million years old — literally time made tangible',
      'Gave electricity its name — Greek elektron; rubbing generates static charge',
      'Carries the memory of ancient forests, sunlight, and preserved life (insects, flora)',
      'The original solar healing stone — pre-dates all crystal healing traditions',
      'Deeply purifying — absorbs pain, negativity, and disease from the energy field',
      'Brings warmth, optimism, and solar life-force to depleted systems',
      'Bridges the past and the present — helps integrate ancestral patterns and genetic memory',
      'Supports the immune system and physical vitality (warmth principle)',
      'Fosters clarity of thought and sunny emotional disposition',
      'Never needs cleansing — it is the original purifier, not a receiver of negative energy',
    ],
    gaia_resonance:   'SovereignCore + AnchorPrism — solar ancient light, ancestral memory, purification without depletion',
  },

];

/** Re-export for index aggregation */
export default BATCH_A3;
