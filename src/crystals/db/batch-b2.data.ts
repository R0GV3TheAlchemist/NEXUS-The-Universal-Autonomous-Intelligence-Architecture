/**
 * src/crystals/db/batch-b2.data.ts
 * GAIA-OS Crystal Database — Batch B-2
 *
 * Entries:
 *   1. Banded Calcite
 *   2. Benitoite
 *   3. Beryl
 *   4. Bismuth
 *   5. Black Calcite
 *
 * Schema: CrystalRecord v1.3
 * Author: GAIA-OS Crystal Intelligence Engine
 * Date:   2026-05-29
 *
 * NOTE: A mineralogically rich batch. Benitoite is the rarest gemstone
 * in this entire database — the official state gem of California, found
 * at a single locality now closed. Beryl is the parent species of
 * emerald, aquamarine, heliodor, morganite, and goshenite. Bismuth is
 * the only native element in this batch — and the only stone that forms
 * those iconic iridescent staircase crystals loved across the tradition.
 */

import type { CrystalRecord } from './crystal.schema';

const BATCH_B2: CrystalRecord[] = [

  // ─────────────────────────────────────────────────────────────────────────
  // 1. BANDED CALCITE
  // Also known as Onyx Marble or Mexican Onyx — NOT true onyx
  // Travertine-type banded calcite — the ancient decorative stone
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Banded Calcite',
    mindat_id:   859,
    rruff_ids:   ['R040070'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  true,
    color_layer: 'natural',
    yin_yang_pair: 'Black Obsidian',

    physical: {
      id:           859,
      longid:       'banded-calcite',
      guid:         '',
      name:         'Calcite (banded travertine variety — also sold as "Mexican Onyx" or "Onyx Marble")',
      ima_formula:  'CaCO₃',
      mindat_formula: 'CaCO3',
      ima_status:   'A',
      ima_year:     1845,
      strunzten:    '5.AB.05',
      dana8ed:      '14.1.1.1',
      crystal_system: 'Trigonal',
      hardness_min: 3,
      hardness_max: 3,
      specific_gravity_min: 2.71,
      specific_gravity_max: 2.71,
      cleavage:    'Perfect rhombohedral on {10−1‐4}',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Waxy (polished)'],
      diaphaneity: ['Translucent'],
      colour:      'Honey-gold, cream, white, orange, green, or brown with alternating concentric or parallel bands',
      streak:      'White',
      fluorescence: 'Strong pink, red, or blue under UV (variable)',
      ri_min:      1.486,
      ri_max:      1.658,
      birefringence: 0.172,
      optical_type: 'U',
      shortdesc:   'Banded travertine calcite — deposited from hot springs or cave drip water in concentric or parallel layers. Commercially sold as "Mexican Onyx" or "Onyx Marble" though it is NOT true onyx (which is chalcedony).',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-859.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Banded Calcite',
      refractive_index: { n_omega: 1.658, n_epsilon: 1.486 },
      birefringence:   0.172,
      optical_sign:    '-',
      dispersion:      'Weak',
      pleochroism:     null,
      fluorescence_lw: 'Strong pink, red, or blue (locality-dependent)',
      fluorescence_sw: 'Variable',
      phosphorescence: 'Possible',
      visible_wavelength_nm: null,
      spectra: ['R040070'],
    },

    color: {
      primary_color:          'Honey-gold to cream with alternating bands',
      color_variants:         ['Honey and cream', 'White and orange', 'Green and cream (Pakistan)', 'Brown and caramel', 'Multi-banded rainbow'],
      dominant_wavelength_nm: 580,
      oklch:   { l: 0.78, c: 0.10, h: 75 },
      hex:     '#d4b060',
      munsell: '5Y 7/4',
      color_temperature_k:    3200,
      psychological_effects:  [
        'The banded pattern creates a visual rhythm that is uniquely meditative — the eye follows the bands inward',
        'Honey-gold and cream tones are among the most universally comforting in the visible spectrum',
        'The translucency — especially when backlit — creates a warm, lantern-like glow that is deeply soothing',
        'Encourages a sense of timelessness — each band represents a layer of geological patience',
      ],
      harmonics: {
        complementary_hue: 255,
        triadic_hues:      [195, 315],
        analogous_range:   [55, 95],
      },
    },

    metaphysical: {
      mineral_name:     'Banded Calcite',
      chakra_primary:   'Solar Plexus',
      chakra_secondary: ['Sacral', 'Crown'],
      element:   ['Earth', 'Water'],
      planet:    ['Saturn', 'Moon'],
      archetype: ['The Layer Keeper', 'The Patient Builder', 'The Ancient Interior'],
      zodiac:    ['Taurus', 'Cancer', 'Capricorn'],
      numerology: 4,
      angel_number: 444,
      intention: 'I build with patience. Each layer of my life has meaning.',
      traditions: [
        'Ancient Egyptian tradition — used for alabaster canopic jars and statuary',
        'Ancient Roman and Greek tradition — decorative vessels, columns, and floors',
        'Mexican craft tradition — widely carved and exported as "Mexican Onyx"',
      ],
      properties: [
        'NOT true onyx — commercially sold as "Mexican Onyx" or "Onyx Marble" but is banded travertine calcite',
        'Formed from calcium-rich spring or cave water depositing calcite in concentric layers over thousands of years',
        'Ancient Egyptians carved it into canopic jars and alabaster vessels — called "alabaster" in the ancient world',
        'The banding records geological time — each layer a season of mineral deposition',
        'Supports patience, methodical progress, and the long view — the stone of builders and architects',
        'Backlit banded calcite produces a warm amber glow — used in decorative lighting and sacred spaces',
        'One of the most widely used decorative stones in human history — found on every continent',
      ],
      gaia_resonance: 'SovereignCore + ViriditasHeart',
      safety_warning: 'Soft (H3) and water-sensitive. Not true onyx — always clarify species to clients. Do not use in water elixirs.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 2. BENITOITE
  // Barium titanium cyclosilicate — the rarest gem in this database
  // California’s state gemstone — found at ONE locality on Earth
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Benitoite',
    mindat_id:   676,
    rruff_ids:   ['R040029'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Sunstone',

    physical: {
      id:           676,
      longid:       'benitoite',
      guid:         '',
      name:         'Benitoite',
      ima_formula:  'BaTiSi₃O₉',
      mindat_formula: 'BaTiSi3O9',
      ima_status:   'A',
      ima_year:     1907,
      strunzten:    '9.CA.05',
      dana8ed:      '63.2.1.1',
      crystal_system: 'Hexagonal',
      hardness_min: 6,
      hardness_max: 6.5,
      specific_gravity_min: 3.65,
      specific_gravity_max: 3.68,
      cleavage:    'Imperfect on {10−1‐0}',
      fracture:    'Conchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Transparent'],
      colour:      'Vivid sapphire blue to violet-blue — among the most saturated natural blues in gemology',
      streak:      'White',
      fluorescence: 'Exceptionally strong blue-white under shortwave UV — among the most fluorescent gems known',
      ri_min:      1.757,
      ri_max:      1.804,
      birefringence: 0.047,
      optical_type: 'U',
      shortdesc:   'Extremely rare barium titanium cyclosilicate. Found gem-quality only at the Benitoite Gem Mine (now closed) on San Benito River, California. California’s official state gem since 1985. Has stronger dispersion than diamond.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-676.html',
      piezoelectric:    true,
      safe_for_water:   true,
      safe_for_hardware: false,
    },

    optical: {
      mineral_name: 'Benitoite',
      refractive_index: { n_omega: 1.804, n_epsilon: 1.757 },
      birefringence:   0.047,
      optical_sign:    '-',
      dispersion:      '0.046 — higher than diamond (0.044)',
      pleochroism:     'Strong dichroic: deep blue / colourless',
      fluorescence_lw: 'Weak',
      fluorescence_sw: 'Exceptionally strong blue-white — among the most fluorescent gems known',
      phosphorescence: null,
      visible_wavelength_nm: { min: 430, max: 470 },
      spectra: ['R040029'],
    },

    color: {
      primary_color:          'Vivid sapphire to violet-blue',
      color_variants:         ['Deep sapphire blue', 'Violet-blue', 'Pale blue (small stones)'],
      dominant_wavelength_nm: 450,
      oklch:   { l: 0.42, c: 0.26, h: 272 },
      hex:     '#1e3fa0',
      munsell: '7.5PB 4/12',
      color_temperature_k:    null,
      psychological_effects:  [
        'The saturation of benitoite blue rivals sapphire — but carries a more electric, alive quality',
        'The exceptional UV fluorescence means the stone glows a completely different colour in sunlight vs indoor light',
        'The rarity of benitoite gives it an energetic intensity that common blue stones cannot match',
        'Activates a sense of unique destiny — the energy of the singular path',
      ],
      harmonics: {
        complementary_hue: 92,
        triadic_hues:      [32, 152],
        analogous_range:   [252, 292],
      },
    },

    metaphysical: {
      mineral_name:     'Benitoite',
      chakra_primary:   'Third Eye',
      chakra_secondary: ['Throat', 'Crown'],
      element:   ['Water', 'Aether'],
      planet:    ['Uranus', 'Neptune'],
      archetype: ['The Singular Soul', 'The Rarest Light', 'The California Star'],
      zodiac:    ['Virgo', 'Aquarius', 'Sagittarius'],
      numerology: 1,
      angel_number: 111,
      intention: 'I am singular and irreplaceable. My light is found nowhere else.',
      traditions: [
        'California geological heritage — state gem since 1985',
        'Western crystal healing — collector-grade stone, rarely used in practice due to extreme rarity',
      ],
      properties: [
        'IMA-recognised since 1907 — named for San Benito County, California',
        'Gem-quality specimens found ONLY at the Benitoite Gem Mine, New Idria district, California — now closed',
        'Has higher dispersion (fire) than diamond — 0.046 vs diamond’s 0.044',
        'Exceptionally strong shortwave UV fluorescence — among the most intensely fluorescent gems known to science',
        'California’s official state gemstone since 1985',
        'Piezoelectric — generates an electric charge under pressure',
        'The rarest gem in the GAIA-OS tradition database — the stone of singular destiny and irreplaceable light',
      ],
      gaia_resonance: 'QuantumNexus + ClarusLens + SovereignCore',
      safety_warning: 'Extremely rare and valuable — handle with exceptional care. Piezoelectric — keep away from sensitive electronics. Collector-grade stone — not typically available for healing work.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 3. BERYL
  // The parent species — emerald, aquamarine, heliodor, morganite
  // One of the most important gem minerals in human history
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Beryl',
    mindat_id:   783,
    rruff_ids:   ['R050031'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Garnet',

    physical: {
      id:           783,
      longid:       'beryl',
      guid:         '',
      name:         'Beryl',
      ima_formula:  'Be₃Al₂Si₆O₁₈',
      mindat_formula: 'Be3Al2Si6O18',
      ima_status:   'A',
      ima_year:     1798,
      strunzten:    '9.CJ.05',
      dana8ed:      '61.1.1.1',
      crystal_system: 'Hexagonal',
      hardness_min: 7.5,
      hardness_max: 8,
      specific_gravity_min: 2.63,
      specific_gravity_max: 2.92,
      cleavage:    'Imperfect on {0001}',
      fracture:    'Conchoidal to uneven',
      tenacity:    'Brittle',
      luster:      ['Vitreous'],
      diaphaneity: ['Transparent', 'Translucent'],
      colour:      'Colourless (goshenite), green (emerald/green beryl), blue (aquamarine), yellow (heliodor), pink (morganite), red (bixbite)',
      streak:      'White',
      fluorescence: 'Variable by variety: none to weak orange, green, or blue',
      ri_min:      1.564,
      ri_max:      1.595,
      birefringence: 0.006,
      optical_type: 'U',
      shortdesc:   'Beryllium aluminium cyclosilicate — parent species of emerald, aquamarine, heliodor, morganite, goshenite, and bixbite. One of the primary sources of the element beryllium. Forms large hexagonal prisms.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-783.html',
      piezoelectric:    false,
      safe_for_water:   true,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Beryl',
      refractive_index: { n_omega: 1.590, n_epsilon: 1.567 },
      birefringence:   0.006,
      optical_sign:    '-',
      dispersion:      '0.014',
      pleochroism:     'Weak to moderate depending on variety',
      fluorescence_lw: 'Weak to none (variety-dependent)',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R050031'],
    },

    color: {
      primary_color:          'Colourless (pure) — full spectrum of varieties by trace element',
      color_variants:         [
        'Colourless (goshenite — pure Be₃Al₂Si₆O₁₈)',
        'Green (emerald — Cr³⁺/V³⁺)',
        'Blue (aquamarine — Fe²⁺)',
        'Yellow-green (heliodor — Fe³⁺)',
        'Pink-peach (morganite — Mn²⁺)',
        'Red (bixbite — Mn³⁺ — extremely rare)',
      ],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.92, c: 0.02, h: 180 },
      hex:     '#e8f0ee',
      munsell: null,
      color_temperature_k:    null,
      psychological_effects:  [
        'As the parent species, beryl in its pure colourless form holds the full potential of all its varieties',
        'It is the template — the blank state from which love (morganite), vision (aquamarine), and growth (emerald) emerge',
        'Energetically: the spectrum of human experience contained in a single mineral family',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   null,
      },
    },

    metaphysical: {
      mineral_name:     'Beryl',
      chakra_primary:   'Crown',
      chakra_secondary: ['Heart', 'Throat', 'Solar Plexus'],
      element:   ['Air', 'Water'],
      planet:    ['Venus', 'Mercury', 'Sun'],
      archetype: ['The Full Spectrum', 'The Parent Stone', 'The Template of Potential'],
      zodiac:    ['Aries', 'Gemini', 'Scorpio'],
      numerology: 1,
      angel_number: 111,
      intention: 'I hold the full spectrum of possibility. I am the source from which all colours emerge.',
      traditions: [
        'Ancient Greek and Roman gem tradition — Pliny the Elder described beryl extensively',
        'Medieval scrying tradition — clear beryl (goshenite) used for crystal balls before quartz became standard',
        'Western crystal healing — varieties treated individually; pure beryl as the meta-stone',
      ],
      properties: [
        'IMA-recognised since 1798 — parent species of emerald, aquamarine, heliodor, morganite, goshenite, and bixbite',
        'The trace element determines the variety: Cr/V → emerald, Fe²⁺ → aquamarine, Mn²⁺ → morganite, Fe³⁺ → heliodor',
        'Forms large, perfectly hexagonal prismatic crystals — some of the largest gem crystals in nature',
        'Primary industrial source of the element beryllium',
        'Medieval scrying tradition used clear goshenite beryl as crystal balls before clear quartz became standard',
        'The Breastplate of Aaron in the Hebrew Bible contains beryl (tarshish) as one of the twelve stones',
        'The parent stone metaphysically: holds the full spectrum rather than a single frequency',
      ],
      gaia_resonance: 'Noosphere + ClarusLens + ViriditasHeart',
      safety_warning: 'Contains beryllium — do not inhale dust when cutting or grinding. Polished specimens are safe to handle. Emerald, aquamarine, and other varieties have individual safety notes — see their specific entries.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 4. BISMUTH
  // Native element — the iridescent staircase crystal
  // Naturally occurring but the most spectacular specimens are lab-grown
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Bismuth',
    mindat_id:   703,
    rruff_ids:   ['R060240'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Clear Quartz',

    physical: {
      id:           703,
      longid:       'bismuth',
      guid:         '',
      name:         'Bismuth (native element)',
      ima_formula:  'Bi',
      mindat_formula: 'Bi',
      ima_status:   'A',
      ima_year:     1832,
      strunzten:    '1.CA.05',
      dana8ed:      '1.3.5.1',
      crystal_system: 'Trigonal',
      hardness_min: 2,
      hardness_max: 2.5,
      specific_gravity_min: 9.70,
      specific_gravity_max: 9.83,
      cleavage:    'Perfect on {0001}',
      fracture:    'Uneven',
      tenacity:    'Brittle',
      luster:      ['Metallic'],
      diaphaneity: ['Opaque'],
      colour:      'Silver-white with iridescent rainbow surface oxidation (blues, pinks, yellows, greens)',
      streak:      'Silver-white',
      fluorescence: null,
      ri_min:      null,
      ri_max:      null,
      birefringence: null,
      optical_type: null,
      shortdesc:   'Native bismuth — a heavy post-transition metal. Natural crystals are rare; the spectacular hopper/staircase lab-grown crystals are the form used in the crystal tradition. The iridescence comes from a thin bismuth oxide layer.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-703.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Bismuth',
      refractive_index: null,
      birefringence:   null,
      optical_sign:    null,
      dispersion:      null,
      pleochroism:     null,
      fluorescence_lw: null,
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R060240'],
    },

    color: {
      primary_color:          'Silver-white metal with full-spectrum iridescent oxidation',
      color_variants:         ['Silver-pink', 'Electric blue staircase', 'Golden-green oxidation', 'Full rainbow hopper crystal'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.70, c: 0.12, h: 300 },
      hex:     '#c088c0',
      munsell: null,
      color_temperature_k:    null,
      psychological_effects:  [
        'The hopper crystal staircase form is one of the most visually complex structures in nature',
        'Full-spectrum iridescence activates the full range of the visual cortex simultaneously',
        'The stepped geometric form embodies the idea of ascension — each level built on the last',
        'The rainbow quality makes it the most joyful and wonder-inducing metal in the tradition',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   null,
      },
    },

    metaphysical: {
      mineral_name:     'Bismuth',
      chakra_primary:   'Crown',
      chakra_secondary: ['Third Eye', 'Earth Star', 'Soul Star'],
      element:   ['Aether', 'Fire', 'Earth'],
      planet:    ['Uranus', 'Jupiter'],
      archetype: ['The Ascension Staircase', 'The Rainbow Bridge', 'The Geometric Spirit'],
      zodiac:    ['Aquarius', 'Libra'],
      numerology: 5,
      angel_number: 555,
      intention: 'I ascend step by step. Every level reveals a new spectrum of possibility.',
      traditions: [
        'Western crystal healing — modern tradition',
        'Alchemical tradition — bismuth ("wismuth") was known to medieval alchemists as a unique metal',
      ],
      properties: [
        'Native element — one of the few pure metals in the crystal tradition alongside gold and copper',
        'Natural crystals are rare and small; the spectacular hopper/staircase forms are lab-grown by controlled cooling',
        'The iridescence is a thin bismuth oxide layer — the same principle as a soap bubble or oil slick',
        'The hopper crystal form occurs because edges grow faster than faces — producing the iconic stepped geometry',
        'Bismuth is the most naturally diamagnetic element — it actively repels magnetic fields',
        'Used in medicine (Pepto-Bismol) — bismuth subsalicylate is a safe digestive compound',
        'The rainbow staircase form is among the most photographed and beloved objects in the modern crystal tradition',
      ],
      gaia_resonance: 'QuantumNexus + Noosphere + SovereignCore',
      safety_warning: 'Heavy metal (SG ~9.8) — do not use in water elixirs. Wash hands after handling. Soft (H2-2.5) — handle with care. Most specimens in the tradition are lab-grown — disclose to clients.',
    },
  },

  // ─────────────────────────────────────────────────────────────────────────
  // 5. BLACK CALCITE
  // Dark to jet-black calcite — rare colour variety
  // The shadow calcite — boundary and psychic protection
  // ─────────────────────────────────────────────────────────────────────────
  {
    name:        'Black Calcite',
    mindat_id:   859,
    rruff_ids:   ['R040070'],
    last_synced: '2026-05-29T00:00:00Z',
    trade_name:  false,
    color_layer: 'natural',
    yin_yang_pair: 'Selenite',

    physical: {
      id:           859,
      longid:       'black-calcite',
      guid:         '',
      name:         'Calcite (black variety — from bituminous or carbonaceous inclusions)',
      ima_formula:  'CaCO₃',
      mindat_formula: 'CaCO3',
      ima_status:   'A',
      ima_year:     1845,
      strunzten:    '5.AB.05',
      dana8ed:      '14.1.1.1',
      crystal_system: 'Trigonal',
      hardness_min: 3,
      hardness_max: 3,
      specific_gravity_min: 2.71,
      specific_gravity_max: 2.75,
      cleavage:    'Perfect rhombohedral on {10−1‐4}',
      fracture:    'Conchoidal',
      tenacity:    'Brittle',
      luster:      ['Vitreous', 'Resinous'],
      diaphaneity: ['Translucent', 'Opaque'],
      colour:      'Dark grey to jet black — from bituminous, carbonaceous, or organic inclusions',
      streak:      'White (distinguishes from graphite and other black minerals)',
      fluorescence: 'Weak or none (organic matter quenches fluorescence)',
      ri_min:      1.486,
      ri_max:      1.660,
      birefringence: 0.172,
      optical_type: 'U',
      shortdesc:   'Black to dark grey colour variety of calcite, coloured by carbonaceous or bituminous inclusions. Rarer than white or coloured calcites. The dark colour is NOT intrinsic to the CaCO₃ — it is always from organic or carbonaceous impurities.',
      updttime:    '2026-05-29T00:00:00Z',
      mindat_url:  'https://www.mindat.org/min-859.html',
      piezoelectric:    false,
      safe_for_water:   false,
      safe_for_hardware: true,
    },

    optical: {
      mineral_name: 'Black Calcite',
      refractive_index: { n_omega: 1.660, n_epsilon: 1.486 },
      birefringence:   0.172,
      optical_sign:    '-',
      dispersion:      'Weak',
      pleochroism:     null,
      fluorescence_lw: 'None to very weak',
      fluorescence_sw: null,
      phosphorescence: null,
      visible_wavelength_nm: null,
      spectra: ['R040070'],
    },

    color: {
      primary_color:          'Dark grey to jet black',
      color_variants:         ['Deep charcoal grey', 'Jet black', 'Dark grey with white matrix', 'Black with subtle vitreous sheen'],
      dominant_wavelength_nm: null,
      oklch:   { l: 0.18, c: 0.01, h: 200 },
      hex:     '#2a2c2b',
      munsell: 'N 2/',
      color_temperature_k:    null,
      psychological_effects:  [
        'Black calcite carries the softness of calcite within the protective frequency of black — a unique combination',
        'Unlike harder black stones (obsidian, tourmaline), black calcite absorbs rather than deflects',
        'The opacity invites a sense of interior privacy — useful for those who feel psychically exposed',
        'Supports the integration of shadow material — the dark calcite is the gentle shadow-worker',
      ],
      harmonics: {
        complementary_hue: null,
        triadic_hues:      null,
        analogous_range:   null,
      },
    },

    metaphysical: {
      mineral_name:     'Black Calcite',
      chakra_primary:   'Root',
      chakra_secondary: ['Earth Star', 'Third Eye'],
      element:   ['Earth'],
      planet:    ['Saturn', 'Pluto'],
      archetype: ['The Gentle Shadow Worker', 'The Boundary Keeper', 'The Interior Protector'],
      zodiac:    ['Capricorn', 'Scorpio'],
      numerology: 8,
      angel_number: 888,
      intention: 'I hold my interior space with care. My boundaries are clear and kind.',
      traditions: [
        'Western crystal healing',
      ],
      properties: [
        'Rare colour variety of calcite coloured by bituminous or carbonaceous inclusions',
        'The black is NOT intrinsic to calcite — always from organic/carbonaceous inclusions — streaks white',
        'Unique in the black stone tradition: carries the amplifying, softening quality of calcite within the protective black frequency',
        'Gentler than black obsidian or black tourmaline for shadow work — absorbs without confrontation',
        'Supports psychic boundary-setting, clearing of unwanted energetic attachments, and interior protection',
        'Angel number 888 — abundance and boundary as two sides of the same sovereignty',
        'Ideal for those beginning shadow work who find harder black stones too intense',
      ],
      gaia_resonance: 'SovereignCore + SomnusVeil',
      safety_warning: 'Soft (H3) and water-sensitive. Streak test (white) distinguishes from graphite or other black minerals. Do not use in water elixirs.',
    },
  },

];

export default BATCH_B2;
