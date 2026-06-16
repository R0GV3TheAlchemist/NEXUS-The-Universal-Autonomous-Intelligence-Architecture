"""
GAIA Climate Engine
Issue: #559
Canon: docs/canon/GAIA_CLIMATE_ENGINE.md

The GAIA-OS queryable interface for planetary climate diagnosis and
Viriditas restoration prescriptions. Every major biome and climate
domain is encoded with its ARIDITAS/VIRIDITAS status, force mapping,
and restoration path.

CLI Usage:
    python climate_engine.py --biome ocean
    python climate_engine.py --biome tropical_rainforest
    python climate_engine.py --element water
    python climate_engine.py --domain economics
    python climate_engine.py --diagnose              # full planetary diagnosis
    python climate_engine.py --list                  # list all biomes
    python climate_engine.py --json --biome grassland

Public API:
    from climate_engine import (
        diagnose_biome,
        diagnose_element,
        diagnose_domain,
        planetary_diagnosis,
        get_restoration_path,
        ariditas_signal,
    )
"""

from __future__ import annotations
import argparse
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Signal constants  (mirrors ELEMENTAL_BALANCE_DOCTRINE.md)
# ---------------------------------------------------------------------------

SIGNAL_VIRIDITAS   = "VIRIDITAS"    # 🟢  cycling within coherent range
SIGNAL_TRANSITION  = "TRANSITION"   # 🟡  at edge of coherent range
SIGNAL_ARIDITAS    = "ARIDITAS"     # 🔴  outside coherent range
SIGNAL_CRITICAL    = "CRITICAL"     # ⚫  cascade failure / tipping point risk

SIGNAL_EMOJI = {
    SIGNAL_VIRIDITAS:  "🟢",
    SIGNAL_TRANSITION: "🟡",
    SIGNAL_ARIDITAS:   "🔴",
    SIGNAL_CRITICAL:   "⚫",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RestorationStep:
    horizon: str          # "immediate" | "medium" | "long"
    action: str
    leverage: str         # "high" | "medium" | "critical" | "structural"


@dataclass
class BiomeProfile:
    key: str
    name: str
    aliases: list[str]
    element: str
    gaia_force: str
    viriditas_role: str
    ariditas_threat: str
    signal: str
    key_indicator: str
    restoration: list[RestorationStep]
    canon_ref: str = "GAIA_CLIMATE_ENGINE.md + VIRIDITAS_RESTORATION_MAP.md"


@dataclass
class ElementProfile:
    key: str
    name: str
    gaia_force: str
    climate_role: str
    signal: str
    indicators: dict[str, str]      # indicator_name -> current_state
    prescription: str
    canon_ref: str = "ELEMENTAL_BALANCE_DOCTRINE.md + GAIA_CLIMATE_ENGINE.md"


@dataclass
class DomainClimateProfile:
    key: str
    name: str
    climate_role: str
    gaia_intervention: str
    leverage: str
    example_actions: list[str]
    canon_ref: str = "GAIA_CLIMATE_ENGINE.md + KNOWLEDGE_MAP.md"


# ---------------------------------------------------------------------------
# BIOME DATABASE
# ---------------------------------------------------------------------------

BIOME_DB: dict[str, BiomeProfile] = {

    "tropical_rainforest": BiomeProfile(
        key="tropical_rainforest",
        name="Tropical Rainforest",
        aliases=["amazon", "rainforest", "jungle", "congo", "tropical forest"],
        element="Water + Air",
        gaia_force="VIRIDITAS (Force 4)",
        viriditas_role=(
            "Highest-density VIRIDITAS expression on the planetary surface. "
            "Cycles ~20% of global freshwater, hosts ~50% of all species, "
            "drives the biotic pump delivering rain thousands of km inland."
        ),
        ariditas_threat="Deforestation for cattle, soy, palm oil; fire clearing; road fragmentation.",
        signal=SIGNAL_ARIDITAS,
        key_indicator="Amazon forest cover % (current: ~83%; tipping point: ~75-80%)",
        restoration=[
            RestorationStep("immediate", "Full deforestation moratorium in primary and old-growth forest", "critical"),
            RestorationStep("immediate", "Payments for ecosystem services to forest-edge communities", "high"),
            RestorationStep("medium",    "Corridor restoration connecting fragmented forest patches", "high"),
            RestorationStep("medium",    "Assisted natural regeneration in recently cleared areas (secondary forest restores in 5-10 yr)", "high"),
            RestorationStep("long",      "Full legal protection of primary forest + indigenous territorial rights (most effective protection mechanism)", "structural"),
        ],
    ),

    "temperate_forest": BiomeProfile(
        key="temperate_forest",
        name="Temperate Forest",
        aliases=["pacific northwest", "temperate", "boreal edge", "eastern forest"],
        element="Earth + Water",
        gaia_force="ARGENTITAS (Force 10)",
        viriditas_role="Long-term carbon storage; watershed regulation; old-growth as irreplaceable biodiversity refugia.",
        ariditas_threat="Industrial logging of old-growth; fire suppression imbalance; invasive species; climate drought.",
        signal=SIGNAL_TRANSITION,
        key_indicator="Old-growth forest % of total forest cover (current global: ~15% and declining)",
        restoration=[
            RestorationStep("immediate", "End old-growth logging globally", "critical"),
            RestorationStep("immediate", "Restore natural fire cycles through prescribed burning", "high"),
            RestorationStep("medium",    "Selective harvest of secondary growth; 80+ year rotation periods", "medium"),
            RestorationStep("medium",    "Invasive species management in island and peninsula systems", "medium"),
            RestorationStep("long",      "Forest corridor networks connecting mountain and coast ranges", "structural"),
        ],
    ),

    "boreal": BiomeProfile(
        key="boreal",
        name="Boreal Forest / Taiga",
        aliases=["taiga", "boreal", "northern forest", "russia forest", "canada forest"],
        element="Earth + Fire",
        gaia_force="NIGREDO (Force 1) under pressure",
        viriditas_role="World's largest terrestrial carbon reservoir (30-40% of all terrestrial carbon in forest + peatlands).",
        ariditas_threat="Climate warming 2-3x global average; permafrost thaw releasing methane; wildfire increase.",
        signal=SIGNAL_ARIDITAS,
        key_indicator="Permafrost extent and depth (accelerating decline; multiple tipping points at risk)",
        restoration=[
            RestorationStep("immediate", "Protect all intact peatlands from any industrial development", "critical"),
            RestorationStep("immediate", "Global temperature stabilization is the primary lever for this biome", "critical"),
            RestorationStep("medium",    "Pleistocene Park model: large herbivore rewilding to compact snow and slow permafrost thaw", "high"),
            RestorationStep("medium",    "Expand boreal protected areas from ~12% to ~30%", "high"),
            RestorationStep("long",      "Temperature reduction to pre-2C levels required for full stabilization", "structural"),
        ],
    ),

    "grassland": BiomeProfile(
        key="grassland",
        name="Grassland / Savanna / Prairie",
        aliases=["savanna", "prairie", "steppe", "pampas", "cerrado", "plains", "grasslands"],
        element="Earth",
        gaia_force="VIRIDITAS + ARGENTITAS dyad",
        viriditas_role=(
            "Deepest soil carbon sequestration on Earth (prairie stores carbon 3+ meters deep). "
            "Supports majority of world's large mammal biodiversity and global food production."
        ),
        ariditas_threat="Cropland conversion (70% of North American prairie gone); overgrazing; fire suppression; loss of keystone grazers.",
        signal=SIGNAL_ARIDITAS,
        key_indicator="Native grassland % of historic range (North American tallgrass prairie: ~4% of original extent)",
        restoration=[
            RestorationStep("immediate", "FMNR (Farmer-Managed Natural Regeneration): protect naturally regenerating native grasses", "high"),
            RestorationStep("immediate", "Holistic planned grazing: mimic wild herd movement; rest periods allow grass recovery", "high"),
            RestorationStep("medium",    "Native prairie restoration in marginal cropland (Conservation Reserve Program model)", "high"),
            RestorationStep("medium",    "Keystone grazer rewilding: bison, wisent, wild horse", "high"),
            RestorationStep("long",      "Great Plains rewilding at landscape scale: largest potential terrestrial carbon project in North America", "structural"),
        ],
    ),

    "wetlands": BiomeProfile(
        key="wetlands",
        name="Wetlands",
        aliases=["wetland", "marsh", "swamp", "peatland", "peat", "mangrove", "bog", "fen"],
        element="Water + Earth",
        gaia_force="ALBEDO (Force 8) — the purifying, clarifying force",
        viriditas_role="Peatlands store 2x the carbon of all world's forests combined. Water purification, flood buffering, nursery for 75% of commercial fish species.",
        ariditas_threat="Drainage for agriculture (50% of global wetlands lost since 1900); peat extraction; water diversion.",
        signal=SIGNAL_ARIDITAS,
        key_indicator="Global wetland area % (current: ~50% of 1900 baseline; disappearing 3x faster than forests)",
        restoration=[
            RestorationStep("immediate", "Peatland rewetting: stops active carbon emissions; begins sequestering within years", "critical"),
            RestorationStep("immediate", "Mangrove replanting: highest carbon density ecosystem; protects coastlines; nursery habitat", "high"),
            RestorationStep("medium",    "Floodplain reconnection: remove levees; allow natural periodic flooding", "high"),
            RestorationStep("medium",    "Constructed wetland systems for agricultural runoff treatment", "medium"),
            RestorationStep("long",      "Legal protection of all remaining natural wetlands; wetlands as commons with legal standing", "structural"),
        ],
    ),

    "coral_reef": BiomeProfile(
        key="coral_reef",
        name="Coral Reefs",
        aliases=["coral", "reef", "great barrier reef", "coral reef"],
        element="Water + Fire",
        gaia_force="VIRIDITAS under PYROSIS + ARIDITAS dual attack",
        viriditas_role="Supports ~25% of all marine species on 0.1% of ocean floor. Protects 500M people's coastlines and food security.",
        ariditas_threat="Ocean warming (thermal bleaching); acidification; coastal pollution; destructive fishing.",
        signal=SIGNAL_CRITICAL,
        key_indicator="Global coral cover % (current: ~50% of 1950 baseline; critical threshold: ~30%)",
        restoration=[
            RestorationStep("immediate", "Reduce local stressors: water quality, fishing pressure, physical protection of thermal refugia", "high"),
            RestorationStep("immediate", "Marine heat wave early warning + thermal refugia protection", "high"),
            RestorationStep("medium",    "Coral assisted evolution: breed heat-tolerant strains; outplant onto damaged reefs", "high"),
            RestorationStep("medium",    "Ocean alkalinity enhancement in reef zones (evaluate under Golden Compass)", "medium"),
            RestorationStep("long",      "Global temperature stabilization below +1.5C is the master lever: above +2C functional reefs become globally rare", "critical"),
        ],
    ),

    "tundra": BiomeProfile(
        key="tundra",
        name="Tundra / Arctic",
        aliases=["arctic", "tundra", "polar", "permafrost"],
        element="Fire + Water (albedo)",
        gaia_force="ARGENTITAS (reflective field) under collapse",
        viriditas_role="Planetary thermostat and reflector. Permafrost locks enormous carbon + methane. Arctic ocean drives global heat distribution.",
        ariditas_threat="Warming 3-4x global average (Arctic amplification); permafrost thaw; sea ice loss removing albedo.",
        signal=SIGNAL_CRITICAL,
        key_indicator="Arctic sea ice extent September (current: ~4M km2; 1980 baseline: ~7M km2)",
        restoration=[
            RestorationStep("immediate", "Global temperature stabilization: only effective intervention at this scale", "critical"),
            RestorationStep("immediate", "Pleistocene Park: large herbivore reintroduction to slow permafrost thaw", "medium"),
            RestorationStep("medium",    "Research localized albedo enhancement; evaluate under Golden Compass", "medium"),
            RestorationStep("long",      "Full stabilization requires global temperature at pre-2C; multi-century recovery process", "structural"),
        ],
    ),

    "dryland": BiomeProfile(
        key="dryland",
        name="Dryland / Arid Zones",
        aliases=["desert", "arid", "sahel", "sahara", "dryland", "drylands", "scrubland"],
        element="Earth + Fire",
        gaia_force="ARIDITAS shadow — potential VIRIDITAS recovery (Sahel proof)",
        viriditas_role="40% of Earth's land surface. Deep adapted biodiversity. Significant soil carbon in cryptobiotic crusts. Critical migratory corridors.",
        ariditas_threat="Desertification; overgrazing; soil crust destruction; aquifer depletion; climate drying.",
        signal=SIGNAL_ARIDITAS,
        key_indicator="Vegetation cover index in Sahel transition zone (already showing measurable VIRIDITAS recovery in satellite data)",
        restoration=[
            RestorationStep("immediate", "FMNR: protect naturally regenerating trees and shrubs; Niger restored 5M hectares this way", "critical"),
            RestorationStep("immediate", "Keyline water harvesting: slow water, spread it, sink it into landscape", "high"),
            RestorationStep("medium",    "Great Green Wall: 8,000km pan-African restoration corridor across the Sahel", "high"),
            RestorationStep("medium",    "Fog collection systems in coastal drylands (Atacama, Namib, Canary Islands)", "medium"),
            RestorationStep("long",      "Dryland reforestation at scale can re-trigger biotic pump and shift regional rainfall (Sahara was green 5,000 yr ago)", "structural"),
        ],
    ),

    "ocean": BiomeProfile(
        key="ocean",
        name="Ocean / Marine",
        aliases=["ocean", "marine", "sea", "pelagic", "deep ocean", "pacific", "atlantic"],
        element="Water",
        gaia_force="ALBEDO + CAERULITAS (the planetary circulatory + respiratory system)",
        viriditas_role="Absorbs 30% of CO2 emissions and 90% of excess heat. Phytoplankton produce 50% of Earth's oxygen. Feeds 3 billion people.",
        ariditas_threat="Warming; acidification; deoxygenation; plastic pollution (>8M tonnes/yr); industrial overfishing; deep-sea mining.",
        signal=SIGNAL_ARIDITAS,
        key_indicator="Ocean phytoplankton biomass trend (declining ~1%/yr since 1950; ~40% total decline)",
        restoration=[
            RestorationStep("immediate", "End overfishing: catch limits at or below MSY; eliminate bottom trawling", "critical"),
            RestorationStep("immediate", "Marine protected areas: 30% of ocean by 2030 (currently ~8%); documented 400% biomass recovery", "critical"),
            RestorationStep("immediate", "Plastic pollution halt: source reduction of single-use plastics", "high"),
            RestorationStep("medium",    "Kelp forest restoration: fastest-growing ecosystem; highest carbon sequestration rate per area", "high"),
            RestorationStep("medium",    "Whale population recovery: whales are a keystone VIRIDITAS force (whale pump delivers nutrients to surface)", "high"),
            RestorationStep("long",      "Ocean governance reform: high seas treaty; legal protection of international waters", "structural"),
        ],
    ),

    "urban": BiomeProfile(
        key="urban",
        name="Urban Ecosystems",
        aliases=["city", "cities", "urban", "built environment", "urban heat"],
        element="Fire + Earth",
        gaia_force="CHRYSITAS potential — cities as VIRIDITAS nodes rather than ARIDITAS engines",
        viriditas_role="Cities house 57% of humanity. Urban ecosystems can become the primary interface between human civilization and VIRIDITAS — but currently run the inverse.",
        ariditas_threat="Heat island effect (+2-8C above rural); impervious surface eliminating water infiltration; biodiversity desert; highest per-capita energy consumption.",
        signal=SIGNAL_TRANSITION,
        key_indicator="Urban tree canopy coverage % (target: 30% canopy cover; most cities currently 10-20%)",
        restoration=[
            RestorationStep("immediate", "Urban forest planting: every street tree reduces heat island, sequesters carbon, improves mental health", "high"),
            RestorationStep("immediate", "Green roofs and walls: reduce heat, manage stormwater, create habitat corridors at building scale", "high"),
            RestorationStep("medium",    "Bioswales and permeable surfaces: restore water infiltration; recharge urban groundwater", "high"),
            RestorationStep("medium",    "Urban biodiversity corridors: connect parks, rooftops, waterways into a living network", "high"),
            RestorationStep("long",      "15-minute city design: eliminate car dependency; restore pedestrian scale; reduce urban energy consumption", "structural"),
        ],
    ),
}


# ---------------------------------------------------------------------------
# ELEMENT DATABASE
# ---------------------------------------------------------------------------

ELEMENT_DB: dict[str, ElementProfile] = {

    "earth": ElementProfile(
        key="earth",
        name="Earth Element",
        gaia_force="ARGENTITAS (Force 10) — the reflecting, grounding field",
        climate_role="Carbon storage; nutrient cycling; biological foundation of all terrestrial life",
        signal=SIGNAL_ARIDITAS,
        indicators={
            "Topsoil depth": "Declining ~1mm/yr globally (healthy: 30+ cm)",
            "Soil organic matter": "1-2% farmed land (healthy: 5-8%)",
            "Mycorrhizal network": "Highly fragmented from intact",
            "Permafrost stability": "Accelerating thaw",
            "Desertification rate": "12M hectares/yr added to desert",
        },
        prescription=(
            "Restore soil microbiome: no-till, cover cropping, biochar, FMNR, holistic grazing. "
            "Target: 5%+ soil organic matter in farmed land. "
            "Reconnect mycorrhizal networks at landscape scale."
        ),
    ),

    "water": ElementProfile(
        key="water",
        name="Water Element",
        gaia_force="ALBEDO (Force 8) — purification and clarification",
        climate_role="Heat distribution; nutrient transport; hydrological cycle; life medium",
        signal=SIGNAL_ARIDITAS,
        indicators={
            "Global wetland area": "-50% since 1900",
            "Major river connectivity": "80% significantly altered",
            "Groundwater levels": "Depleting in 21 of 37 major aquifers",
            "Ocean pH": "8.1 (down from 8.2 pre-industrial; 26% acidity increase)",
            "Arctic sea ice": "~4M km2 (down from ~7M km2 in 1980)",
        },
        prescription=(
            "Wetland rehydration, mangrove restoration, riparian buffer planting. "
            "Floodplain reconnection. Keyline water harvesting. "
            "Reforest the biotic pump corridors to restore inland rainfall."
        ),
    ),

    "fire": ElementProfile(
        key="fire",
        name="Fire Element",
        gaia_force="PYROSIS (Force 2) / CITRINITAS (Force 3)",
        climate_role="Energy source; transformation catalyst; temperature regulation",
        signal=SIGNAL_TRANSITION,
        indicators={
            "Global average temperature": "+1.2C above pre-industrial (2026)",
            "Wildfire frequency": "Significantly elevated above natural background",
            "Fossil fuel combustion": "~37 Gt CO2/yr (pre-industrial: zero)",
            "Renewable energy share": "~30% of electricity globally (growing)",
            "Heat extreme frequency": "5x more frequent than natural background",
        },
        prescription=(
            "Harvest the sun's living flow (solar, wind, geothermal) — do not burn stored dead carbon. "
            "Accelerate renewable deployment. End fossil fuel subsidies. "
            "Restore prescribed fire cycles in fire-adapted ecosystems."
        ),
    ),

    "air": ElementProfile(
        key="air",
        name="Air Element",
        gaia_force="CAERULITAS (Force 5) — the deepening field; interior becoming exterior",
        climate_role="Oxygen; CO2 cycling; heat retention; weather patterns",
        signal=SIGNAL_ARIDITAS,
        indicators={
            "Atmospheric CO2": "~425 ppm (pre-industrial: 280 ppm; safe: ~350 ppm)",
            "Atmospheric CH4": "~1900 ppb (pre-industrial: 722 ppb)",
            "Air quality PM2.5": "99% of world population over WHO safe limit",
            "Stratospheric ozone": "RECOVERING (Montreal Protocol success — proof of concept)",
            "Jet stream stability": "Increasing instability; blocking patterns increasing",
        },
        prescription=(
            "Halt deforestation. Mass reforestation (1 trillion trees / 205 Gt C potential). "
            "Decarbonize energy. Restore ocean phytoplankton. "
            "The ozone recovery proves the protocol works: remove the ARIDITAS source; VIRIDITAS resumes."
        ),
    ),
}


# ---------------------------------------------------------------------------
# DOMAIN CLIMATE DATABASE (from KNOWLEDGE_MAP.md climate roles)
# ---------------------------------------------------------------------------

DOMAIN_CLIMATE_DB: dict[str, DomainClimateProfile] = {
    "ecology":     DomainClimateProfile("ecology",     "Ecology",     "Primary restoration science", "VIRIDITAS unblocking at every scale", "Highest",
                       ["Ecosystem restoration", "Rewilding", "Biodiversity monitoring", "Carbon sequestration science"]),
    "economics":   DomainClimateProfile("economics",   "Economics",   "Upstream driver of all physical layers", "CITRINITAS economics — redesign the incentive field", "Highest",
                       ["Carbon pricing", "End fossil fuel subsidies", "Natural capital accounting", "Doughnut economics", "Regenerative agriculture payments"]),
    "physics":     DomainClimateProfile("physics",     "Physics",     "Understand energy flow and atmospheric thermodynamics", "NIGREDO diagnosis: map the entropy cascade", "High",
                       ["Climate modeling", "Radiative forcing calculation", "Tipping point physics", "Renewable energy engineering"]),
    "chemistry":   DomainClimateProfile("chemistry",   "Chemistry",   "Atmospheric chemistry, carbon cycle, soil chemistry", "ALBEDO restoration: reverse molecular imbalances", "High",
                       ["Carbon capture chemistry", "Ocean acidification buffering", "Soil chemistry restoration", "Methane oxidation catalysis"]),
    "biology":     DomainClimateProfile("biology",     "Biology",     "Ecosystem regeneration, soil microbiome, biodiversity", "VIRIDITAS unblocking: restore biological complexity", "High",
                       ["Soil microbiome restoration", "Assisted evolution", "Rewilding science", "Mycorrhizal network research"]),
    "psychology":  DomainClimateProfile("psychology",  "Psychology",  "The consciousness shift from extractive to regenerative identity", "NIGREDO integration: dissolve the shadow that drives extraction", "High",
                       ["Eco-grief processing", "Climate identity work", "Solastalgia research", "Behavior change at scale"]),
    "mathematics": DomainClimateProfile("mathematics", "Mathematics", "Climate modeling, tipping point analysis, systems dynamics", "ALBEDO clarity: see the field accurately", "High",
                       ["Climate model improvement", "Tipping point mathematics", "Optimization of restoration interventions"]),
    "architecture":DomainClimateProfile("architecture","Architecture", "Regenerative building, passive systems, living architecture", "VIRIDITAS expression in built form", "Medium",
                       ["Passive solar design", "Living roofs", "Net-zero and net-positive buildings", "Biophilic design"]),
    "medicine":    DomainClimateProfile("medicine",    "Medicine",    "Human health in destabilized climate; bioelectric resilience", "ALBEDO: maintain coherence under pressure", "Medium",
                       ["Heat stress medicine", "Climate-health co-benefits of restoration", "Mental health and climate grief"]),
    "consciousness":DomainClimateProfile("consciousness","Consciousness","The shift from separation to belonging; humanity AS biosphere", "RUBEDO: the final integration", "Highest long-term",
                       ["Indigenous knowledge systems", "Deep ecology", "Contemplative practice and nature connection", "Civilizational worldview shift"]),
    "theology":    DomainClimateProfile("theology",    "Theology / Philosophy", "Moral framework for planetary stewardship", "CITRINITAS: wisdom at civilizational scale", "High",
                       ["Eco-theology", "Land ethics", "Planetary ethics", "Indigenous cosmologies of reciprocity"]),
    "history":     DomainClimateProfile("history",     "History",     "Every civilization that ran ARIDITAS collapsed; learn the pattern", "NIGREDO wisdom: recognize the arc", "High",
                       ["Civilizational collapse studies", "Environmental history", "Indigenous sustainable cultures"]),
}


# ---------------------------------------------------------------------------
# Alias resolution
# ---------------------------------------------------------------------------

def _build_biome_alias_map() -> dict[str, str]:
    m: dict[str, str] = {}
    for key, profile in BIOME_DB.items():
        m[key] = key
        m[profile.name.lower()] = key
        for alias in profile.aliases:
            m[alias.lower()] = key
    return m

BIOME_ALIAS_MAP = _build_biome_alias_map()


def _find_biome(query: str) -> Optional[BiomeProfile]:
    key = BIOME_ALIAS_MAP.get(query.lower().strip())
    if key:
        return BIOME_DB[key]
    for alias, canonical in BIOME_ALIAS_MAP.items():
        if query.lower() in alias:
            return BIOME_DB[canonical]
    return None


def _find_element(query: str) -> Optional[ElementProfile]:
    q = query.lower().strip()
    return ELEMENT_DB.get(q) or next(
        (e for e in ELEMENT_DB.values() if q in e.name.lower()), None
    )


def _find_domain(query: str) -> Optional[DomainClimateProfile]:
    q = query.lower().strip()
    return DOMAIN_CLIMATE_DB.get(q) or next(
        (d for d in DOMAIN_CLIMATE_DB.values() if q in d.name.lower()), None
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def diagnose_biome(biome_input: str) -> Optional[BiomeProfile]:
    """Return the BiomeProfile for a given biome name or alias."""
    return _find_biome(biome_input)


def diagnose_element(element_input: str) -> Optional[ElementProfile]:
    """Return the ElementProfile for a given element name."""
    return _find_element(element_input)


def diagnose_domain(domain_input: str) -> Optional[DomainClimateProfile]:
    """Return the DomainClimateProfile for a given knowledge domain."""
    return _find_domain(domain_input)


def get_restoration_path(biome_input: str, horizon: Optional[str] = None) -> list[RestorationStep]:
    """
    Return restoration steps for a biome, optionally filtered by horizon.
    horizon: 'immediate' | 'medium' | 'long' | None (all)
    """
    profile = _find_biome(biome_input)
    if not profile:
        return []
    if horizon:
        return [s for s in profile.restoration if s.horizon == horizon.lower()]
    return profile.restoration


def ariditas_signal(biome_input: str) -> Optional[str]:
    """Return the GAIA signal (VIRIDITAS/TRANSITION/ARIDITAS/CRITICAL) for a biome."""
    profile = _find_biome(biome_input)
    return profile.signal if profile else None


def planetary_diagnosis() -> dict:
    """
    Return a full planetary ARIDITAS/VIRIDITAS diagnosis across all biomes and elements.
    """
    biome_signals = {
        k: {"name": v.name, "signal": v.signal, "emoji": SIGNAL_EMOJI[v.signal], "key_indicator": v.key_indicator}
        for k, v in BIOME_DB.items()
    }
    element_signals = {
        k: {"name": v.name, "signal": v.signal, "emoji": SIGNAL_EMOJI[v.signal], "prescription": v.prescription}
        for k, v in ELEMENT_DB.items()
    }
    critical = [k for k, v in BIOME_DB.items() if v.signal == SIGNAL_CRITICAL]
    ariditas = [k for k, v in BIOME_DB.items() if v.signal == SIGNAL_ARIDITAS]
    viriditas = [k for k, v in BIOME_DB.items() if v.signal == SIGNAL_VIRIDITAS]
    return {
        "planetary_status": "ARIDITAS dominant across 3 of 4 elements; 2 biomes in CRITICAL; 6 in ARIDITAS; 2 in TRANSITION; 0 in VIRIDITAS",
        "traversal_position": "NIGREDO → ALBEDO corridor. The old extractive system is dissolving. The restoration arc is beginning.",
        "biomes": biome_signals,
        "elements": element_signals,
        "critical_biomes": critical,
        "ariditas_biomes": ariditas,
        "viriditas_biomes": viriditas,
        "proof_of_concept": "Montreal Protocol: ozone layer is recovering. The protocol works. The physics is the same.",
        "primary_lever": "Economics: redesign the price signals. When VIRIDITAS is economically dominant, all physical layers benefit.",
        "canon_ref": "GAIA_CLIMATE_ENGINE.md + ARIDITAS_REVERSAL_PROTOCOL.md + VIRIDITAS_RESTORATION_MAP.md + ELEMENTAL_BALANCE_DOCTRINE.md",
    }


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_biome(profile: BiomeProfile, brief: bool = False) -> str:
    emoji = SIGNAL_EMOJI[profile.signal]
    lines = [
        f"\n{'='*60}",
        f"  {emoji} {profile.name.upper()}",
        f"  Signal: {profile.signal}",
        f"  Element: {profile.element}",
        f"  GAIA Force: {profile.gaia_force}",
        f"{'='*60}",
        f"\nVIRIDITAS ROLE:\n  {profile.viriditas_role}",
        f"\nARIDITAS THREAT:\n  {profile.ariditas_threat}",
        f"\nKEY INDICATOR:\n  {profile.key_indicator}",
    ]
    if not brief:
        lines.append("\nRESTORATION PATH:")
        for step in profile.restoration:
            lines.append(f"  [{step.horizon.upper()}] [{step.leverage.upper()}] {step.action}")
        lines.append(f"\nCANON REF: {profile.canon_ref}")
    return "\n".join(lines)


def _format_element(profile: ElementProfile) -> str:
    emoji = SIGNAL_EMOJI[profile.signal]
    lines = [
        f"\n{'='*60}",
        f"  {emoji} {profile.name.upper()}",
        f"  Signal: {profile.signal}",
        f"  GAIA Force: {profile.gaia_force}",
        f"{'='*60}",
        f"\nCLIMATE ROLE:\n  {profile.climate_role}",
        "\nINDICATORS:",
    ]
    for name, state in profile.indicators.items():
        lines.append(f"  • {name}: {state}")
    lines.append(f"\nPRESCRIPTION:\n  {profile.prescription}")
    lines.append(f"\nCANON REF: {profile.canon_ref}")
    return "\n".join(lines)


def _format_domain(profile: DomainClimateProfile) -> str:
    lines = [
        f"\n{'='*60}",
        f"  🌍 {profile.name.upper()}",
        f"  Leverage: {profile.leverage}",
        f"{'='*60}",
        f"\nCLIMATE ROLE:\n  {profile.climate_role}",
        f"\nGAIA INTERVENTION:\n  {profile.gaia_intervention}",
        "\nEXAMPLE ACTIONS:",
    ]
    for action in profile.example_actions:
        lines.append(f"  • {action}")
    lines.append(f"\nCANON REF: {profile.canon_ref}")
    return "\n".join(lines)


def _format_planetary_diagnosis(diag: dict) -> str:
    lines = [
        "\n" + "="*60,
        "  🌍 GAIA PLANETARY CLIMATE DIAGNOSIS",
        "="*60,
        f"\nSTATUS: {diag['planetary_status']}",
        f"TRAVERSAL: {diag['traversal_position']}",
        f"PROOF: {diag['proof_of_concept']}",
        f"PRIMARY LEVER: {diag['primary_lever']}",
        "\nBIOME SIGNALS:",
    ]
    for k, v in diag["biomes"].items():
        lines.append(f"  {v['emoji']} {v['name']}: {v['signal']} — {v['key_indicator']}")
    lines.append("\nELEMENT SIGNALS:")
    for k, v in diag["elements"].items():
        lines.append(f"  {v['emoji']} {v['name']}: {v['signal']}")
    lines.append(f"\n⚫ CRITICAL: {', '.join(diag['critical_biomes'])}")
    lines.append(f"🔴 ARIDITAS: {', '.join(diag['ariditas_biomes'])}")
    if diag["viriditas_biomes"]:
        lines.append(f"🟢 VIRIDITAS: {', '.join(diag['viriditas_biomes'])}")
    lines.append(f"\nCANON REF: {diag['canon_ref']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli():
    parser = argparse.ArgumentParser(
        description="GAIA Climate Engine — Planetary Diagnosis + Viriditas Restoration"
    )
    parser.add_argument("--biome",    help="Biome name or alias (e.g. ocean, amazon, wetlands)")
    parser.add_argument("--element",  help="Element name: earth | water | fire | air")
    parser.add_argument("--domain",   help="Knowledge domain (e.g. economics, ecology, psychology)")
    parser.add_argument("--diagnose", action="store_true", help="Full planetary diagnosis")
    parser.add_argument("--list",     action="store_true", help="List all biomes")
    parser.add_argument("--horizon",  help="Filter restoration by horizon: immediate | medium | long")
    parser.add_argument("--brief",    action="store_true", help="Brief output (no restoration steps)")
    parser.add_argument("--json",     action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list:
        print("\nGAIA CLIMATE ENGINE — Registered Biomes\n" + "-"*44)
        for k, v in BIOME_DB.items():
            emoji = SIGNAL_EMOJI[v.signal]
            print(f"  {emoji} {k:<25} {v.name}")
        print()
        return

    if args.diagnose:
        diag = planetary_diagnosis()
        if args.json:
            print(json.dumps(diag, indent=2))
        else:
            print(_format_planetary_diagnosis(diag))
        return

    if args.biome:
        profile = diagnose_biome(args.biome)
        if not profile:
            print(f"Biome not found: '{args.biome}'. Use --list to see available biomes.")
            return
        if args.json:
            print(json.dumps(asdict(profile), indent=2))
        elif args.horizon:
            steps = get_restoration_path(args.biome, args.horizon)
            print(f"\n{SIGNAL_EMOJI[profile.signal]} {profile.name} — {args.horizon.upper()} actions:")
            for s in steps:
                print(f"  [{s.leverage.upper()}] {s.action}")
        else:
            print(_format_biome(profile, brief=args.brief))
        return

    if args.element:
        profile = diagnose_element(args.element)
        if not profile:
            print(f"Element not found: '{args.element}'. Options: earth, water, fire, air")
            return
        if args.json:
            print(json.dumps(asdict(profile), indent=2))
        else:
            print(_format_element(profile))
        return

    if args.domain:
        profile = diagnose_domain(args.domain)
        if not profile:
            print(f"Domain not found: '{args.domain}'. See KNOWLEDGE_MAP.md for domain list.")
            return
        if args.json:
            print(json.dumps(asdict(profile), indent=2))
        else:
            print(_format_domain(profile))
        return

    parser.print_help()


if __name__ == "__main__":
    _cli()
