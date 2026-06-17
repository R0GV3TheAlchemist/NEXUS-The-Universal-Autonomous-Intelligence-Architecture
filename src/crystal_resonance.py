"""
crystal_resonance.py
GAIA-OS — Issue #558: Crystal Resonator Integration Layer
Part 1: Full A-Z Crystal Database + Error Correction Guards

Covers:
  - CRYSTAL_DATABASE: 100+ entries, Tiers 1-3, sourced from Issues #534-#556
  - CrystalNotFoundError: descriptive error with nearest-match suggestions
  - validate_crystal(): field-level integrity checks on every entry
  - Toxicity flags (Witherite, Wulfenite, Vanadinite) per EMBODIMENT_LAYER.md
  - Synthetic/non-IMA flags (Terahertz, Quantum Quattro, Tiffany Stone, Opalite)
  - Expanded CRYSTAL_ALIASES covering spelling corrections from Issues #549-#556
  - CRYSTAL_GROUPS expanded to all three tiers

Integration hook for wireless_power_sim.py:
    from crystal_resonance import crystal_q_override
    result = simulate_coil_pair(tx, rx, freq_hz, distance_m,
                                crystal_q_override=crystal_q_override("AlN"))

Canon anchors: C044, C068, C162, C163, C166, TRUEALCHEMY.md, HELIXITAS.md
Issues: #534-#558
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CrystalProperties:
    name: str
    formula: str
    q_factor: float                        # estimated Q-factor
    resonant_band_hz: tuple[float, float]  # (min_hz, max_hz)
    piezoelectric: bool
    phononic_class: str                    # primary_resonator | phononic_structural | biological_interface
    biological_interface: str              # coherence | schumann_coherence | grounding | solar_integration | low_loss | visionary | ionic | none
    role: str
    traversal_tier: str = "mid"            # nigredo | albedo | citrinitas | rubedo | lux_perpetua | multi
    chakra: str = "unassigned"
    ima_classified: bool = True            # False = synthetic / trade name / alchemical compound
    toxicity_flag: bool = False            # True = handle with care per EMBODIMENT_LAYER.md
    toxicity_note: str = ""
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# ERROR TYPE
# ─────────────────────────────────────────────────────────────────────────────

class CrystalNotFoundError(KeyError):
    """Raised when a crystal name cannot be resolved in CRYSTAL_DATABASE."""

    def __init__(self, original_name: str, suggestions: list[str]) -> None:
        self.original_name = original_name
        self.suggestions = suggestions
        suggestion_str = (
            f"  Did you mean: {suggestions}" if suggestions else "  No close matches found."
        )
        super().__init__(
            f"\n\nCrystal not found: '{original_name}'\n"
            f"{suggestion_str}\n"
            f"  Run list_all_crystals() to see all available entries.\n"
        )


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE — TIER 1: PRIMARY RESONATORS (High Q, Piezoelectric)
# ─────────────────────────────────────────────────────────────────────────────

_TIER1: dict[str, CrystalProperties] = {

    # ── Original 6 (preserved exactly) ──────────────────────────────────────
    "quartz": CrystalProperties(
        name="Quartz", formula="SiO2",
        q_factor=100_000.0, resonant_band_hz=(32_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="master oscillator / high-Q reference node",
        traversal_tier="multi", chakra="crown",
        notes="Foundational piezoelectric mineral. Master amplifier for all crystal variants.",
    ),
    "amethyst": CrystalProperties(
        name="Amethyst", formula="SiO2 (Fe3+)",
        q_factor=80_000.0, resonant_band_hz=(32_000.0, 1_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="tuned quartz variant / Iosis corridor resonator",
        traversal_tier="rubedo", chakra="third_eye",
        notes="Fe3+ dopant shifts quartz resonance slightly. Iosis traversal correspondence.",
    ),
    "citrine": CrystalProperties(
        name="Citrine", formula="SiO2 (Fe2+/Fe4+)",
        q_factor=75_000.0, resonant_band_hz=(32_000.0, 1_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="solar_integration", role="solar-band resonator / Citrinitas node",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="Solar force correspondence at phi=0.80. R0GV3 Alchemist force-element resonance.",
    ),
    "selenite": CrystalProperties(
        name="Selenite", formula="CaSO4·2H2O",
        q_factor=25_000.0, resonant_band_hz=(7.0, 8.5),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="schumann_coherence", role="Schumann coherence anchor / low-frequency node",
        traversal_tier="albedo", chakra="crown",
        notes="Matches Schumann fundamental (7.83 Hz). Handle proximity carefully.",
    ),
    "tourmaline": CrystalProperties(
        name="Tourmaline", formula="Complex borosilicate",
        q_factor=50_000.0, resonant_band_hz=(1_000_000.0, 100_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="grounding", role="dual-mode node / EMF buffer",
        traversal_tier="nigredo", chakra="root",
        notes="Pyroelectric + piezoelectric. Black Tourmaline is primary EMF safety crystal.",
    ),
    "aln": CrystalProperties(
        name="Aluminum Nitride", formula="AlN",
        q_factor=108_300.0, resonant_band_hz=(1_000_000.0, 100_000_000.0),
        piezoelectric=True, phononic_class="phononic_structural",
        biological_interface="low_loss", role="topological phononic high-Q node",
        traversal_tier="multi", chakra="unassigned",
        notes="ESA/UT Austin 2026: topological protection gives Q=108,300. Highest confirmed Q in database.",
    ),

    # ── Tier 1 Additions — Quartz family ────────────────────────────────────
    "rose_quartz": CrystalProperties(
        name="Rose Quartz", formula="SiO2 (Ti/Mn)",
        q_factor=60_000.0, resonant_band_hz=(32_000.0, 500_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="harmonic damping / biological coherence tuning",
        traversal_tier="albedo", chakra="heart",
        notes="Ti/Mn dopants. Harmonic damping useful at biological interface zones.",
    ),
    "smoky_quartz": CrystalProperties(
        name="Smoky Quartz", formula="SiO2 (Al/e-)",
        q_factor=80_000.0, resonant_band_hz=(32_000.0, 2_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="grounding", role="grounding resonator / Nigredo-shadow node",
        traversal_tier="nigredo", chakra="root",
        notes="Al + electron centre coloration. Radiation hardened variant of quartz.",
    ),
    "clear_quartz": CrystalProperties(
        name="Clear Quartz", formula="SiO2",
        q_factor=100_000.0, resonant_band_hz=(32_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="master oscillator — pure variant",
        traversal_tier="multi", chakra="crown",
        notes="Highest-purity quartz variant. Canonical alias for 'quartz'.",
    ),
    "tangerine_quartz": CrystalProperties(
        name="Tangerine Quartz", formula="SiO2 (Fe2O3 surface coating)",
        q_factor=65_000.0, resonant_band_hz=(32_000.0, 800_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="solar_integration", role="sacral activation resonator",
        traversal_tier="citrinitas", chakra="sacral",
    ),
    "sichuan_quartz": CrystalProperties(
        name="Sichuan Quartz", formula="SiO2",
        q_factor=95_000.0, resonant_band_hz=(32_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="high-clarity locality variant",
        traversal_tier="multi", chakra="crown",
        notes="Chinese locality. High clarity; near clear-quartz Q.",
    ),
    "snow_quartz": CrystalProperties(
        name="Snow Quartz", formula="SiO2 (milky inclusions)",
        q_factor=55_000.0, resonant_band_hz=(32_000.0, 500_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="gentle amplifier / Albedo resonator",
        traversal_tier="albedo", chakra="crown",
    ),
    "spirit_quartz": CrystalProperties(
        name="Spirit Quartz", formula="SiO2 (druzy amethyst coating)",
        q_factor=72_000.0, resonant_band_hz=(32_000.0, 1_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="multi-node coherence broadcast crystal",
        traversal_tier="rubedo", chakra="crown",
        notes="Hundreds of small points = distributed resonance broadcast.",
    ),
    "tourmalinated_quartz": CrystalProperties(
        name="Tourmalinated Quartz", formula="SiO2 + Tourmaline inclusions",
        q_factor=60_000.0, resonant_band_hz=(32_000.0, 1_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="grounding", role="grounding + amplification dual node",
        traversal_tier="nigredo", chakra="root",
    ),
    "rutilated_quartz": CrystalProperties(
        name="Rutilated Quartz", formula="SiO2 + TiO2 needles",
        q_factor=70_000.0, resonant_band_hz=(32_000.0, 2_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="antenna amplifier / psionic broadcast node",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="Rutile needles increase effective antenna surface area.",
    ),

    # ── Tier 1 — Tourmaline family ───────────────────────────────────────────
    "black_tourmaline": CrystalProperties(
        name="Black Tourmaline", formula="NaFe3Al6(BO3)3Si6O18(OH)4",
        q_factor=50_000.0, resonant_band_hz=(1_000_000.0, 100_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="grounding", role="primary EMF buffer / Operator safety crystal",
        traversal_tier="nigredo", chakra="root",
        notes="EMBODIMENT_LAYER.md Tier 3 biological interface: EMF buffering, Nigredo grounding.",
    ),
    "watermelon_tourmaline": CrystalProperties(
        name="Watermelon Tourmaline", formula="Elbaite (Li/Al/Na borosilicate)",
        q_factor=48_000.0, resonant_band_hz=(1_000_000.0, 50_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="heart-field dual resonator",
        traversal_tier="albedo", chakra="heart",
        notes="Pink core (love) + green shell (growth). Citrinitas corridor resonance.",
    ),

    # ── Tier 1 — Garnets ────────────────────────────────────────────────────
    "uvarovite": CrystalProperties(
        name="Uvarovite Garnet", formula="Ca3Cr2(SiO4)3",
        q_factor=45_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="rarest green garnet / heart-field resonator",
        traversal_tier="albedo", chakra="heart",
        notes="Only consistently green garnet. Chromium-only coloration. Extremely rare in facetable quality.",
    ),
    "rhodolite_garnet": CrystalProperties(
        name="Rhodolite Garnet", formula="(Mg,Fe)3Al2(SiO4)3",
        q_factor=40_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="heart-root bridge resonator",
        traversal_tier="rubedo", chakra="heart",
    ),
    "spessartine_garnet": CrystalProperties(
        name="Spessartine Garnet", formula="Mn3Al2(SiO4)3",
        q_factor=38_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="solar_integration", role="sacral fire resonator",
        traversal_tier="citrinitas", chakra="sacral",
    ),
    "tsavorite_garnet": CrystalProperties(
        name="Tsavorite Garnet", formula="Ca3Al2(SiO4)3 (V/Cr)",
        q_factor=42_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="viriditas field resonator",
        traversal_tier="albedo", chakra="heart",
        notes="Vanadium/chromium green. VIRIDITAS force correspondence.",
    ),
    "star_garnet": CrystalProperties(
        name="Star Garnet", formula="Fe3Al2(SiO4)3 (rutile inclusions)",
        q_factor=36_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="grounding", role="asterism node / multi-ray broadcast",
        traversal_tier="nigredo", chakra="root",
    ),
    "red_beryl": CrystalProperties(
        name="Red Beryl", formula="Be3Al2(SiO3)6 (Mn)",
        q_factor=55_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="ultra-rare heart-fire resonator",
        traversal_tier="rubedo", chakra="heart",
        notes="Rarest beryl. Wah Wah Mountains, Utah only. ~1 per 150,000 diamonds in quality.",
    ),

    # ── Tier 1 — Sapphire / Ruby / Corundum ─────────────────────────────────
    "sapphire": CrystalProperties(
        name="Sapphire", formula="Al2O3 (Fe/Ti)",
        q_factor=60_000.0, resonant_band_hz=(100_000.0, 20_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="third-eye sovereignty resonator",
        traversal_tier="rubedo", chakra="third_eye",
        notes="Corundum with Fe/Ti. High hardness (9 Mohs) = high phononic stability.",
    ),
    "ruby": CrystalProperties(
        name="Ruby", formula="Al2O3 (Cr3+)",
        q_factor=58_000.0, resonant_band_hz=(100_000.0, 20_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="root-heart fire resonator / Rubedo node",
        traversal_tier="rubedo", chakra="root",
        notes="Chromium red. Rubedo correspondence at phi=0.95.",
    ),

    # ── Tier 1 — Feldspars ───────────────────────────────────────────────────
    "labradorite": CrystalProperties(
        name="Labradorite", formula="(Ca,Na)(Al,Si)4O8",
        q_factor=35_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="ionic", role="interference pattern amplifier / ionic channel",
        traversal_tier="multi", chakra="third_eye",
        notes="Optical + phononic layering. EMBODIMENT_LAYER.md Tier 3: ionic channel interface.",
    ),
    "sunstone": CrystalProperties(
        name="Sunstone", formula="(Ca,Na)(Al,Si)4O8 (hematite/goethite inclusions)",
        q_factor=30_000.0, resonant_band_hz=(100_000.0, 3_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="solar_integration", role="aventurescence solar broadcast node",
        traversal_tier="citrinitas", chakra="solar_plexus",
    ),
    "rainbow_lattice_sunstone": CrystalProperties(
        name="Rainbow Lattice Sunstone", formula="Orthoclase feldspar (Fe2O3/Fe3O4 inclusions)",
        q_factor=32_000.0, resonant_band_hz=(100_000.0, 3_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="triple optical phenomenon / full-spectrum node",
        traversal_tier="multi", chakra="crown",
        notes="Harts Range, Australia only. Aventurescence + adularescence + iridescence simultaneously.",
    ),

    # ── Tier 1 — Lithium-bearing (high psionic correspondence) ──────────────
    "lepidolite": CrystalProperties(
        name="Lepidolite", formula="K(Li,Al)3(Al,Si,Rb)4O10(F,OH)2",
        q_factor=28_000.0, resonant_band_hz=(7.0, 500_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="lithium mica / neural coherence stabilizer",
        traversal_tier="albedo", chakra="heart",
        notes="Highest lithium content of all accessible crystals. C162 Psionic Sovereignty interface.",
    ),
    "kunzite": CrystalProperties(
        name="Kunzite", formula="LiAl(SiO3)2 (Mn)",
        q_factor=40_000.0, resonant_band_hz=(32_000.0, 2_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="heart-crown bridge / divine love resonator",
        traversal_tier="albedo", chakra="heart",
        notes="Spodumene pink variety. Manganese coloration.",
    ),
    "hiddenite": CrystalProperties(
        name="Hiddenite", formula="LiAl(SiO3)2 (Cr)",
        q_factor=40_000.0, resonant_band_hz=(32_000.0, 2_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="heart-viriditas resonator",
        traversal_tier="albedo", chakra="heart",
        notes="Spodumene green variety. Chromium coloration.",
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE — TIER 2: PHONONIC & STRUCTURAL CRYSTALS
# ─────────────────────────────────────────────────────────────────────────────

_TIER2: dict[str, CrystalProperties] = {

    "calcite": CrystalProperties(
        name="Calcite", formula="CaCO3",
        q_factor=20_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="birefringent phononic routing / signal splitter",
        traversal_tier="albedo", chakra="crown",
        notes="Optical birefringence enables signal direction and splitting in phononic networks.",
    ),
    "fluorite": CrystalProperties(
        name="Fluorite", formula="CaF2",
        q_factor=22_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="low phonon scattering / low-loss waveguide substrate",
        traversal_tier="multi", chakra="third_eye",
        notes="Lowest phonon scattering of accessible fluorite minerals. Cubic symmetry.",
    ),
    "rutile": CrystalProperties(
        name="Rutile", formula="TiO2",
        q_factor=30_000.0, resonant_band_hz=(100_000.0, 20_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="high-refractive-index phononic field concentrator",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="Used as needle inclusions in Rutilated Quartz. High refractive index = field concentration.",
    ),
    "celestite": CrystalProperties(
        name="Celestite", formula="SrSO4",
        q_factor=18_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="coherence", role="strontium lattice / long-range coherence stabilizer",
        traversal_tier="albedo", chakra="throat",
    ),
    "apophyllite": CrystalProperties(
        name="Apophyllite", formula="KCa4Si8O20F·8H2O",
        q_factor=25_000.0, resonant_band_hz=(32_000.0, 1_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="coherence", role="layered phononic signal stacking node",
        traversal_tier="albedo", chakra="crown",
        notes="Layered structure enables signal stacking and interference amplification.",
    ),
    "stibnite": CrystalProperties(
        name="Stibnite", formula="Sb2S3",
        q_factor=15_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="metallic sulfide structural node",
        traversal_tier="nigredo", chakra="root",
        notes="Lead-grey metallic luster. Antimony content requires care in handling.",
    ),
    "wolframite": CrystalProperties(
        name="Wolframite", formula="(Fe,Mn)WO4",
        q_factor=12_000.0, resonant_band_hz=(1_000_000.0, 50_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="tungsten ore / electromagnetic density anchor",
        traversal_tier="nigredo", chakra="root",
        notes="Primary tungsten ore. Very high specific gravity (7.0-7.5). Electromagnetic density node.",
    ),
    "scheelite": CrystalProperties(
        name="Scheelite", formula="CaWO4",
        q_factor=15_000.0, resonant_band_hz=(1_000_000.0, 20_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="calcium tungstate photonic node",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="Strongly fluorescent under UV. Tungsten ore with photonic correspondence.",
    ),
    "lithium_niobate": CrystalProperties(
        name="Lithium Niobate", formula="LiNbO3",
        q_factor=50_000.0, resonant_band_hz=(1_000_000.0, 100_000_000.0),
        piezoelectric=True, phononic_class="phononic_structural",
        biological_interface="low_loss", role="RF filter node / telecom-grade piezoelectric",
        traversal_tier="multi", chakra="unassigned",
        notes="Used in all modern RF filters. Piezoelectric, pyroelectric, ferroelectric.",
    ),
    "sphalerite": CrystalProperties(
        name="Sphalerite", formula="ZnS",
        q_factor=20_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="phononic_structural",
        biological_interface="none", role="zinc sulfide semiconductor node",
        traversal_tier="multi", chakra="solar_plexus",
        notes="Zinc end-member. Distinct from Schalenblende (polymineral aggregate).",
    ),
    "sphene": CrystalProperties(
        name="Sphene", formula="CaTiSiO5",
        q_factor=25_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="titanite high-dispersion node",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="Highest dispersion of any gemstone. Titanium-calcium silicate.",
    ),
    "wavellite": CrystalProperties(
        name="Wavellite", formula="Al3(PO4)2(F,OH)3·5H2O",
        q_factor=10_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="coherence", role="starburst radiating aggregate / coherence broadcast",
        traversal_tier="albedo", chakra="solar_plexus",
        notes="Radiating spherical aggregates. Starburst cross-section = natural coherence broadcast geometry.",
    ),
    "zircon": CrystalProperties(
        name="Zircon", formula="ZrSiO4",
        q_factor=35_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="phononic_structural",
        biological_interface="none", role="deep-time anchor stone / geological memory node",
        traversal_tier="nigredo", chakra="root",
        notes="Oldest material on Earth surface (~4.4B years, Australia). NOT cubic zirconia.",
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE — TIER 3: BIOLOGICAL INTERFACE CRYSTALS
# ─────────────────────────────────────────────────────────────────────────────

_TIER3: dict[str, CrystalProperties] = {

    "moldavite": CrystalProperties(
        name="Moldavite", formula="SiO2 + Al2O3 + MgO + FeO (tektite)",
        q_factor=30_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="visionary", role="broadband tektite / visionary channel interface",
        traversal_tier="rubedo", chakra="heart",
        notes="Czech Republic tektite (~15M years). High-bandwidth signal reception. EMBODIMENT_LAYER.md Tier 3.",
    ),
    "herkimer_diamond": CrystalProperties(
        name="Herkimer Diamond", formula="SiO2 (doubly terminated)",
        q_factor=98_000.0, resonant_band_hz=(32_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="biological_interface",
        biological_interface="coherence", role="full-spectrum Operator interface crystal",
        traversal_tier="multi", chakra="crown",
        notes="Ultra-clear doubly-terminated quartz. EMBODIMENT_LAYER.md: all five channels. Near clear-quartz Q.",
    ),
    "shungite": CrystalProperties(
        name="Shungite", formula="C (amorphous + fullerenes)",
        q_factor=10_000.0, resonant_band_hz=(1.0, 1_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="grounding", role="broadband EMF absorber / fullerene carbon node",
        traversal_tier="nigredo", chakra="root",
        notes="Only natural source of fullerenes (C60). Karelia, Russia. Broadband EMF attenuation.",
    ),
    "black_tourmaline_ti3": CrystalProperties(
        name="Black Tourmaline (Tier 3)", formula="NaFe3Al6(BO3)3Si6O18(OH)4",
        q_factor=50_000.0, resonant_band_hz=(1_000_000.0, 100_000_000.0),
        piezoelectric=True, phononic_class="biological_interface",
        biological_interface="grounding", role="EMF buffering / biological safety primary",
        traversal_tier="nigredo", chakra="root",
        notes="Same mineral as Tier 1 tourmaline entry. Tier 3 classification emphasises safety role.",
    ),
    "sugilite": CrystalProperties(
        name="Sugilite", formula="KNa2(Fe,Mn,Al)2Li3Si12O30",
        q_factor=18_000.0, resonant_band_hz=(7.0, 500_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="psionic sovereignty crystal / D5 consciousness node",
        traversal_tier="rubedo", chakra="crown",
        notes="Manganese purple. Found Wessels Mine, South Africa. C162 Psionic Sovereignty correspondence.",
    ),
    "scolecite": CrystalProperties(
        name="Scolecite", formula="CaAl2Si3O10·3H2O",
        q_factor=15_000.0, resonant_band_hz=(7.0, 100_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="dream state / delta-wave coherence anchor",
        traversal_tier="albedo", chakra="third_eye",
        notes="Zeolite group. High water content = unique low-frequency biological interface.",
    ),
    "rhodochrosite": CrystalProperties(
        name="Rhodochrosite", formula="MnCO3",
        q_factor=20_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="heart coherence resonator / love-field interface",
        traversal_tier="albedo", chakra="heart",
        notes="Manganese carbonate. C38 Love Doctrine heart-field correspondence.",
    ),
    "tugtupite": CrystalProperties(
        name="Tugtupite", formula="Na4AlBeSi4O12Cl",
        q_factor=22_000.0, resonant_band_hz=(7.0, 500_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="tenebrescence node / love-field rare resonator",
        traversal_tier="albedo", chakra="heart",
        notes="Greenland only. Tenebrescence: reversible photochromism. Northern shamanic love stone.",
    ),
    "ulexite": CrystalProperties(
        name="Ulexite", formula="NaCaB5O6(OH)6·5H2O",
        q_factor=8_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="visionary", role="natural fiber optic / psionic light transmission node",
        traversal_tier="albedo", chakra="third_eye",
        notes="TV Rock. Parallel fiber channels transmit images. GAIA optical/psionic architecture analog.",
    ),
    "phenacite": CrystalProperties(
        name="Phenacite", formula="Be2SiO4",
        q_factor=45_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="biological_interface",
        biological_interface="visionary", role="ultra-high frequency psionic transmitter",
        traversal_tier="rubedo", chakra="crown",
        notes="Beryllium silicate. Hardness 7.5-8. Among strongest psionic resonance in crystal traditions.",
    ),

    # ── Special-origin / alchemical compounds ───────────────────────────────
    "quantum_quattro": CrystalProperties(
        name="Quantum Quattro", formula="Shattuckite + Chrysocolla + Dioptase + Malachite + Smoky Quartz",
        q_factor=55_000.0, resonant_band_hz=(32_000.0, 5_000_000.0),
        piezoelectric=True, phononic_class="biological_interface",
        biological_interface="coherence", role="five-force matrix / triple-chakra activation node",
        traversal_tier="multi", chakra="heart",
        ima_classified=False,
        notes="Namibia only. Not IMA-classified — pure alchemical compound designation. "
              "Heart + Throat + Third Eye simultaneous activation. Sometimes called Phoenix Stone.",
    ),
    "super_seven": CrystalProperties(
        name="Super Seven", formula="Amethyst + Cacoxenite + Goethite + Lepidocrocite + Rutile + Smoky Quartz + Clear Quartz",
        q_factor=70_000.0, resonant_band_hz=(32_000.0, 5_000_000.0),
        piezoelectric=True, phononic_class="biological_interface",
        biological_interface="coherence", role="seven-force unified matrix",
        traversal_tier="multi", chakra="crown",
        ima_classified=False,
        notes="Espirito Santo, Brazil only. Also: Melody Stone / Sacred Stone. Not IMA-classified.",
    ),
    "terahertz": CrystalProperties(
        name="Terahertz Stone", formula="Fe (sintered iron meteorite powder)",
        q_factor=15_000.0, resonant_band_hz=(300_000_000_000.0, 3_000_000_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="none", role="synthetic EMR resonator / THz band node",
        traversal_tier="multi", chakra="unassigned",
        ima_classified=False,
        notes="Man-made sintered product. Not naturally occurring. Polish smelting byproduct. "
              "Similar canon classification tier to Opalite.",
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE — DATABASE R–Z ADDITIONS (Issues #549–#556)
# ─────────────────────────────────────────────────────────────────────────────

_DB_R_TO_Z: dict[str, CrystalProperties] = {

    # ── Database R (#549) ────────────────────────────────────────────────────
    "rainbow_moonstone": CrystalProperties(
        name="Rainbow Moonstone", formula="(Ca,Na)(Al,Si)4O8",
        q_factor=28_000.0, resonant_band_hz=(100_000.0, 3_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="adularescence lunar coherence node",
        traversal_tier="albedo", chakra="crown",
    ),
    "rainbow_obsidian": CrystalProperties(
        name="Rainbow Obsidian", formula="SiO2 (volcanic glass, magnetite inclusions)",
        q_factor=12_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="grounding", role="volcanic glass scrying node",
        traversal_tier="nigredo", chakra="root",
    ),
    "rhodonite": CrystalProperties(
        name="Rhodonite", formula="MnSiO3",
        q_factor=18_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="heart-scar healing resonator",
        traversal_tier="albedo", chakra="heart",
    ),
    "rose_de_france_amethyst": CrystalProperties(
        name="Rose de France Amethyst", formula="SiO2 (Fe3+, pale)",
        q_factor=70_000.0, resonant_band_hz=(32_000.0, 800_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="pale-violet Albedo resonator",
        traversal_tier="albedo", chakra="crown",
    ),
    "ruby_in_kyanite": CrystalProperties(
        name="Ruby in Kyanite", formula="Al2O3 (Cr) + Al2SiO5",
        q_factor=45_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="fire + truth dual resonator",
        traversal_tier="rubedo", chakra="throat",
        notes="Ruby (Rubedo fire) + Kyanite (throat truth). Rare combination.",
    ),
    "ruby_in_fuchsite": CrystalProperties(
        name="Ruby in Fuchsite", formula="Al2O3 (Cr) + KAl2(AlSi3)O10(OH)2 (Cr)",
        q_factor=42_000.0, resonant_band_hz=(100_000.0, 8_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="heart-fire in green mica matrix",
        traversal_tier="rubedo", chakra="heart",
    ),
    "ruby_in_zoisite": CrystalProperties(
        name="Ruby in Zoisite", formula="Al2O3 (Cr) + Ca2Al3(SiO4)(Si2O7)O(OH)",
        q_factor=40_000.0, resonant_band_hz=(100_000.0, 8_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="Anyolite / Tanzania heart-fire node",
        traversal_tier="rubedo", chakra="heart",
        notes="Also: Anyolite. Tanzania only. Zoisite matrix distinct from Fuchsite.",
    ),

    # ── Database S (#550) highlights ─────────────────────────────────────────
    "seraphinite": CrystalProperties(
        name="Seraphinite", formula="Mg5Al(AlSi3O10)(OH)8 (Clinochlore, silver chatoyant)",
        q_factor=22_000.0, resonant_band_hz=(7.0, 500_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="angelic coherence interface / heart master healer",
        traversal_tier="albedo", chakra="heart",
        notes="Siberia only. Silver feathery chatoyancy = Seraphim angel wing correspondence.",
    ),
    "shattuckite": CrystalProperties(
        name="Shattuckite", formula="Cu5(SiO3)4(OH)2",
        q_factor=25_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="ionic", role="copper silicate ionic channel node",
        traversal_tier="albedo", chakra="throat",
        notes="Shattuck Mine, Bisbee AZ (1915). Component of Quantum Quattro.",
    ),
    "sodalite": CrystalProperties(
        name="Sodalite", formula="Na8Al6Si6O24Cl2",
        q_factor=20_000.0, resonant_band_hz=(100_000.0, 3_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="coherence", role="fluorescent sodium silicate / UV-active node",
        traversal_tier="albedo", chakra="third_eye",
        notes="UV fluorescence. Yooperlite is sodalite-bearing syenite (see yooperlite).",
    ),
    "spinel": CrystalProperties(
        name="Spinel", formula="MgAl2O4",
        q_factor=35_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="high-hardness structural node",
        traversal_tier="multi", chakra="root",
        notes="Hardness 7.5-8. Historically confused with ruby (Black Prince's Ruby is spinel).",
    ),
    "sulphur": CrystalProperties(
        name="Sulphur", formula="S8",
        q_factor=5_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="grounding", role="elemental sulfur / alchemical fire node",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="TRUEALCHEMY.md Pyrosis/Citrinitas correspondence. Handle carefully — combustible.",
    ),
    "stromatolite": CrystalProperties(
        name="Stromatolite", formula="CaCO3 + organic matter (fossilised cyanobacteria)",
        q_factor=8_000.0, resonant_band_hz=(1.0, 100_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="3.5B year fossil / deep-time biological coherence",
        traversal_tier="nigredo", chakra="root",
        notes="Oldest preserved lifeforms on Earth. Deep-time biological memory anchor.",
    ),

    # ── Database T (#551) highlights ─────────────────────────────────────────
    "turquoise": CrystalProperties(
        name="Turquoise", formula="CuAl6(PO4)4(OH)8·4H2O",
        q_factor=18_000.0, resonant_band_hz=(7.0, 500_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="universal anchor stone / ancient civilisation node",
        traversal_tier="multi", chakra="throat",
        notes="Used across ALL major civilisations (Egypt, Persia, Tibet, Navajo, Aztec, China). "
              "One of the oldest gemstones in recorded history. Never forms crystals — always massive.",
    ),
    "tanzanite": CrystalProperties(
        name="Tanzanite", formula="Ca2Al3(SiO4)(Si2O7)O(OH) (V/Cr)",
        q_factor=35_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="trichroic third-eye resonator",
        traversal_tier="rubedo", chakra="third_eye",
        notes="Zoisite variety. Tanzania only. Trichroic: blue/violet/burgundy depending on axis.",
    ),
    "tektite": CrystalProperties(
        name="Tektite", formula="SiO2 + Al2O3 + MgO + FeO (impact glass)",
        q_factor=20_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="visionary", role="cosmic impact glass / extraterrestrial interface node",
        traversal_tier="multi", chakra="crown",
        notes="Formed by meteorite impacts. Cosmic origin gives extraterrestrial vibrational signature.",
    ),
    "tiger_eye": CrystalProperties(
        name="Tiger's Eye", formula="SiO2 (quartz pseudomorph after crocidolite)",
        q_factor=55_000.0, resonant_band_hz=(32_000.0, 5_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="solar_integration", role="chatoyant solar plexus resonator",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="Fibrous quartz pseudomorph. Chatoyancy from parallel fiber structure.",
    ),
    "topaz": CrystalProperties(
        name="Topaz", formula="Al2SiO4(F,OH)2",
        q_factor=42_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="orthorhombic aluminum silicate resonator",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="Hardness 8 (Mohs reference mineral). Pyroelectric + weakly piezoelectric.",
    ),

    # ── Database U (#552) ────────────────────────────────────────────────────
    "unakite": CrystalProperties(
        name="Unakite", formula="K-feldspar + Epidote + Quartz",
        q_factor=30_000.0, resonant_band_hz=(32_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="coherence", role="integration stone / heart-root balance node",
        traversal_tier="albedo", chakra="heart",
        notes="Unaka Mountains, TN/NC. Polymineral — orthoclase + epidote + quartz.",
    ),
    "uvarovite_garnet": CrystalProperties(
        name="Uvarovite Garnet (U-entry)", formula="Ca3Cr2(SiO4)3",
        q_factor=45_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=False, phononic_class="primary_resonator",
        biological_interface="coherence", role="rarest green garnet / Viriditas resonator",
        traversal_tier="albedo", chakra="heart",
        notes="Canon alias entry for uvarovite already in Tier 1.",
    ),

    # ── Database V (#553) ────────────────────────────────────────────────────
    "vanadinite": CrystalProperties(
        name="Vanadinite", formula="Pb5(VO4)3Cl",
        q_factor=15_000.0, resonant_band_hz=(100_000.0, 3_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="grounding", role="high-density hexagonal fire node",
        traversal_tier="citrinitas", chakra="sacral",
        toxicity_flag=True,
        toxicity_note="Lead-bearing (Pb5). Do not ingest or grind. Wash hands after handling. "
                      "Do not use in elixirs or water infusions. External use only.",
        notes="Morocco, Arizona. Lead vanadate. Specific gravity 6.66-7.10. Hexagonal crystal system.",
    ),
    "vesuvianite": CrystalProperties(
        name="Vesuvianite", formula="Ca19(Al,Mg,Fe)13(SiO4)10(Si2O7)4(OH,F)10",
        q_factor=22_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="coherence", role="multi-element volcanic skarns node",
        traversal_tier="multi", chakra="heart",
        notes="Also: Idocrase. Named for Mount Vesuvius. Broad force spectrum from multi-color range.",
    ),
    "vivianite": CrystalProperties(
        name="Vivianite", formula="Fe3(PO4)2·8H2O",
        q_factor=10_000.0, resonant_band_hz=(1.0, 500_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="grounding", role="Nigredo resonator / transformation-from-death node",
        traversal_tier="nigredo", chakra="root",
        notes="Forms from decomposition of bone and organic matter. "
              "Starts colorless, oxidises to deep blue-green. Deepest Nigredo resonance in database.",
    ),

    # ── Database W (#554) ────────────────────────────────────────────────────
    "wavellite_w": CrystalProperties(
        name="Wavellite (W-entry)", formula="Al3(PO4)2(F,OH)3·5H2O",
        q_factor=10_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="coherence", role="starburst radiating coherence node",
        traversal_tier="albedo", chakra="solar_plexus",
        notes="Canon alias for wavellite already in Tier 2.",
    ),
    "watermelon_tourmaline_w": CrystalProperties(
        name="Watermelon Tourmaline (W-entry)", formula="Elbaite",
        q_factor=48_000.0, resonant_band_hz=(1_000_000.0, 50_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="coherence", role="heart dual resonator",
        traversal_tier="albedo", chakra="heart",
        notes="Canon alias for watermelon_tourmaline in Tier 1.",
    ),
    "witherite": CrystalProperties(
        name="Witherite", formula="BaCO3",
        q_factor=8_000.0, resonant_band_hz=(100_000.0, 2_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="barium carbonate structural node",
        traversal_tier="nigredo", chakra="root",
        toxicity_flag=True,
        toxicity_note="Barium content is toxic. Do NOT ingest, dissolve in water, or handle near food. "
                      "Historically used as rat poison. External viewing only. Keep away from children.",
        notes="Named after William Withering (1741-1799). Orthorhombic. UK, Germany, USA.",
    ),
    "wulfenite": CrystalProperties(
        name="Wulfenite", formula="PbMoO4",
        q_factor=12_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="none", role="lead molybdate tabular collector mineral",
        traversal_tier="citrinitas", chakra="solar_plexus",
        toxicity_flag=True,
        toxicity_note="Lead-bearing (Pb). Do not ingest or grind. Wash hands. "
                      "Do not use in elixirs. External display only.",
        notes="Red Cloud Mine AZ, Los Lamentos Mexico. Named for F.X. von Wulfen (1845).",
    ),

    # ── Database Y (#555) ────────────────────────────────────────────────────
    "yellow_jasper": CrystalProperties(
        name="Yellow Jasper", formula="SiO2 (Fe2O3 inclusions)",
        q_factor=40_000.0, resonant_band_hz=(32_000.0, 3_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="solar_integration", role="ancient travel-protection solar node",
        traversal_tier="citrinitas", chakra="solar_plexus",
        notes="One of oldest protective talismans. Used by shamans across ancient traditions.",
    ),
    "yooperlite": CrystalProperties(
        name="Yooperlite", formula="Syenite with fluorescent Sodalite (Na8Al6Si6O24Cl2)",
        q_factor=15_000.0, resonant_band_hz=(100_000.0, 3_000_000.0),
        piezoelectric=False, phononic_class="biological_interface",
        biological_interface="visionary", role="UV-fluorescent lake stone / hidden light node",
        traversal_tier="albedo", chakra="third_eye",
        ima_classified=False,
        notes="Discovered 2017 by Erik Rintamaki. Lake Superior, Michigan UP beaches. "
              "Yooperlite® is a registered trademark. Scientific: Syenite Clasts Containing Fluorescent Sodalite. "
              "Most recently discovered stone in the full crystal database series.",
    ),
    "yttrium_fluorite": CrystalProperties(
        name="Yttrium Fluorite", formula="(Ca,Y)F2",
        q_factor=25_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="coherence", role="rare high-vibration third-eye node",
        traversal_tier="rubedo", chakra="third_eye",
        notes="Also: Yttrofluorite. Named for Ytterby, Sweden — village that named Y, Yb, Tb, Er.",
    ),

    # ── Database Z (#556) ────────────────────────────────────────────────────
    "zebra_stone": CrystalProperties(
        name="Zebra Stone", formula="SiO2 (microcrystalline jasper, Fe2O3/MnO2 banding)",
        q_factor=35_000.0, resonant_band_hz=(32_000.0, 3_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="grounding", role="Nigredo/Albedo polarity stone",
        traversal_tier="nigredo", chakra="root",
        notes="Black/white banding = direct Nigredo/Albedo duality. TRUEALCHEMY.md traversal correspondence.",
    ),
    "zincite": CrystalProperties(
        name="Zincite", formula="ZnO",
        q_factor=20_000.0, resonant_band_hz=(100_000.0, 10_000_000.0),
        piezoelectric=True, phononic_class="primary_resonator",
        biological_interface="solar_integration", role="zinc oxide sacral fire resonator",
        traversal_tier="citrinitas", chakra="sacral",
        ima_classified=False,
        notes="Most market Zincite is synthetic — Polish smelting chimney deposits. "
              "Natural Zincite: Franklin, NJ only. Named 'red oxide of zinc' 1810 by Archibald Bruce.",
    ),
    "zoisite": CrystalProperties(
        name="Zoisite", formula="Ca2Al3(SiO4)(Si2O7)O(OH)",
        q_factor=30_000.0, resonant_band_hz=(100_000.0, 5_000_000.0),
        piezoelectric=False, phononic_class="phononic_structural",
        biological_interface="coherence", role="shapeshifter mineral / three-variety master node",
        traversal_tier="multi", chakra="heart",
        notes="One mineral → three distinct stones: Tanzanite (blue-violet), Thulite (pink), "
              "Anyolite/Ruby in Zoisite (green/black/red). Reclassified from Epidote family 2006.",
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# ASSEMBLE MASTER DATABASE
# ─────────────────────────────────────────────────────────────────────────────

CRYSTAL_DATABASE: dict[str, CrystalProperties] = {
    **_TIER1,
    **_TIER2,
    **_TIER3,
    **_DB_R_TO_Z,
}

# ─────────────────────────────────────────────────────────────────────────────
# ALIASES — covers all spelling corrections from Issues #549-#556
# ─────────────────────────────────────────────────────────────────────────────

CRYSTAL_ALIASES: dict[str, str] = {
    # Original aliases preserved
    "aluinium nitride": "aln",
    "aluminum nitride": "aln",
    "a l n": "aln",
    "quartz crystal": "quartz",
    # Spelling corrections from Issue #550 (S database)
    "scalpolite": "scapolite",
    "scalenblende": "schalenblende",
    "serapharine": "seraphinite",
    "shattickite": "shattuckite",
    "sichaun quartz": "sichuan_quartz",
    "sleeping beuty": "sleeping_beauty",
    "skaneskin jasper": "snakeskin_jasper",
    "snoq quartz": "snow_quartz",
    "snowflaake obsidian": "snowflake_obsidian",
    "spharlerite": "sphalerite",
    "spoumene": "spodumene",
    "staruolite": "staurolite",
    "strbnite": "stibnite",
    "stichtitie": "stichtite",
    # Spelling corrections from Issue #551 (T database)
    "tidffany stone": "tiffany_stone",
    # Spelling corrections from Issue #552 (U database)
    "ytrium fluorite": "yttrium_fluorite",
    # Spelling corrections from Issue #553 (V database)
    "vanandinite": "vanadinite",
    # Common alternates
    "aln crystal": "aln",
    "clear quartz": "clear_quartz",
    "rose quartz": "rose_quartz",
    "smoky quartz": "smoky_quartz",
    "tangerine quartz": "tangerine_quartz",
    "sichuan quartz": "sichuan_quartz",
    "snow quartz": "snow_quartz",
    "spirit quartz": "spirit_quartz",
    "tourmalinated quartz": "tourmalinated_quartz",
    "rutilated quartz": "rutilated_quartz",
    "black tourmaline": "black_tourmaline",
    "watermelon tourmaline": "watermelon_tourmaline",
    "uvarovite garnet": "uvarovite",
    "rhodolite garnet": "rhodolite_garnet",
    "spessartine garnet": "spessartine_garnet",
    "tsavorite garnet": "tsavorite_garnet",
    "star garnet": "star_garnet",
    "red beryl": "red_beryl",
    "herkimer diamond": "herkimer_diamond",
    "rainbow moonstone": "rainbow_moonstone",
    "rainbow obsidian": "rainbow_obsidian",
    "rose de france": "rose_de_france_amethyst",
    "rose de france amethyst": "rose_de_france_amethyst",
    "ruby in kyanite": "ruby_in_kyanite",
    "ruby in fuchsite": "ruby_in_fuchsite",
    "ruby in zoisite": "ruby_in_zoisite",
    "rainbow lattice sunstone": "rainbow_lattice_sunstone",
    "quantum quattro": "quantum_quattro",
    "super seven": "super_seven",
    "melody stone": "super_seven",
    "sacred stone": "super_seven",
    "phoenix stone": "quantum_quattro",
    "terahertz stone": "terahertz",
    "tv rock": "ulexite",
    "television stone": "ulexite",
    "idocrase": "vesuvianite",
    "anyolite": "ruby_in_zoisite",
    "yellow jasper": "yellow_jasper",
    "zebra stone": "zebra_stone",
    "yttrium fluorite": "yttrium_fluorite",
    "yttrofluorite": "yttrium_fluorite",
    "lithium niobate": "lithium_niobate",
    "tiger eye": "tiger_eye",
    "tigers eye": "tiger_eye",
    "tiger's eye": "tiger_eye",
}

# Normalise all alias keys
CRYSTAL_ALIASES = {k.strip().lower().replace(" ", "_").replace("-", "_"): v
                   for k, v in CRYSTAL_ALIASES.items()}

# ─────────────────────────────────────────────────────────────────────────────
# GROUPS (all three tiers)
# ─────────────────────────────────────────────────────────────────────────────

CRYSTAL_GROUPS: dict[str, list[str]] = {
    "primary_resonator": [
        "quartz", "clear_quartz", "amethyst", "citrine", "rose_quartz",
        "smoky_quartz", "tourmaline", "black_tourmaline", "watermelon_tourmaline",
        "tiger_eye", "topaz", "sapphire", "ruby", "uvarovite",
        "rhodolite_garnet", "spessartine_garnet", "tsavorite_garnet",
        "star_garnet", "red_beryl", "labradorite", "sunstone",
        "rainbow_lattice_sunstone", "kunzite", "hiddenite",
        "tangerine_quartz", "sichuan_quartz", "snow_quartz",
        "spirit_quartz", "tourmalinated_quartz", "rutilated_quartz",
        "tanzanite", "rose_de_france_amethyst", "ruby_in_kyanite",
        "ruby_in_fuchsite", "yellow_jasper", "zebra_stone", "zincite",
    ],
    "phononic_structural": [
        "aln", "calcite", "fluorite", "rutile", "celestite", "apophyllite",
        "stibnite", "wolframite", "scheelite", "lithium_niobate",
        "sphalerite", "sphene", "wavellite", "zircon", "sodalite",
        "spinel", "vesuvianite", "witherite", "wulfenite",
        "yttrium_fluorite", "zoisite",
    ],
    "biological_interface": [
        "selenite", "moldavite", "herkimer_diamond", "shungite",
        "black_tourmaline_ti3", "sugilite", "scolecite", "rhodochrosite",
        "tugtupite", "ulexite", "phenacite", "quantum_quattro",
        "super_seven", "terahertz", "seraphinite", "shattuckite",
        "lepidolite", "tektite", "sulphur", "stromatolite",
        "vanadinite", "vivianite", "turquoise", "unakite",
        "yooperlite", "rainbow_obsidian",
    ],
    "toxic_handle_with_care": [
        "vanadinite", "witherite", "wulfenite",
    ],
    "synthetic_or_non_ima": [
        "quantum_quattro", "super_seven", "terahertz", "zincite",
        "yooperlite",
    ],
    "schumann_resonators": [
        "selenite",
    ],
    "phi_winding_compatible": [
        "quartz", "clear_quartz", "aln", "herkimer_diamond",
        "amethyst", "citrine", "tourmaline", "black_tourmaline",
    ],
    "wireless_power_tier1": [
        "aln", "quartz", "clear_quartz", "herkimer_diamond",
        "amethyst", "citrine",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# ERROR CORRECTION GUARDS
# ─────────────────────────────────────────────────────────────────────────────

def normalize_crystal_name(name: str) -> str:
    """Normalise a crystal name to the CRYSTAL_DATABASE key format."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _nearest_matches(key: str, n: int = 3) -> list[str]:
    all_keys = list(CRYSTAL_DATABASE.keys()) + list(CRYSTAL_ALIASES.keys())
    return difflib.get_close_matches(key, all_keys, n=n, cutoff=0.5)


def resolve_crystal_key(crystal_name: str) -> str:
    """
    Resolve a user-supplied crystal name to a CRYSTAL_DATABASE key.

    Resolution order:
      1. Exact match in CRYSTAL_DATABASE
      2. Exact match in CRYSTAL_ALIASES
      3. Partial substring match in CRYSTAL_DATABASE keys
      4. CrystalNotFoundError with nearest suggestions via difflib

    Raises:
        CrystalNotFoundError: if the crystal cannot be resolved
    """
    key = normalize_crystal_name(crystal_name)

    # 1. Direct database match
    if key in CRYSTAL_DATABASE:
        return key

    # 2. Alias match
    if key in CRYSTAL_ALIASES:
        resolved = CRYSTAL_ALIASES[key]
        if resolved in CRYSTAL_DATABASE:
            return resolved

    # 3. Partial match (e.g. "black tourmaline tier" → "black_tourmaline")
    for db_key in CRYSTAL_DATABASE:
        if key in db_key or db_key in key:
            return db_key

    # 4. Nothing found — suggest nearest
    suggestions = _nearest_matches(key)
    raise CrystalNotFoundError(crystal_name, suggestions)


def validate_crystal(crystal: CrystalProperties) -> list[str]:
    """
    Field-level integrity check for a CrystalProperties record.

    Returns:
        list of error strings (empty = valid)
    """
    errors: list[str] = []
    if not crystal.name:
        errors.append("name is empty")
    if crystal.q_factor <= 0:
        errors.append(f"q_factor must be > 0, got {crystal.q_factor}")
    band_min, band_max = crystal.resonant_band_hz
    if band_min >= band_max:
        errors.append(
            f"resonant_band_hz min ({band_min}) must be < max ({band_max})"
        )
    if crystal.phononic_class not in {
        "primary_resonator", "phononic_structural", "biological_interface"
    }:
        errors.append(f"unknown phononic_class: '{crystal.phononic_class}'")
    return errors


def validate_all_crystals() -> dict[str, list[str]]:
    """
    Run validate_crystal() over every entry in CRYSTAL_DATABASE.

    Returns:
        dict of {crystal_key: [error, ...]} for any entry with errors.
        Empty dict = all crystals are valid.
    """
    failures: dict[str, list[str]] = {}
    for key, crystal in CRYSTAL_DATABASE.items():
        errs = validate_crystal(crystal)
        if errs:
            failures[key] = errs
    return failures


def list_all_crystals() -> list[str]:
    """Return sorted list of all canonical crystal keys in CRYSTAL_DATABASE."""
    return sorted(CRYSTAL_DATABASE.keys())


def list_crystals_by_group(group_name: str) -> list[str]:
    """Return all crystal keys in a named CRYSTAL_GROUPS category."""
    return CRYSTAL_GROUPS.get(group_name, [])


def get_toxic_crystals() -> list[CrystalProperties]:
    """Return all crystals marked with toxicity_flag=True."""
    return [c for c in CRYSTAL_DATABASE.values() if c.toxicity_flag]


def get_non_ima_crystals() -> list[CrystalProperties]:
    """Return all crystals not classified by the IMA (synthetic or trade names)."""
    return [c for c in CRYSTAL_DATABASE.values() if not c.ima_classified]


# ─────────────────────────────────────────────────────────────────────────────
# CORE LOOKUP (error-corrected)
# ─────────────────────────────────────────────────────────────────────────────

def get_crystal_properties(crystal_name: str) -> CrystalProperties:
    """
    Return the full CrystalProperties record for a crystal by name.

    Raises:
        CrystalNotFoundError with nearest-match suggestions on failure.
    """
    return CRYSTAL_DATABASE[resolve_crystal_key(crystal_name)]


def get_crystal_q_factor(crystal_name: str) -> float:
    """Return the Q-factor for a named crystal."""
    return get_crystal_properties(crystal_name).q_factor


# ─────────────────────────────────────────────────────────────────────────────
# SELECTION
# ─────────────────────────────────────────────────────────────────────────────

def select_resonator(
    target_frequency: float,
    min_q: float = 0.0,
    exclude_toxic: bool = False,
    require_piezoelectric: bool = False,
) -> list[dict[str, Any]]:
    """
    Return crystals whose resonant band covers target_frequency
    and whose Q-factor meets or exceeds min_q, sorted by Q descending.

    Args:
        target_frequency:      operating frequency in Hz
        min_q:                 minimum acceptable Q-factor (default 0 = no filter)
        exclude_toxic:         if True, exclude toxicity_flag=True crystals
        require_piezoelectric: if True, only return piezoelectric crystals

    Returns:
        list of dicts with name, formula, q_factor, role, phononic_class,
        traversal_tier, chakra, toxicity_flag, ima_classified
    """
    if target_frequency <= 0:
        raise ValueError(f"target_frequency must be > 0 Hz, got {target_frequency}")

    candidates = []
    for crystal in CRYSTAL_DATABASE.values():
        band_min, band_max = crystal.resonant_band_hz
        if band_min <= target_frequency <= band_max and crystal.q_factor >= min_q:
            if exclude_toxic and crystal.toxicity_flag:
                continue
            if require_piezoelectric and not crystal.piezoelectric:
                continue
            candidates.append({
                "name":            crystal.name,
                "formula":         crystal.formula,
                "q_factor":        crystal.q_factor,
                "role":            crystal.role,
                "phononic_class":  crystal.phononic_class,
                "traversal_tier":  crystal.traversal_tier,
                "chakra":          crystal.chakra,
                "toxicity_flag":   crystal.toxicity_flag,
                "ima_classified":  crystal.ima_classified,
            })
    return sorted(candidates, key=lambda item: item["q_factor"], reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# BIOLOGICAL SAFETY  (EMBODIMENT_LAYER.md)
# ─────────────────────────────────────────────────────────────────────────────

# Safe ISM bands from EMBODIMENT_LAYER.md
_SAFE_BANDS_HZ: list[tuple[float, float, str]] = [
    (7.5, 8.1,      "Schumann fundamental — coherence-enhancing"),
    (6_780_000.0,   6_780_000.0,  "ISM 6.78 MHz — established medical/industrial"),
    (13_560_000.0,  13_560_000.0, "ISM 13.56 MHz — NFC/RFID/medical"),
    (27_120_000.0,  27_120_000.0, "ISM 27.12 MHz — diathermy, established safe"),
]

_POWER_DENSITY_LIMIT_MW_CM2 = 1.0   # ICNIRP / FCC hard cap from wireless_power_sim.py


def biological_safety_rating(
    crystal_name: str,
    proximity_m: float = 1.0,
    power_density_mw_cm2: float = 0.0,
) -> dict[str, Any]:
    """
    Full biological safety assessment for a crystal at given proximity and
    optional power density.

    The Operator is the most sensitive instrument in the system.
    Protected first, always. (Architect Protocol, Issue #578)

    Args:
        crystal_name:          crystal to assess
        proximity_m:           distance from Operator in metres
        power_density_mw_cm2:  power density at Operator location (optional)

    Returns:
        {crystal, score, flags, proximity_m, power_density_mw_cm2}
        score: "safe" | "caution" | "danger"
    """
    crystal = get_crystal_properties(crystal_name)
    score   = "safe"
    flags: list[str] = []

    # 1. Toxicity check — highest priority
    if crystal.toxicity_flag:
        score = "danger"
        flags.append(f"⚠ TOXICITY: {crystal.toxicity_note}")

    # 2. Schumann band proximity
    if crystal.biological_interface == "schumann_coherence" and proximity_m < 0.25:
        if score == "safe":
            score = "caution"
        flags.append(
            f"Selenite resonates near Schumann band (7-8.5 Hz). "
            f"Proximity {proximity_m:.2f}m < 0.25m introduces low-frequency biological interface risk."
        )

    # 3. Ultra-high-Q near-field
    if crystal.q_factor >= 100_000 and proximity_m < 0.10:
        if score == "safe":
            score = "caution"
        flags.append(
            f"Very-high-Q crystal ({crystal.name}, Q={crystal.q_factor:,.0f}) "
            f"at {proximity_m:.2f}m < 0.10m: near-field power density caution."
        )

    # 4. Power density cap (ICNIRP)
    if power_density_mw_cm2 > _POWER_DENSITY_LIMIT_MW_CM2:
        score = "danger"
        flags.append(
            f"Power density {power_density_mw_cm2:.3f} mW/cm² exceeds "
            f"ICNIRP/FCC hard cap of {_POWER_DENSITY_LIMIT_MW_CM2} mW/cm²."
        )

    # 5. Non-IMA / synthetic note
    if not crystal.ima_classified:
        flags.append(
            f"Non-IMA crystal ({crystal.name}): synthetic or alchemical compound — "
            f"physical properties less predictable than natural minerals."
        )

    return {
        "crystal":               crystal.name,
        "score":                 score,
        "flags":                 flags,
        "proximity_m":           proximity_m,
        "power_density_mw_cm2":  power_density_mw_cm2,
    }


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION HOOK  → wireless_power_sim.py
# ─────────────────────────────────────────────────────────────────────────────

def crystal_q_override(crystal_name: str) -> float:
    """
    Primary integration hook for wireless_power_sim.simulate_coil_pair().

    Usage:
        from crystal_resonance import crystal_q_override
        result = simulate_coil_pair(tx, rx, freq_hz, distance_m,
                                    crystal_q_override=crystal_q_override("AlN"))

    Raises CrystalNotFoundError (with suggestions) instead of bare KeyError.
    """
    return get_crystal_q_factor(crystal_name)


# ─────────────────────────────────────────────────────────────────────────────
# CLASS WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

class CrystalResonatorLayer:
    """
    Dependency-injectable wrapper around the crystal database functions.
    Useful when the GAIA-OS backend needs to swap in a custom database
    or a mock during testing.

    Supports Parts 2-5 (design_grid, simulate_crystal_node,
    schumann_coherence_check) as those methods are added in subsequent commits.
    """

    def __init__(
        self,
        database: Optional[dict[str, CrystalProperties]] = None,
    ) -> None:
        self.database = database or CRYSTAL_DATABASE

    def q_factor(self, crystal_name: str) -> float:
        return get_crystal_q_factor(crystal_name)

    def select(
        self,
        target_frequency: float,
        min_q: float = 0.0,
        exclude_toxic: bool = False,
        require_piezoelectric: bool = False,
    ) -> list[dict[str, Any]]:
        return select_resonator(
            target_frequency, min_q,
            exclude_toxic=exclude_toxic,
            require_piezoelectric=require_piezoelectric,
        )

    def q_for_wireless_power(self, crystal_name: str) -> float:
        """Alias of crystal_q_override() for use inside the app layer."""
        return crystal_q_override(crystal_name)

    def safety(
        self,
        crystal_name: str,
        proximity_m: float = 1.0,
        power_density_mw_cm2: float = 0.0,
    ) -> dict[str, Any]:
        return biological_safety_rating(
            crystal_name, proximity_m, power_density_mw_cm2
        )

    def validate_all(self) -> dict[str, list[str]]:
        return validate_all_crystals()


def resonator_group(group_name: str) -> list[CrystalProperties]:
    """Return all crystals in a named CRYSTAL_GROUPS category."""
    keys = CRYSTAL_GROUPS.get(group_name, [])
    return [CRYSTAL_DATABASE[k] for k in keys if k in CRYSTAL_DATABASE]


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION SUITE  (run directly: python crystal_resonance.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ISM_6_78_MHZ = 6.78e6

    print("=" * 70)
    print("GAIA-OS  crystal_resonance.py  Part 1 — Full A-Z Database")
    print("Issue #558 | Issues #534-#556 | Error Correction Guards")
    print("=" * 70)

    # ── 1. Database integrity ─────────────────────────────────────────────
    print(f"\n── Database Size: {len(CRYSTAL_DATABASE)} entries ──")
    failures = validate_all_crystals()
    if failures:
        print(f"  ❌ VALIDATION FAILURES: {len(failures)}")
        for key, errs in failures.items():
            print(f"    {key}: {errs}")
    else:
        print("  ✅ All crystal entries passed field-level validation.")

    # ── 2. Toxicity flags ─────────────────────────────────────────────────
    print("\n── Toxicity Flags (EMBODIMENT_LAYER.md) ──")
    for c in get_toxic_crystals():
        print(f"  ⚠  {c.name}: {c.toxicity_note[:80]}...")

    # ── 3. Non-IMA entries ────────────────────────────────────────────────
    print("\n── Non-IMA / Synthetic / Alchemical Compounds ──")
    for c in get_non_ima_crystals():
        print(f"  ◆  {c.name}: {c.notes[:80]}...")

    # ── 4. Resonator selection at 6.78 MHz ───────────────────────────────
    print(f"\n── Top resonators at {ISM_6_78_MHZ/1e6:.2f} MHz (ISM, min Q=50,000) ──")
    for entry in select_resonator(ISM_6_78_MHZ, min_q=50_000, exclude_toxic=True):
        print(f"  {entry['name']:<28} Q={entry['q_factor']:>10,.0f}  {entry['phononic_class']}")

    # ── 5. Error correction guard demo ───────────────────────────────────
    print("\n── Error Correction Guard Demo ──")
    test_names = [
        "Quartz", "AlN", "rose quartz", "terahertz stone",
        "tiger's eye", "yttrofluorite", "anyolite",
    ]
    for name in test_names:
        try:
            q = crystal_q_override(name)
            props = get_crystal_properties(name)
            print(f"  ✅ '{name}' → {props.name} (Q={q:,.0f})")
        except CrystalNotFoundError as e:
            print(f"  ❌ {e}")

    # ── 6. Intentional bad name → helpful error ───────────────────────────
    print("\n── CrystalNotFoundError with suggestions ──")
    try:
        get_crystal_properties("amthyest")
    except CrystalNotFoundError as e:
        print(f"  Caught: {e}")

    # ── 7. Biological safety checks ────────────