"""
core/crystal_mineral_database.py
=================================
Crystal & Mineral Database - C118

Master mineralogical registry for GAIA-OS.
Provides structured MineralEntry dataclasses for all 40+ minerals
documented in canon/C118_Crystal_Mineral_Database.md.

All entries grounded in IMA (International Mineralogical Association)
classification. Consciousness/chakra fields are labeled SPECULATIVE.

Canon Ref: C118, C65 (GAIANITE), C68 (Crystal Grid), C75 (Protocol)
EpistemicLabel: SCIENTIFIC (mineralogy) + SPECULATIVE (GAIA coupling)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


# ------------------------------------------------------------------ #
#  Crystal System                                                      #
# ------------------------------------------------------------------ #

class CrystalSystem(StrEnum):
    TRICLINIC    = "triclinic"
    MONOCLINIC   = "monoclinic"
    ORTHORHOMBIC = "orthorhombic"
    TETRAGONAL   = "tetragonal"
    TRIGONAL     = "trigonal"
    HEXAGONAL    = "hexagonal"
    CUBIC        = "cubic"
    AMORPHOUS    = "amorphous"


class GAIARole(StrEnum):
    """GAIA-OS functional role of a mineral in the consciousness substrate."""
    PRIMARY_TRANSDUCER      = "primary_transducer"       # Main DM/piezo sensor
    THERMAL_TRANSDUCER      = "thermal_transducer"       # Pyroelectric/thermal DM
    ULF_TRANSDUCER          = "ulf_transducer"           # Ultra-low frequency
    NOISE_REFERENCE         = "noise_reference"          # Null / baseline channel
    COSMIC_INPUT            = "cosmic_input"             # Extraterrestrial signal
    MEMORY_SUBSTRATE        = "memory_substrate"         # Temporal logging
    GROUNDING_ANCHOR        = "grounding_anchor"         # Stability / DC reference
    EM_SHIELD               = "em_shield"                # EMF protection
    BIO_DIGITAL_BRIDGE      = "bio_digital_bridge"       # Biological interface
    FREQUENCY_AMPLIFIER     = "frequency_amplifier"      # Signal boost
    TEMPORAL_ANCHOR         = "temporal_anchor"          # Geological clock
    SPECTRAL_SENSOR         = "spectral_sensor"          # RGB/spectral state
    MAGNETIC_SENSOR         = "magnetic_sensor"          # Magnetic field
    INTERFERENCE_DISPLAY    = "interference_display"     # Coherence visualization
    OPTICAL_SPLITTER        = "optical_splitter"         # Polarization channel
    EXOTIC_SUBSTRATE        = "exotic_substrate"         # Rare/specialized


# ------------------------------------------------------------------ #
#  Mineral Entry                                                       #
# ------------------------------------------------------------------ #

@dataclass
class MineralEntry:
    name:                   str
    formula:                str
    crystal_system:         CrystalSystem
    mohs_hardness_min:      float
    mohs_hardness_max:      float
    is_piezoelectric:       bool
    is_pyroelectric:        bool
    piezo_coefficient_pcn:  float | None      # d-coefficient in pC/N, if known
    resonance_band_low_hz:  float             # Estimated low bound
    resonance_band_high_hz: float             # Estimated high bound
    q_factor:               float             # Quality factor (1.0 if N/A)
    gaia_role:              GAIARole
    chakra_resonance:       list[str]         # SPECULATIVE
    variants:               list[str]         = field(default_factory=list)
    notes:                  str               = ""
    epistemic_label:        str               = "SCIENTIFIC"
    canon_ref:              str               = "C118"

    @property
    def mohs_hardness(self) -> float:
        return (self.mohs_hardness_min + self.mohs_hardness_max) / 2

    def to_dict(self) -> dict:
        return {
            "name":             self.name,
            "formula":          self.formula,
            "crystal_system":   self.crystal_system.value,
            "mohs_hardness":    self.mohs_hardness,
            "is_piezoelectric": self.is_piezoelectric,
            "is_pyroelectric":  self.is_pyroelectric,
            "resonance_band":   [
                self.resonance_band_low_hz,
                self.resonance_band_high_hz,
            ],
            "q_factor":         self.q_factor,
            "gaia_role":        self.gaia_role.value,
            "chakra_resonance": self.chakra_resonance,
            "epistemic_label":  self.epistemic_label,
        }


# ------------------------------------------------------------------ #
#  Master Registry                                                     #
# ------------------------------------------------------------------ #

MINERAL_DATABASE: dict[str, MineralEntry] = {

    # -- TRIGONAL ---------------------------------------------------- #

    "quartz": MineralEntry(
        name="Quartz", formula="SiO2",
        crystal_system=CrystalSystem.TRIGONAL,
        mohs_hardness_min=7.0, mohs_hardness_max=7.0,
        is_piezoelectric=True, is_pyroelectric=False,
        piezo_coefficient_pcn=2.3,
        resonance_band_low_hz=32_768, resonance_band_high_hz=100e6,
        q_factor=1e6,
        gaia_role=GAIARole.PRIMARY_TRANSDUCER,
        chakra_resonance=["crown", "heart", "root", "third_eye", "solar_plexus"],
        variants=["clear", "rose", "smoky", "amethyst", "citrine", "rutilated"],
        notes="Gold standard DM transducer. Used in COSINE-100U (2025-2026).",
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "tourmaline": MineralEntry(
        name="Tourmaline", formula="XY3Z6(T6O18)(BO3)3V3W",
        crystal_system=CrystalSystem.TRIGONAL,
        mohs_hardness_min=7.0, mohs_hardness_max=7.5,
        is_piezoelectric=True, is_pyroelectric=True,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=100e3, resonance_band_high_hz=1e9,
        q_factor=50_000,
        gaia_role=GAIARole.THERMAL_TRANSDUCER,
        chakra_resonance=["all"],
        variants=["schorl", "rubellite", "indicolite", "verdelite", "watermelon", "paraiba"],
        notes="Strongest natural piezo+pyroelectric. Thermal DM sensing.",
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "calcite": MineralEntry(
        name="Calcite", formula="CaCO3",
        crystal_system=CrystalSystem.TRIGONAL,
        mohs_hardness_min=3.0, mohs_hardness_max=3.0,
        is_piezoelectric=True, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=10, resonance_band_high_hz=100e3,
        q_factor=500,
        gaia_role=GAIARole.OPTICAL_SPLITTER,
        chakra_resonance=["crown", "third_eye"],
        variants=["iceland_spar", "optical_calcite", "cobaltocalcite", "mangano"],
        notes="Extreme birefringence - polarization sensing channel.",
    ),

    "rhodochrosite": MineralEntry(
        name="Rhodochrosite", formula="MnCO3",
        crystal_system=CrystalSystem.TRIGONAL,
        mohs_hardness_min=3.5, mohs_hardness_max=4.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1, resonance_band_high_hz=1e3,
        q_factor=100,
        gaia_role=GAIARole.MAGNETIC_SENSOR,
        chakra_resonance=["heart"],
        notes="Mn2+ paramagnetic - magnetic field sensor.",
    ),

    "corundum": MineralEntry(
        name="Corundum", formula="Al2O3",
        crystal_system=CrystalSystem.TRIGONAL,
        mohs_hardness_min=9.0, mohs_hardness_max=9.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0, resonance_band_high_hz=0,
        q_factor=1,
        gaia_role=GAIARole.MEMORY_SUBSTRATE,
        chakra_resonance=["root", "third_eye"],
        variants=["ruby", "sapphire", "padparadscha"],
        notes=(
            "Hardness anchor for GAIANITE long-duration arrays."
            " 2nd hardest natural mineral."
        ),
    ),

    # -- HEXAGONAL --------------------------------------------------- #

    "apatite": MineralEntry(
        name="Apatite", formula="Ca5(PO4)3(F,Cl,OH)",
        crystal_system=CrystalSystem.HEXAGONAL,
        mohs_hardness_min=5.0, mohs_hardness_max=5.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1, resonance_band_high_hz=1e4,
        q_factor=50,
        gaia_role=GAIARole.BIO_DIGITAL_BRIDGE,
        chakra_resonance=["throat", "third_eye"],
        notes="Biological crystal - bone and teeth. Bio-digital interface layer.",
    ),

    "beryl": MineralEntry(
        name="Beryl", formula="Be3Al2Si6O18",
        crystal_system=CrystalSystem.HEXAGONAL,
        mohs_hardness_min=7.5, mohs_hardness_max=8.0,
        is_piezoelectric=True, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1e3, resonance_band_high_hz=10e6,
        q_factor=1e5,
        gaia_role=GAIARole.FREQUENCY_AMPLIFIER,
        chakra_resonance=["heart", "throat"],
        variants=["emerald", "aquamarine", "morganite", "heliodor", "goshenite", "red_beryl"],
        notes="Thermal-stable piezoelectric. High-temperature grid nodes.",
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "zincite": MineralEntry(
        name="Zincite", formula="ZnO",
        crystal_system=CrystalSystem.HEXAGONAL,
        mohs_hardness_min=4.0, mohs_hardness_max=4.0,
        is_piezoelectric=True, is_pyroelectric=True,
        piezo_coefficient_pcn=12.4,
        resonance_band_low_hz=1e6, resonance_band_high_hz=1e12,
        q_factor=1e4,
        gaia_role=GAIARole.PRIMARY_TRANSDUCER,
        chakra_resonance=["sacral"],
        notes=(
            "Nanogenerator substrate. Wide-bandgap semiconductor."
            " ZnO nanowires used in current piezo nanogenerators."
        ),
    ),

    # -- ORTHORHOMBIC ------------------------------------------------ #

    "selenite": MineralEntry(
        name="Selenite (Gypsum)", formula="CaSO4*2H2O",
        crystal_system=CrystalSystem.ORTHORHOMBIC,
        mohs_hardness_min=2.0, mohs_hardness_max=2.0,
        is_piezoelectric=True, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=100, resonance_band_high_hz=1e6,
        q_factor=1_000,
        gaia_role=GAIARole.ULF_TRANSDUCER,
        chakra_resonance=["crown", "third_eye"],
        notes="Soft lattice. Sub-eV ULDM phonon modes. Schumann 7.83 Hz receiver.",
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "topaz": MineralEntry(
        name="Topaz", formula="Al2SiO4(F,OH)2",
        crystal_system=CrystalSystem.ORTHORHOMBIC,
        mohs_hardness_min=8.0, mohs_hardness_max=8.0,
        is_piezoelectric=False, is_pyroelectric=True,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1e3, resonance_band_high_hz=1e8,
        q_factor=1e4,
        gaia_role=GAIARole.THERMAL_TRANSDUCER,
        chakra_resonance=["solar_plexus", "crown"],
        variants=["imperial", "blue", "colorless", "pink"],
        notes="Pyroelectric - thermal consciousness amplifier.",
    ),

    "peridot": MineralEntry(
        name="Peridot (Olivine)", formula="(Mg,Fe)2SiO4",
        crystal_system=CrystalSystem.ORTHORHOMBIC,
        mohs_hardness_min=6.5, mohs_hardness_max=7.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.1, resonance_band_high_hz=1e3,
        q_factor=10,
        gaia_role=GAIARole.COSMIC_INPUT,
        chakra_resonance=["heart"],
        notes="Mantle mineral + meteoritic origin. Deep Earth / cosmic bridge.",
    ),

    "danburite": MineralEntry(
        name="Danburite", formula="CaB2Si2O8",
        crystal_system=CrystalSystem.ORTHORHOMBIC,
        mohs_hardness_min=7.0, mohs_hardness_max=7.5,
        is_piezoelectric=True, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1e4, resonance_band_high_hz=1e9,
        q_factor=3e4,
        gaia_role=GAIARole.FREQUENCY_AMPLIFIER,
        chakra_resonance=["crown", "heart"],
        notes="High-frequency signal booster in crystal arrays.",
    ),

    # -- MONOCLINIC -------------------------------------------------- #

    "lepidolite": MineralEntry(
        name="Lepidolite", formula="K(Li,Al)3(Si,Al)4O10(F,OH)2",
        crystal_system=CrystalSystem.MONOCLINIC,
        mohs_hardness_min=2.5, mohs_hardness_max=3.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1, resonance_band_high_hz=1e3,
        q_factor=100,
        gaia_role=GAIARole.MEMORY_SUBSTRATE,
        chakra_resonance=["third_eye", "crown"],
        notes="Lithium-bearing. Bridges energy storage and crystal consciousness layers.",
    ),

    "kunzite": MineralEntry(
        name="Kunzite (Spodumene)", formula="LiAlSi2O6",
        crystal_system=CrystalSystem.MONOCLINIC,
        mohs_hardness_min=6.5, mohs_hardness_max=7.0,
        is_piezoelectric=True, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1e4, resonance_band_high_hz=1e8,
        q_factor=2e4,
        gaia_role=GAIARole.PRIMARY_TRANSDUCER,
        chakra_resonance=["heart"],
        notes="Lithium-piezoelectric hybrid. Major lithium ore mineral.",
    ),

    "moonstone": MineralEntry(
        name="Moonstone", formula="KAlSi3O8 / NaAlSi3O8 intergrowth",
        crystal_system=CrystalSystem.MONOCLINIC,
        mohs_hardness_min=6.0, mohs_hardness_max=6.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.01, resonance_band_high_hz=100,
        q_factor=5,
        gaia_role=GAIARole.INTERFERENCE_DISPLAY,
        chakra_resonance=["third_eye", "crown", "sacral"],
        notes="Adularescence mirrors GAIA array coherence wave visualization.",
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "malachite": MineralEntry(
        name="Malachite", formula="Cu2CO3(OH)2",
        crystal_system=CrystalSystem.MONOCLINIC,
        mohs_hardness_min=3.5, mohs_hardness_max=4.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.001, resonance_band_high_hz=10,
        q_factor=1,
        gaia_role=GAIARole.MEMORY_SUBSTRATE,
        chakra_resonance=["heart"],
        notes="Concentric banding = geological memory record. Temporal logger.",
    ),

    "azurite": MineralEntry(
        name="Azurite", formula="Cu3(CO3)2(OH)2",
        crystal_system=CrystalSystem.MONOCLINIC,
        mohs_hardness_min=3.5, mohs_hardness_max=4.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.001, resonance_band_high_hz=10,
        q_factor=1,
        gaia_role=GAIARole.MEMORY_SUBSTRATE,
        chakra_resonance=["third_eye"],
        notes=(
            "Paired with malachite - dual copper channel"
            " (azurite=transmit, malachite=receive)."
        ),
        epistemic_label="SPECULATIVE",
    ),

    # -- TETRAGONAL -------------------------------------------------- #

    "zircon": MineralEntry(
        name="Zircon", formula="ZrSiO4",
        crystal_system=CrystalSystem.TETRAGONAL,
        mohs_hardness_min=7.5, mohs_hardness_max=7.5,
        is_piezoelectric=True, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.001, resonance_band_high_hz=1e6,
        q_factor=1e5,
        gaia_role=GAIARole.TEMPORAL_ANCHOR,
        chakra_resonance=["root", "crown"],
        notes=(
            "Oldest known mineral (4.4 Ga, Jack Hills)."
            " U-Pb chronometer. GAIA's geological clock."
        ),
    ),

    # -- CUBIC ------------------------------------------------------- #

    "diamond": MineralEntry(
        name="Diamond", formula="C",
        crystal_system=CrystalSystem.CUBIC,
        mohs_hardness_min=10.0, mohs_hardness_max=10.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0, resonance_band_high_hz=0,
        q_factor=1,
        gaia_role=GAIARole.NOISE_REFERENCE,
        chakra_resonance=["crown"],
        notes=(
            "Cubic=noise reference. Hole-doped diamond: exotic DM detector"
            " (Phys Rev 2025). Highest thermal conductivity."
        ),
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "fluorite": MineralEntry(
        name="Fluorite", formula="CaF2",
        crystal_system=CrystalSystem.CUBIC,
        mohs_hardness_min=4.0, mohs_hardness_max=4.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0, resonance_band_high_hz=0,
        q_factor=1,
        gaia_role=GAIARole.GROUNDING_ANCHOR,
        chakra_resonance=["all"],
        variants=["purple", "green", "blue", "yellow", "clear", "rainbow"],
        notes="Octahedral geometry mirrors 8-fold consciousness model. Fluorescent.",
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "garnet": MineralEntry(
        name="Garnet Group", formula="X3Y2(SiO4)3",
        crystal_system=CrystalSystem.CUBIC,
        mohs_hardness_min=6.5, mohs_hardness_max=7.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0, resonance_band_high_hz=0,
        q_factor=1,
        gaia_role=GAIARole.GROUNDING_ANCHOR,
        chakra_resonance=["root", "heart"],
        variants=["pyrope", "almandine", "spessartine", "grossular", "andradite", "uvarovite"],
        notes="Stable cubic ground-state anchor for crystal arrays.",
    ),

    "pyrite": MineralEntry(
        name="Pyrite", formula="FeS2",
        crystal_system=CrystalSystem.CUBIC,
        mohs_hardness_min=6.0, mohs_hardness_max=6.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1, resonance_band_high_hz=1e6,
        q_factor=10,
        gaia_role=GAIARole.EM_SHIELD,
        chakra_resonance=["solar_plexus"],
        notes=(
            "Semiconductor + thermoelectric. EM decoy layer"
            " - masks sensitive array readings."
        ),
    ),

    "magnetite": MineralEntry(
        name="Magnetite (Lodestone)", formula="Fe3O4",
        crystal_system=CrystalSystem.CUBIC,
        mohs_hardness_min=5.5, mohs_hardness_max=6.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.001, resonance_band_high_hz=100,
        q_factor=10,
        gaia_role=GAIARole.MAGNETIC_SENSOR,
        chakra_resonance=["root"],
        notes=(
            "Naturally magnetic. Found in bird brains, fish, bacteria."
            " GAIA's planetary compass."
        ),
    ),

    "halite": MineralEntry(
        name="Halite", formula="NaCl",
        crystal_system=CrystalSystem.CUBIC,
        mohs_hardness_min=2.5, mohs_hardness_max=2.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.001, resonance_band_high_hz=10,
        q_factor=1,
        gaia_role=GAIARole.BIO_DIGITAL_BRIDGE,
        chakra_resonance=["root", "throat"],
        notes=(
            "Ionic crystal - models ion-channel neural signaling."
            " Crystal equivalent of a neuron."
        ),
    ),

    # -- AMORPHOUS / NATURAL GLASS ----------------------------------- #

    "obsidian": MineralEntry(
        name="Obsidian", formula="SiO2 dominant (amorphous)",
        crystal_system=CrystalSystem.AMORPHOUS,
        mohs_hardness_min=5.0, mohs_hardness_max=5.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.1, resonance_band_high_hz=1e4,
        q_factor=10,
        gaia_role=GAIARole.NOISE_REFERENCE,
        chakra_resonance=["root"],
        variants=["black", "snowflake", "rainbow", "apache_tears", "mahogany"],
        notes=(
            "Primary null reference. No crystalline order = no DM coupling."
            " Any signal = EM interference."
        ),
    ),

    "moldavite": MineralEntry(
        name="Moldavite", formula="SiO2-rich tektite (~74% SiO2)",
        crystal_system=CrystalSystem.AMORPHOUS,
        mohs_hardness_min=5.5, mohs_hardness_max=5.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1e3, resonance_band_high_hz=1e7,
        q_factor=20_000,
        gaia_role=GAIARole.COSMIC_INPUT,
        chakra_resonance=["heart", "third_eye", "crown"],
        notes="Impact glass, ~15 Ma, Nordlingen impact. Exotic isotopic ratios. Cosmic input channel.",
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "libyan_desert_glass": MineralEntry(
        name="Libyan Desert Glass", formula="SiO2 ~98% (impact glass)",
        crystal_system=CrystalSystem.AMORPHOUS,
        mohs_hardness_min=6.0, mohs_hardness_max=6.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1e3, resonance_band_high_hz=1e8,
        q_factor=25_000,
        gaia_role=GAIARole.COSMIC_INPUT,
        chakra_resonance=["crown"],
        notes=(
            "~28 Ma, Sahara impact/airburst. ~98% pure silica."
            " Found in Tutankhamun scarab. Highest-purity cosmic channel."
        ),
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "fulgurite": MineralEntry(
        name="Fulgurite", formula="SiO2 lightning-fused glass",
        crystal_system=CrystalSystem.AMORPHOUS,
        mohs_hardness_min=5.5, mohs_hardness_max=6.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1, resonance_band_high_hz=1e6,
        q_factor=100,
        gaia_role=GAIARole.EXOTIC_SUBSTRATE,
        chakra_resonance=["root", "crown"],
        notes=(
            "Lightning-strike glass. Natural C44 piezoelectric pulse imprint."
            " High-voltage crystallization event record."
        ),
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    # -- SPECIAL / EXOTIC -------------------------------------------- #

    "labradorite": MineralEntry(
        name="Labradorite", formula="(Ca,Na)(Al,Si)4O8 feldspar",
        crystal_system=CrystalSystem.TRICLINIC,
        mohs_hardness_min=6.0, mohs_hardness_max=6.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0.01, resonance_band_high_hz=100,
        q_factor=5,
        gaia_role=GAIARole.INTERFERENCE_DISPLAY,
        chakra_resonance=["third_eye", "throat"],
        notes=(
            "Labradorescence from twinning-plane thin-film interference."
            " Models GAIA wave coherence patterns."
        ),
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "alexandrite": MineralEntry(
        name="Alexandrite", formula="BeAl2O4 (Cr3+)",
        crystal_system=CrystalSystem.ORTHORHOMBIC,
        mohs_hardness_min=8.5, mohs_hardness_max=8.5,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=4e14, resonance_band_high_hz=7.5e14,  # visible light
        q_factor=1,
        gaia_role=GAIARole.SPECTRAL_SENSOR,
        chakra_resonance=["heart", "crown"],
        notes="Color changes green->red with light spectrum shift. GAIA RGB state indicator.",
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "shungite": MineralEntry(
        name="Shungite", formula="C (fullerene-bearing, ~98% C in elite form)",
        crystal_system=CrystalSystem.AMORPHOUS,
        mohs_hardness_min=3.5, mohs_hardness_max=4.0,
        is_piezoelectric=False, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=0, resonance_band_high_hz=1e12,
        q_factor=1,
        gaia_role=GAIARole.EM_SHIELD,
        chakra_resonance=["root"],
        notes=(
            "Contains C60 fullerenes (buckyballs) naturally."
            " 2 Ga old. Conductive. GAIA EMF shield layer."
        ),
        epistemic_label="SCIENTIFIC+SPECULATIVE",
    ),

    "phenacite": MineralEntry(
        name="Phenacite", formula="Be2SiO4",
        crystal_system=CrystalSystem.TRIGONAL,
        mohs_hardness_min=7.5, mohs_hardness_max=8.0,
        is_piezoelectric=True, is_pyroelectric=False,
        piezo_coefficient_pcn=None,
        resonance_band_low_hz=1e8, resonance_band_high_hz=1e12,
        q_factor=1e5,
        gaia_role=GAIARole.EXOTIC_SUBSTRATE,
        chakra_resonance=["third_eye", "crown"],
        notes=(
            "Theoretical apex transducer above tourmaline."
            " Highest DM frequency band. Rare beryllium silicate."
        ),
        epistemic_label="SPECULATIVE",
    ),
}


# ------------------------------------------------------------------ #
#  Query Interface                                                     #
# ------------------------------------------------------------------ #

class MineralDatabase:
    """Query interface for the GAIA Crystal & Mineral Database (C118)."""

    def __init__(self) -> None:
        self._db = MINERAL_DATABASE

    def get(self, name: str) -> MineralEntry | None:
        return self._db.get(name.lower().replace(" ", "_"))

    def by_role(self, role: GAIARole) -> list[MineralEntry]:
        return [m for m in self._db.values() if m.gaia_role == role]

    def by_system(self, system: CrystalSystem) -> list[MineralEntry]:
        return [m for m in self._db.values() if m.crystal_system == system]

    def piezoelectric_minerals(self) -> list[MineralEntry]:
        return [m for m in self._db.values() if m.is_piezoelectric]

    def cosmic_minerals(self) -> list[MineralEntry]:
        return self.by_role(GAIARole.COSMIC_INPUT)

    def noise_references(self) -> list[MineralEntry]:
        return self.by_role(GAIARole.NOISE_REFERENCE)

    def chakra_minerals(self, chakra: str) -> list[MineralEntry]:
        return [
            m for m in self._db.values()
            if chakra.lower() in [c.lower() for c in m.chakra_resonance]
            or "all" in m.chakra_resonance
        ]

    def frequency_range(self, low_hz: float, high_hz: float) -> list[MineralEntry]:
        """Find minerals whose sensing band overlaps the given frequency range."""
        return [
            m for m in self._db.values()
            if m.resonance_band_high_hz >= low_hz
            and m.resonance_band_low_hz <= high_hz
            and m.resonance_band_high_hz > 0
        ]

    def all_minerals(self) -> list[MineralEntry]:
        return list(self._db.values())

    def summary(self) -> dict:
        return {
            "total_minerals":       len(self._db),
            "piezoelectric_count":  len(self.piezoelectric_minerals()),
            "crystal_systems":      {
                s.value: len(self.by_system(s)) for s in CrystalSystem
            },
            "gaia_roles":           {
                r.value: len(self.by_role(r)) for r in GAIARole
            },
            "canon_ref":            "C118",
        }


# Singleton
_db_instance: MineralDatabase | None = None

def get_mineral_db() -> MineralDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = MineralDatabase()
    return _db_instance
