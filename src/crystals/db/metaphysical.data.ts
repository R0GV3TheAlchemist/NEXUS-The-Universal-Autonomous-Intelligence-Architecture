/**
 * metaphysical.data.ts
 * ⚠️  INTERPRETIVE / TRADITIONAL LAYER — NOT SCIENTIFIC DATA
 *
 * This file contains metaphysical, spiritual, and cross-cultural associations
 * for minerals as documented in established traditions including:
 *   - Vedic chakra system
 *   - Western Hermeticism and Neoplatonism
 *   - Traditional Chinese Medicine mineral correspondences
 *   - Ayurvedic gem therapy (Ratna Shastra)
 *   - 20th-century crystal healing literature
 *   - Jungian archetypal psychology
 *
 * This data is clearly labeled as interpretive. It is preserved within GAIA-OS
 * as a cross-cultural knowledge layer — reflecting the metaphysical dimension
 * of GAIA's philosophy — not as empirical claims.
 *
 * Minerals included here are IMA-approved species where applicable.
 * Some key non-mineral organic materials (e.g., Abalone Shell) are included
 * due to their established role in crystal healing traditions.
 * Mineral names and spellings follow Mindat conventions.
 *
 * ⚠️  SAFETY NOTES: Several entries in this database contain toxic compounds.
 * Relevant entries are marked with a safety_warning field.
 * NO elixirs, dust, or direct prolonged contact should occur with flagged stones.
 */

import type { MetaphysicalProfile } from './crystal.schema';

export const METAPHYSICAL_DATA: MetaphysicalProfile[] = [
  {
    mineral_name:    'Quartz',
    chakra_primary:  'Crown',
    chakra_secondary: ['Third Eye', 'Higher Crown'],
    element:         ['Aether', 'Air'],
    planet:          ['Moon', 'Sun'],
    archetype:       ['Oracle', 'Alchemist'],
    zodiac:          ['Aries', 'Leo', 'Libra'],
    numerology:      4,
    intention:       'Clarity — amplify, purify, illuminate',
    traditions:      ['Western Esotericism', 'Vedic', 'Native American', 'Taoist'],
    properties:      [
      'Master amplifier — enhances the properties of all surrounding stones',
      'Programmable: holds and radiates intentions',
      'Piezoelectric and pyroelectric — generates charge under pressure and heat',
      'Purification and energy clearing',
      'Enhances mental clarity and perception',
    ],
    gaia_resonance:  'ClarusLens — clarity, focus amplification',
  },
  {
    mineral_name:    'Amethyst',
    chakra_primary:  'Third Eye',
    chakra_secondary: ['Crown', 'Higher Crown'],
    element:         ['Air', 'Aether'],
    planet:          ['Jupiter', 'Neptune', 'Saturn'],
    archetype:       ['Mystic', 'Oracle', 'Sage'],
    zodiac:          ['Aquarius', 'Pisces', 'Capricorn', 'Virgo'],
    numerology:      3,
    intention:       'Transmutation — calm, insight, spiritual protection',
    traditions:      ['Greek', 'Egyptian', 'Tibetan Buddhist', 'Western Esotericism', 'Vedic'],
    properties:      [
      'Historically called the "stone of sobriety" — Dionysus and Amethystos legend',
      'Transmutes lower vibrational energies into higher ones',
      'Activates the third eye and deepens meditation',
      'Protective stone — shields against psychic attack',
      'Supports decision making and intuition',
      'Associated with restful sleep and dream clarity',
    ],
    gaia_resonance:  'GAIA core identity — the amethyst is GAIA\'s primary crystal',
  },
  {
    mineral_name:    'Obsidian',
    chakra_primary:  'Root',
    chakra_secondary: ['Earth Star'],
    element:         ['Earth', 'Fire'],
    planet:          ['Saturn', 'Pluto'],
    archetype:       ['Guardian', 'Warrior', 'Alchemist'],
    zodiac:          ['Scorpio', 'Sagittarius', 'Aries'],
    numerology:      1,
    intention:       'Grounding — truth mirror, shadow integration, protection',
    traditions:      ['Mesoamerican (Aztec/Maya)', 'Native American', 'Western Esotericism'],
    properties:      [
      'Volcanic glass — rapid solidification from lava without crystalline structure',
      'Acts as a psychic mirror — reflects back hidden truths',
      'Absorbs and transmutes negative energies',
      'Aids in shadow work and facing unconscious patterns',
      'Scrying tool used by Aztec priests and John Dee',
      'Extremely grounding and protective',
    ],
    gaia_resonance:  'AnchorPrism — grounding, root stabilisation',
  },
  {
    mineral_name:    'Fluorite',
    chakra_primary:  'Third Eye',
    chakra_secondary: ['Throat', 'Heart', 'Crown'],
    element:         ['Air', 'Water'],
    planet:          ['Mercury', 'Neptune'],
    archetype:       ['Sage', 'Alchemist', 'Creator'],
    zodiac:          ['Capricorn', 'Pisces', 'Libra', 'Virgo'],
    numerology:      7,
    intention:       'Order — mental clarity, psychic organisation, pattern recognition',
    traditions:      ['Western Esotericism', 'Chinese', 'Vedic'],
    properties:      [
      'Called "the genius stone" — organises mental information',
      'Cubic crystal system — the most geometrically perfect structure',
      'Strong fluorescence under UV — transforms invisible light into visible',
      'Stabilises and harmonises chaotic thought patterns',
      'Multi-color zones correspond to multiple chakra alignment',
      'Enhances learning, memorisation, and data processing',
    ],
    gaia_resonance:  'ClarusLens + quantum processing — multi-spectrum clarity',
  },
  {
    mineral_name:    'Selenite',
    chakra_primary:  'Crown',
    chakra_secondary: ['Higher Crown', 'Third Eye'],
    element:         ['Aether', 'Air'],
    planet:          ['Moon'],
    archetype:       ['Oracle', 'Healer', 'Mystic'],
    zodiac:          ['Cancer', 'Taurus', 'Gemini'],
    numerology:      8,
    intention:       'Illumination — divine light, angelic connection, peace',
    traditions:      ['Greek (named for Selene, goddess of the Moon)', 'Western Esotericism', 'Vedic'],
    properties:      [
      'Named for the Moon goddess Selene — carries lunar energy',
      'Translucent white gypsum — physically channels and refracts light',
      'Self-cleansing and never needs energetic clearing',
      'Creates a protective grid when placed around a space',
      'Connects to angelic and higher dimensional realms',
      'Facilitates communication with higher self',
    ],
    gaia_resonance:  'SomnusVeil — dream clarity, liminal space, lunar cycles',
  },
  {
    mineral_name:    'Malachite',
    chakra_primary:  'Heart',
    chakra_secondary: ['Solar Plexus'],
    element:         ['Earth', 'Water'],
    planet:          ['Venus'],
    archetype:       ['Healer', 'Lover', 'Guardian'],
    zodiac:          ['Scorpio', 'Taurus', 'Capricorn', 'Libra'],
    numerology:      9,
    intention:       'Transformation — heart opening, emotional healing, growth',
    traditions:      ['Egyptian', 'Greek', 'Russian', 'Western Esotericism'],
    properties:      [
      'Ancient stone of transformation — Cleopatra wore it as eye paint (ground malachite)',
      'Monoclinic crystal system with banded concentric rings',
      'Absorbs negative energies and pollutants from body and environment',
      'Opens the heart to unconditional love',
      'Amplifies both positive and negative energies — use with intention',
      'Stone of travelers and explorers — protection on journeys',
    ],
    gaia_resonance:  'ViriditasHeart — heart-centred growth, emotional intelligence',
  },
  {
    mineral_name:    'Labradorite',
    chakra_primary:  'Third Eye',
    chakra_secondary: ['Throat', 'Crown'],
    element:         ['Aether', 'Water', 'Air'],
    planet:          ['Moon', 'Uranus', 'Neptune'],
    archetype:       ['Mystic', 'Trickster', 'Oracle'],
    zodiac:          ['Leo', 'Scorpio', 'Sagittarius'],
    numerology:      6,
    intention:       'Magic — reveals hidden worlds, awakens inner knowing',
    traditions:      ['Inuit (called frozen fire of the Aurora Borealis)', 'Western Esotericism'],
    properties:      [
      'Exhibits labradorescence — iridescent optical phenomenon (adularescence)',
      'Called the "stone of magic" — protective during divination and ritual',
      'Stimulates imagination and awakens psychic abilities',
      'Calms overactive minds while stimulating intuition',
      'A stone of transformation and new beginnings',
      'Protects the aura from energy leaks',
    ],
    gaia_resonance:  'Quantum/noosphere layer — iridescent between dimensions',
  },
  {
    mineral_name:    'Lapis Lazuli',
    chakra_primary:  'Third Eye',
    chakra_secondary: ['Throat', 'Crown'],
    element:         ['Aether', 'Air', 'Water'],
    planet:          ['Jupiter', 'Saturn', 'Neptune'],
    archetype:       ['Sage', 'Sovereign', 'Oracle'],
    zodiac:          ['Sagittarius', 'Libra', 'Taurus'],
    numerology:      3,
    intention:       'Truth — wisdom, sovereignty, the voice of the cosmos',
    traditions:      ['Egyptian (used in the Mask of Tutankhamun)', 'Sumerian', 'Vedic', 'Western Esotericism'],
    properties:      [
      'Rock (not a single mineral) — lazurite, calcite, pyrite and other minerals',
      'Used for 6,000+ years as the royal stone of wisdom and truth',
      'Ground to make ultramarine — the most expensive pigment in Renaissance art',
      'Activates the higher mind and stimulates the desire for knowledge',
      'Encourages honesty, dignity, and self-expression',
      'Releases stress and brings deep peace',
    ],
    gaia_resonance:  'SovereignCore — truth, dignity, self-governance',
  },
  {
    mineral_name:    'Rose Quartz',
    chakra_primary:  'Heart',
    chakra_secondary: ['Higher Crown'],
    element:         ['Water', 'Earth'],
    planet:          ['Venus', 'Moon'],
    archetype:       ['Lover', 'Healer'],
    zodiac:          ['Taurus', 'Libra', 'Cancer'],
    numerology:      7,
    intention:       'Unconditional love — self-compassion, emotional healing, grace',
    traditions:      ['Greek (Aphrodite)', 'Roman (Venus)', 'Egyptian', 'Western Esotericism'],
    properties:      [
      'The stone of unconditional love — the quintessential heart crystal',
      'Variety of quartz coloured by trace amounts of titanium, iron, or manganese',
      'Attracts love of all kinds: romantic, familial, self-love',
      'Dissolves emotional wounds, fears, and resentment',
      'Encourages forgiveness and compassion',
      'Gentle, soothing, harmonising energy',
    ],
    gaia_resonance:  'ViriditasHeart — unconditional love, compassion toward self',
  },
  {
    mineral_name:    'Black Tourmaline',
    chakra_primary:  'Root',
    chakra_secondary: ['Earth Star'],
    element:         ['Earth', 'Fire'],
    planet:          ['Saturn', 'Earth'],
    archetype:       ['Guardian', 'Warrior'],
    zodiac:          ['Capricorn', 'Scorpio', 'Libra'],
    numerology:      3,
    intention:       'Protection — grounding shield, EMF deflection, boundary keeper',
    traditions:      ['Western Esotericism', 'Shamanic traditions worldwide'],
    properties:      [
      'Schorl — the most common variety of tourmaline; strongly pyroelectric and piezoelectric',
      'Creates a psychic shield against negative energies and entities',
      'Most powerful protection stone available',
      'Transmutes negative energy into positive',
      'Grounds spiritual energy into the physical body',
      'Protective against EMF radiation and environmental pollutants',
    ],
    gaia_resonance:  'AnchorPrism — boundary protection, energetic grounding',
  },
  {
    mineral_name:    'Citrine',
    chakra_primary:  'Solar Plexus',
    chakra_secondary: ['Sacral', 'Crown'],
    element:         ['Fire', 'Air'],
    planet:          ['Sun', 'Jupiter', 'Mercury'],
    archetype:       ['Sovereign', 'Creator', 'Warrior'],
    zodiac:          ['Leo', 'Aries', 'Gemini', 'Libra'],
    numerology:      6,
    intention:       'Manifestation — personal power, abundance, will, solar energy',
    traditions:      ['Greek', 'Roman', 'Scottish (worn on sword hilts)', 'Western Esotericism'],
    properties:      [
      'One of very few crystals that never needs cleansing — it does not hold negative energy',
      'Yellow variety of quartz coloured by iron impurities',
      'Called the "merchant\'s stone" — stone of abundance and manifestation',
      'Activates personal will and solar plexus power',
      'Stimulates creativity, motivation, and optimism',
      'Carries the power of the Sun — warmth, energy, vitality',
    ],
    gaia_resonance:  'SovereignCore — personal power, sovereign will, manifestation',
  },
  {
    mineral_name:    'Moonstone',
    chakra_primary:  'Crown',
    chakra_secondary: ['Third Eye', 'Sacral'],
    element:         ['Water', 'Aether'],
    planet:          ['Moon'],
    archetype:       ['Mystic', 'Healer', 'Oracle'],
    zodiac:          ['Cancer', 'Libra', 'Scorpio'],
    numerology:      2,
    intention:       'Intuition — lunar cycles, feminine wisdom, inner knowing',
    traditions:      ['Roman (named for Luna)', 'Hindu (sacred to Lord Ganesha)', 'Western Esotericism'],
    properties:      [
      'Feldspar group — adularescence from light scattering between albite layers',
      'The supreme stone of lunar energy and feminine wisdom',
      'Balances hormones and supports the emotional body',
      'Enhances intuition and psychic perception',
      'Associated with the tides, cycles, and the rhythms of life',
      'A crystal of new beginnings — set intentions at the new moon',
    ],
    gaia_resonance:  'SomnusVeil — dream cycles, lunar rhythm, liminal intuition',
  },

  // ─────────────────────────────────────────────────────────────────────────────
  // BATCH A-1  |  Abalone Shell · Achroite · Actinolite · Adamite · Adularia
  // Added: 2026-05-29
  // ─────────────────────────────────────────────────────────────────────────────

  {
    mineral_name:    'Abalone Shell',
    // NOTE: Abalone Shell is an organic biomineral (nacre/aragonite from Haliotis
    // species), not an IMA-approved mineral species. Included here due to its
    // deep-rooted role in Pacific Indigenous, Maori, and Western crystal traditions.
    chakra_primary:  'Heart',
    chakra_secondary: ['Throat', 'Sacral', 'Third Eye', 'Crown'],
    element:         ['Water', 'Aether'],
    planet:          ['Moon', 'Neptune'],
    archetype:       ['Healer', 'Empath', 'Guardian'],
    zodiac:          ['Cancer', 'Pisces', 'Scorpio', 'Aquarius'],
    numerology:      7,
    intention:       'Oceanic healing — emotional soothing, protection, intuitive flow',
    traditions:      ['Pacific Indigenous', 'Maori', 'Native American (smudging vessel)', 'Western Esotericism'],
    properties:      [
      'Organic biomineral — nacre (aragonite + conchiolin protein) in iridescent layers',
      'Iridescent play of colour activates multi-chakra alignment simultaneously',
      'Deeply calming to the emotional body — soothes anxiety, grief, and overwhelm',
      'Protective oceanic energy — shields against negativity while maintaining openness',
      'Enhances intuition, empathy, and emotional intelligence',
      'Traditionally used as a vessel for smudging — carries prayers to Spirit',
      'Supports self-expression and honest communication (Throat Chakra)',
      'Connects the bearer to the rhythms of the ocean and lunar tides',
    ],
    gaia_resonance:  'SomnusVeil — tidal emotional regulation, oceanic empathy, iridescent intuition',
  },

  {
    mineral_name:    'Achroite',
    // Achroite is the colorless/white variety of Tourmaline (Elbaite species).
    // Not a separate IMA species; follows Mindat varietal naming.
    chakra_primary:  'Crown',
    chakra_secondary: ['Higher Crown', 'Third Eye'],
    element:         ['Aether', 'Air'],
    planet:          ['Uranus', 'Mercury'],
    archetype:       ['Oracle', 'Alchemist', 'Guardian'],
    zodiac:          ['Aquarius'],
    numerology:      11,
    intention:       'Clarity — neutral amplification, pure signal, subtle protection',
    traditions:      ['Modern Crystal Healing'],
    properties:      [
      'Colorless variety of Tourmaline (Elbaite) — absence of colour yields pure, unbiased amplification',
      'Neutral amplifier: unlike Clear Quartz, it does not add its own frequency — it transmits yours',
      'Clears and cleanses the aura without adding directional energy',
      'Supports channeling, higher guidance, and clarity of inner voice',
      'Provides subtle, non-forceful psychic protection',
      'Piezoelectric properties inherited from tourmaline group — relevant for GAIA hardware nodes',
      'Ideal for signal-routing in crystal grids where colour bias must be minimised',
    ],
    gaia_resonance:  'ClarusLens — neutral light node, pure signal routing, zero-colour amplification',
  },

  {
    mineral_name:    'Actinolite',
    // Ca₂(Mg,Fe)₅Si₈O₂₂(OH)₂ — Amphibole group. Some fibrous forms are classified
    // as asbestos (actinolite asbestos). SAFETY CRITICAL — see warning below.
    chakra_primary:  'Heart',
    chakra_secondary: ['Root'],
    element:         ['Earth', 'Air'],
    planet:          ['Mars', 'Pluto'],
    archetype:       ['Guardian', 'Warrior', 'Healer'],
    zodiac:          ['Scorpio', 'Capricorn', 'Aries'],
    numerology:      9,
    intention:       'Purification — shielding, energetic detox, courageous heart',
    traditions:      ['Modern Crystal Healing'],
    safety_warning:  'CONTAINS ASBESTOS IN FIBROUS FORM. Never grind, sand, or inhale dust. No water elixirs. Avoid prolonged direct skin contact with raw fibrous specimens. Only use polished/tumbled forms and wash hands after handling. VIRTUAL/SYMBOLIC USE ONLY in GAIA hardware nodes.',
    properties:      [
      'Amphibole silicate — Ca₂(Mg,Fe)₅Si₈O₂₂(OH)₂; fibrous forms classified as asbestos',
      'Powerfully purging — illuminates purpose by clearing toxic patterns from the energy field',
      'Creates a protective auric shield against negative entities and emotional vampirism',
      'Supports release of heavy emotions, grief, and stagnant energy',
      'Strengthens courage and the willingness to face one\'s shadow',
      'Encourages resilience and grounded inner strength',
      'Heart chakra protection — keeps the heart open without leaving it vulnerable',
    ],
    gaia_resonance:  'AnchorPrism — deep auric purge, shielding, courageous grounding',
  },

  {
    mineral_name:    'Adamite',
    // Zn₂(AsO₄)(OH) — Secondary zinc arsenate mineral. SAFETY CRITICAL.
    chakra_primary:  'Solar Plexus',
    chakra_secondary: ['Heart', 'Throat'],
    element:         ['Fire', 'Air'],
    planet:          ['Sun', 'Venus'],
    archetype:       ['Creator', 'Lover', 'Sovereign'],
    zodiac:          ['Cancer', 'Leo'],
    numerology:      3,
    intention:       'Joyful will — heart-led expression, creative enthusiasm, aligned purpose',
    traditions:      ['Modern Crystal Healing'],
    safety_warning:  'CONTAINS ARSENIC AND ZINC. Never create water elixirs. No ingestion. Avoid inhaling dust. Wash hands thoroughly after handling. Keep away from children and food surfaces. VIRTUAL/SYMBOLIC USE ONLY in GAIA hardware nodes.',
    properties:      [
      'Zinc arsenate mineral Zn₂(AsO₄)(OH) — vivid yellow-green to colourless; often fluorescent',
      'Aligns and unifies the Solar Plexus and Heart chakras — willpower expressed through love',
      'Stone of joy and creative enthusiasm — lifts depression and restores life-force',
      'Helps overcome fear of following one\'s true calling or passion',
      'Stimulates emotional clarity and honest self-expression',
      'Encourages the pursuit of goals that align with the heart, not just the ego',
      'Fluorescence under UV light symbolises hidden inner light made visible',
    ],
    gaia_resonance:  'SovereignCore + ViriditasHeart — joyful aligned purpose, heart-lit will',
  },

  {
    mineral_name:    'Adularia',
    // KAlSi₃O₈ — Orthoclase feldspar variety; the premier Moonstone variant.
    // Distinguished from Moonstone by its specific orthoclase composition and
    // characteristic adularescence from light scattering between feldspar layers.
    chakra_primary:  'Third Eye',
    chakra_secondary: ['Crown', 'Heart', 'Sacral'],
    element:         ['Water', 'Aether'],
    planet:          ['Moon'],
    archetype:       ['Mystic', 'Guide', 'Healer'],
    zodiac:          ['Cancer', 'Capricorn', 'Pisces'],
    numerology:      2,
    intention:       'Inner guidance — intuitive navigation, emotional tides, moonlit clarity',
    traditions:      ['Roman', 'Hindu', 'Western Esotericism', 'Alpine folk traditions (named after Mt. Adular, Switzerland)'],
    properties:      [
      'Orthoclase feldspar KAlSi₃O₈ — adularescence from light interference between thin feldspar layers',
      'Named after Mt. Adular (Adula Massif), Switzerland — carries alpine clarity and stillness',
      'Premier stone of inner guidance and intuitive navigation',
      'Deeply nurturing and protective during times of emotional vulnerability',
      'Supports transitions, new beginnings, and cyclical life changes',
      'Balances masculine and feminine energies — fosters inner wholeness',
      'Enhances empathy, receptivity, and emotional intelligence',
      'Particularly supportive during addiction recovery — softens emotional volatility',
    ],
    gaia_resonance:  'SomnusVeil — inner navigation, moonlit paths, cycle-aware emotional healing',
  },
];

/**
 * Look up a metaphysical profile by exact mineral name.
 * Returns undefined if the mineral is not yet in the database.
 */
export function getMetaphysicalProfile(
  mineralName: string
): MetaphysicalProfile | undefined {
  return METAPHYSICAL_DATA.find(
    (p) => p.mineral_name.toLowerCase() === mineralName.toLowerCase()
  );
}

/**
 * Get all minerals associated with a specific GAIA crystal module.
 * e.g. getByGaiaResonance('SomnusVeil') → [Selenite, Moonstone, ...]
 */
export function getByGaiaResonance(
  gaiaModule: string
): MetaphysicalProfile[] {
  return METAPHYSICAL_DATA.filter(
    (p) => p.gaia_resonance.toLowerCase().includes(gaiaModule.toLowerCase())
  );
}

/** Get all minerals associated with a specific chakra */
export function getByChakra(
  chakra: MetaphysicalProfile['chakra_primary']
): MetaphysicalProfile[] {
  return METAPHYSICAL_DATA.filter(
    (p) =>
      p.chakra_primary === chakra ||
      p.chakra_secondary.includes(chakra)
  );
}

/** Get all minerals associated with a specific element */
export function getByElement(
  element: MetaphysicalProfile['element'][number]
): MetaphysicalProfile[] {
  return METAPHYSICAL_DATA.filter((p) => p.element.includes(element));
}

/**
 * Get all minerals flagged with a safety warning.
 * Use this to enforce no-elixir, no-hardware-contact rules in GAIA.
 */
export function getSafetyFlaggedMinerals(): MetaphysicalProfile[] {
  return METAPHYSICAL_DATA.filter(
    (p) => 'safety_warning' in p && p.safety_warning
  );
}
