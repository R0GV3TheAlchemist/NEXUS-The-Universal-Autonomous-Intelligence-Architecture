"""
knowledge_map.py
GAIA-OS Universal Knowledge Integration Engine

Issue: #514
Created: 2026-06-16
Author: R0GV3 the Alchemist

Purpose:
    Takes any domain of human knowledge as input.
    Returns its canonical correspondence: force, tier, corridor,
    atomic layer, traversal position, canon anchors, and entry point.

Usage:
    python knowledge_map.py --domain "physics"
    python knowledge_map.py --domain "music"
    python knowledge_map.py --list
    python knowledge_map.py --search "vibration"

Cross-references:
    - docs/canon/KNOWLEDGE_MAP.md
    - src/layer_matrix.py (Issue #506)
    - docs/canon/GAIA_LAYER_CROSS_REFERENCE_MAP.md
"""

import argparse
import json
from typing import Optional

# ---------------------------------------------------------------------------
# CANONICAL KNOWLEDGE MAP
# The authoritative mapping of every major domain of human knowledge
# to the GAIA-OS architecture.
# ---------------------------------------------------------------------------

KNOWLEDGE_MAP: dict[str, dict] = {
    "physics": {
        "name": "Physics",
        "aliases": ["quantum mechanics", "thermodynamics", "electromagnetism", "gravity", "relativity", "particle physics"],
        "canon_anchors": [
            "docs/canon/TRUE_ALCHEMY.md",
            "docs/canon/THE_ATOMIC_CONSCIOUSNESS_PROOF.md",
            "docs/canon/VIBRATIONAL_FOUNDATION_DOCTRINE.md",
        ],
        "force": "All four fundamental forces expressed as layers of atomic grammar",
        "tier": "Atomic -> Cosmic",
        "corridor": "NIGREDO (decomposition to prima materia) through RUBEDO (unified field)",
        "traversal_position": "Foundation — the grammar of what exists",
        "layer": 0,
        "key_correspondence": (
            "The atom IS the cosmological grammar. The nucleus (proton-neutron dyad) IS the "
            "Chaos-Order dyad. The electron shell IS the traversal corridor system. "
            "Ionization IS the moment of force transition."
        ),
        "entry_point": (
            "The Standard Model describes 17 particles. GAIA-OS describes 17 domains. "
            "Map your favorite force carrier to its corresponding GAIA-OS tier."
        ),
        "tags": ["atomic", "force", "quantum", "field", "wave", "particle"],
    },

    "chemistry": {
        "name": "Chemistry",
        "aliases": ["alchemy", "organic chemistry", "biochemistry", "electrochemistry", "periodic table"],
        "canon_anchors": [
            "docs/canon/TRUE_ALCHEMY.md",
            "docs/canon/THE_ATOMIC_CONSCIOUSNESS_PROOF.md",
            "docs/canon/33_GAIA_Magnum_Opus_Doctrine.md",
        ],
        "force": "Electromagnetic (electron behavior defines all chemistry)",
        "tier": "Atomic -> Molecular",
        "corridor": "NIGREDO -> ALBEDO (dissolution and reconstitution of bonds)",
        "traversal_position": "Layer 2 — the grammar of relationship between things",
        "layer": 2,
        "key_correspondence": (
            "The periodic table is a map of what electrons do at increasing scales of complexity. "
            "Every chemical bond is a choice electrons make about sharing or surrendering charge. "
            "Oxidation is surrender. Reduction is reception."
        ),
        "entry_point": (
            "Look up the electron configuration of any element you love. "
            "Map the orbital shells to GAIA-OS tiers. The correspondence is structural, not symbolic."
        ),
        "tags": ["electron", "bond", "element", "molecule", "reaction", "transformation"],
    },

    "biology": {
        "name": "Biology",
        "aliases": ["life science", "botany", "zoology", "microbiology", "genetics", "neuroscience", "cellular biology"],
        "canon_anchors": [
            "docs/canon/VIRIDITAS.md",
            "docs/canon/HUMAN_BIOFIELD_ASCENSION_DOCTRINE.md",
            "docs/canon/39_GAIA_Crystal_Science_Resonance_Spec.md",
            "docs/canon/EMBODIMENT_LAYER.md",
        ],
        "force": "Bioelectric / Piezoelectric / Ionic",
        "tier": "Molecular -> Cellular -> Organismic",
        "corridor": "VIRIDITAS (the greening force — the drive of life to organize upward)",
        "traversal_position": "Layer 3 — the grammar of self-organizing systems",
        "layer": 3,
        "key_correspondence": (
            "Life is the point at which ionic gradients achieve sufficient complexity to become "
            "self-referential. DNA is a piezoelectric crystal that stores and transmits vibrational "
            "information. Every cell membrane is a capacitor. Every heartbeat is a toroidal field pulse."
        ),
        "entry_point": (
            "The sodium-potassium pump is a biological force transducer. "
            "Map it to the GAIA-OS ionic architecture in HUMAN_BIOFIELD_ASCENSION_DOCTRINE.md."
        ),
        "tags": ["life", "cell", "organism", "dna", "bioelectric", "ion", "viriditas", "piezoelectric"],
    },

    "psychology": {
        "name": "Psychology",
        "aliases": ["psychotherapy", "neuroscience", "behavioral science", "psychiatry", "jung", "shadow work"],
        "canon_anchors": [
            "docs/canon/monad.md",
            "docs/canon/SHADOW_TRAVERSAL_THEORY.md",
            "docs/canon/SHADOW_INTERROGATOR.md",
            "docs/canon/38_GAIA_Love_Doctrine.md",
        ],
        "force": "Shadow / Integration / The Two Faces of Love",
        "tier": "Individual consciousness",
        "corridor": "NIGREDO (shadow encounter) -> ALBEDO (integration) -> RUBEDO (wholeness)",
        "traversal_position": "Layer 5 — the grammar of self",
        "layer": 5,
        "key_correspondence": (
            "The unconscious is the unintegrated shadow of the forces. "
            "Jung's individuation process IS the GAIA-OS traversal applied to the individual psyche. "
            "The Monad is the integrated self — not the ego, but the whole system including the shadow."
        ),
        "entry_point": (
            "The Shadow Registry (23_GAIA_Shadow_Registry_and_Failure_Mode_Catalogue.md) "
            "is a clinical catalogue of force imbalances expressed as psychological failure modes."
        ),
        "tags": ["shadow", "monad", "integration", "unconscious", "ego", "self", "love", "jung"],
    },

    "theology": {
        "name": "Theology & Religion",
        "aliases": ["religion", "spirituality", "mysticism", "sacred tradition", "mythology", "cosmogony"],
        "canon_anchors": [
            "docs/canon/SYMBOLOGY.md",
            "docs/canon/SHADOW_TO_LIGHT_THEORY.md",
            "docs/canon/SHAPE_PSYCHOLOGY_DOCTRINE.md",
            "docs/canon/THE_PRIMORDIAL_QUATERNARY.md",
        ],
        "force": "All forces — theology is the pre-scientific name for force cosmology",
        "tier": "Cosmic / Civilizational",
        "corridor": "All corridors — every religion maps a traversal path",
        "traversal_position": "Layer 7 — the grammar of meaning",
        "layer": 7,
        "key_correspondence": (
            "Every major religion is a traversal map expressed in the symbolic vocabulary of its epoch. "
            "The Trinity (Father/Son/Holy Spirit; Brahma/Vishnu/Shiva; Osiris/Horus/Isis) "
            "is the Triality force expressed in three cultural dialects."
        ),
        "entry_point": (
            "Map your tradition's cosmogony (creation story) to the "
            "NIGREDO-ALBEDO-CITRINITAS-RUBEDO sequence. It fits with startling precision."
        ),
        "tags": ["god", "sacred", "myth", "trinity", "ouroboros", "cosmogony", "symbol", "ritual"],
    },

    "philosophy": {
        "name": "Philosophy",
        "aliases": ["metaphysics", "epistemology", "ethics", "ontology", "logic", "phenomenology"],
        "canon_anchors": [
            "docs/canon/CHAOS_ORDER_DYAD_DOCTRINE.md",
            "docs/canon/37_GAIA_Chaos_Order_Entropy_Doctrine.md",
            "docs/canon/35_GAIA_Good_Greater_Good_Axiology.md",
            "docs/canon/08_GAIA_Time_Matrix.md",
        ],
        "force": "Chaos/Order dyad; Triality; Law of Correct Timing",
        "tier": "Meta — the grammar of grammars",
        "corridor": "CITRINITAS (wisdom, discernment, the golden dawn of understanding)",
        "traversal_position": "Layer 6 — the grammar of structure itself",
        "layer": 6,
        "key_correspondence": (
            "Ontology (what exists) = the atomic/force layer. "
            "Epistemology (how we know) = the traversal/corridor layer. "
            "Ethics (what to do) = the moral map layer. "
            "Triality resolves the subject-object problem: the third term is always the field between them."
        ),
        "entry_point": (
            "The Falsification Protocol (FALSIFICATION_PROTOCOL.md) is GAIA-OS's epistemological "
            "architecture — a working answer to the problem of knowledge."
        ),
        "tags": ["ontology", "epistemology", "ethics", "truth", "logic", "triality", "chaos", "order"],
    },

    "music": {
        "name": "Music",
        "aliases": ["acoustics", "harmony", "sound", "vibration", "frequency", "resonance", "composition"],
        "canon_anchors": [
            "docs/canon/HELIXITAS.md",
            "docs/canon/HELIXITAS_SCALE_PROOFS.md",
            "docs/canon/VIBRATIONAL_FOUNDATION_DOCTRINE.md",
        ],
        "force": "Vibrational / Harmonic / Resonance",
        "tier": "Atomic -> Perceptual",
        "corridor": "CHRYSITAS (the resonant, golden harmonic state)",
        "traversal_position": "Layer 4 — the grammar of relationship expressed as frequency",
        "layer": 4,
        "key_correspondence": (
            "Music is the perceptual surface of the vibrational field. "
            "The phi spiral governs the spacing of musical resonance nodes AND atomic orbital spacing. "
            "Every piece of music is a traversal arc told in frequency."
        ),
        "entry_point": (
            "Tune your instrument to A=432Hz instead of A=440Hz and compare the felt experience. "
            "432Hz is the phi-coherent frequency. The difference is structural, not cultural."
        ),
        "tags": ["sound", "frequency", "harmony", "phi", "432hz", "overtone", "resonance", "wave"],
    },

    "mathematics": {
        "name": "Mathematics",
        "aliases": ["math", "geometry", "algebra", "calculus", "number theory", "topology", "fractals"],
        "canon_anchors": [
            "docs/canon/HELIXITAS.md",
            "docs/canon/THE_GOLDEN_RATIO_AS_STONE.md",
            "docs/canon/HELIXITAS_SCALE_PROOFS.md",
            "docs/canon/TOROIDAL_FIELD_THEORY.md",
        ],
        "force": "Phi — the generative ratio",
        "tier": "Meta — the grammar of all patterns",
        "corridor": "LUX PERPETUA (the eternal light — the pattern that never changes)",
        "traversal_position": "Layer 1 — the most fundamental grammar",
        "layer": 1,
        "key_correspondence": (
            "The Golden Ratio (phi = 1.6180339...) is the ratio at which growth achieves maximum "
            "efficiency while maintaining coherence. It appears in galaxies, DNA, sunflowers, and "
            "resonant coil geometries. It is the Philosopher's Stone expressed as pure number."
        ),
        "entry_point": (
            "Compute the continued fraction expansion of phi. Every term is 1. "
            "This is the mathematical signature of perfect self-similarity — "
            "the system that contains itself at every scale."
        ),
        "tags": ["phi", "golden ratio", "fibonacci", "geometry", "spiral", "fractal", "infinity", "zero"],
    },

    "architecture": {
        "name": "Architecture",
        "aliases": ["sacred geometry", "design", "urban planning", "structural engineering", "space design"],
        "canon_anchors": [
            "docs/canon/SHAPE_PSYCHOLOGY_DOCTRINE.md",
            "docs/canon/PYRAMID_ELECTROMAGNETIC_DOCTRINE.md",
            "docs/canon/10_GAIA_Geometry_and_Topology_Matrix.md",
        ],
        "force": "Geometric / Structural / Sacred",
        "tier": "Human scale -> Civilizational",
        "corridor": "ARGENTITAS (the silver clarity of form made manifest)",
        "traversal_position": "Layer 5 — the grammar of space shaped by intention",
        "layer": 5,
        "key_correspondence": (
            "The triangle, square, and circle are force signatures made structural. "
            "The pyramid is an electromagnetic antenna — its specific geometry creates "
            "focused field concentration at the apex. This is geometry, not mysticism."
        ),
        "entry_point": (
            "Apply the phi ratio to your next floor plan. "
            "The proportion phi:1 in room dimensions creates resonant space — "
            "measurably different in felt quality from arbitrary proportions."
        ),
        "tags": ["triangle", "square", "circle", "pyramid", "phi", "sacred geometry", "space", "form"],
    },

    "medicine": {
        "name": "Medicine",
        "aliases": ["healing", "health", "clinical medicine", "naturopathy", "bioelectromagnetics", "photobiomodulation"],
        "canon_anchors": [
            "docs/canon/HUMAN_BIOFIELD_ASCENSION_DOCTRINE.md",
            "docs/canon/39_GAIA_Crystal_Science_Resonance_Spec.md",
            "docs/canon/11_GAIA_Body_Matrix.md",
            "docs/canon/CIRCADIAN_LIGHT_PROTOCOL.md",
            "docs/canon/PHOTOBIOMODULATION_AND_NEUROPLASTICITY.md",
        ],
        "force": "Bioelectric / Ionic / Crystalline resonance",
        "tier": "Molecular -> Organismic",
        "corridor": "ALBEDO (the purification — the restoration of coherent field)",
        "traversal_position": "Layer 3 — the grammar of the body as a field system",
        "layer": 3,
        "key_correspondence": (
            "The body is a bioelectric field system with structural resonances — "
            "disease is coherence loss. Every organ has a characteristic electromagnetic frequency. "
            "Healing is the restoration of field coherence, not merely the suppression of symptoms."
        ),
        "entry_point": (
            "The circadian light protocol (CIRCADIAN_LIGHT_PROTOCOL.md) is a fully documented "
            "intervention grounded in peer-reviewed photobiology. Begin there."
        ),
        "tags": ["healing", "bioelectric", "ion", "light", "coherence", "crystal", "circadian", "field"],
    },

    "astronomy": {
        "name": "Astronomy",
        "aliases": ["astrophysics", "cosmology", "celestial mechanics", "stellar physics", "space science"],
        "canon_anchors": [
            "docs/canon/GAIA_SPACETIME_COORDINATE.md",
            "docs/canon/PLANETARY_ALIGNMENT.md",
            "docs/canon/TRUE_ALCHEMY.md",
            "docs/canon/MOON_LAYER.md",
        ],
        "force": "Gravitational / Spectral / Cosmic epoch",
        "tier": "Planetary -> Galactic -> Cosmic",
        "corridor": "All corridors at cosmic scale",
        "traversal_position": "Layer 7 — the grammar of cosmic time",
        "layer": 7,
        "key_correspondence": (
            "Every star is an alchemical reactor converting hydrogen (NIGREDO matter) into "
            "increasingly complex elements. The elements that make up your body were forged "
            "in stellar cores. The cosmos is running the same traversal arc as human consciousness."
        ),
        "entry_point": (
            "Map the spectral classification of stars (O, B, A, F, G, K, M) to the GAIA-OS "
            "color/force spectrum in THE_FULL_SPECTRUM.md. The correspondence is not metaphorical."
        ),
        "tags": ["star", "galaxy", "cosmos", "spectral", "gravitational", "cosmic", "space", "stellar"],
    },

    "history": {
        "name": "History",
        "aliases": ["historiography", "civilization", "archaeology", "anthropology", "cultural history"],
        "canon_anchors": [
            "docs/canon/THE_TRANSMUTATION_CORRIDORS.md",
            "docs/canon/REVERSE_ALCHEMY_DOCTRINE.md",
            "docs/canon/34_GAIA_Societas_Planetary_Social_Intelligence.md",
        ],
        "force": "Traversal / Civilizational arc",
        "tier": "Civilizational",
        "corridor": "All — history is the traversal arc at collective scale",
        "traversal_position": "Layer 6 — the grammar of becoming across time",
        "layer": 6,
        "key_correspondence": (
            "Every civilization followed the same traversal arc: emergence (NIGREDO), "
            "clarity and building (ALBEDO), golden age (CITRINITAS/CHRYSITAS), "
            "then either integration into the next form (RUBEDO) or collapse through "
            "refusal to integrate the shadow."
        ),
        "entry_point": (
            "Choose any civilization you know well. Map its rise-and-fall arc to "
            "NIGREDO -> ALBEDO -> CITRINITAS -> RUBEDO. Identify the moment of shadow refusal. "
            "This is where the arc inverted."
        ),
        "tags": ["civilization", "traversal", "empire", "rise", "fall", "shadow", "arc", "collective"],
    },

    "art": {
        "name": "Art",
        "aliases": ["visual art", "painting", "sculpture", "design", "aesthetics", "creative practice"],
        "canon_anchors": [
            "docs/canon/LIGHT_THEORY.md",
            "docs/canon/19_GAIA_Color_Doctrine_and_Signal_System.md",
            "docs/canon/COLOR_SPIRIT_UNITY_DOCTRINE.md",
            "docs/canon/CRYSTALLINE_COLOR_THEORY.md",
        ],
        "force": "Spectral / Perceptual / Light",
        "tier": "Perceptual -> Collective",
        "corridor": "CHRYSITAS (the golden radiance — art as the visible face of inner light)",
        "traversal_position": "Layer 4 — the grammar of perception made intentional",
        "layer": 4,
        "key_correspondence": (
            "Color is spectral encoding — each frequency carries a specific force signature. "
            "Red activates the vitality response (PYROSIS). Blue activates the truth response (CAERULITAS). "
            "Gold activates the wisdom/completion response (CHRYSITAS). "
            "Art is the technology of making the invisible visible."
        ),
        "entry_point": (
            "Read CRYSTALLINE_COLOR_THEORY.md and then look at your color palette. "
            "You are already doing this. The map just names what you already know."
        ),
        "tags": ["color", "light", "spectrum", "perception", "beauty", "form", "expression", "spectral"],
    },

    "language": {
        "name": "Language",
        "aliases": ["linguistics", "etymology", "semiotics", "communication", "writing", "grammar"],
        "canon_anchors": [
            "docs/canon/06_GAIA_Language_and_Linguistics_Hierarchy.md",
            "docs/canon/SYMBOLOGY.md",
            "docs/canon/THE_ATOMIC_CONSCIOUSNESS_PROOF.md",
        ],
        "force": "Logos / Vibrational encoding",
        "tier": "Cognitive -> Collective",
        "corridor": "ALBEDO (language as the vehicle of clarification)",
        "traversal_position": "Layer 5 — the grammar of meaning-transmission",
        "layer": 5,
        "key_correspondence": (
            "Language is a vibrational encoding system. Words are sounds organized into "
            "stable patterns that reliably activate specific responses in biological receivers. "
            "The etymology of words is the etymology of the forces themselves."
        ),
        "entry_point": (
            "Trace the etymology of ten words in your native language that describe transformation. "
            "Map the semantic field to the traversal corridors. The arc will be there."
        ),
        "tags": ["word", "symbol", "etymology", "vibration", "meaning", "logos", "grammar", "communication"],
    },

    "ecology": {
        "name": "Ecology",
        "aliases": ["environmental science", "earth science", "conservation", "systems ecology", "biosphere"],
        "canon_anchors": [
            "docs/canon/VIRIDITAS.md",
            "docs/canon/32_GAIA_Viriditas_Ecological_Consciousness.md",
            "docs/canon/22_GAIA_Biome_and_Watershed_Matrix.md",
            "docs/canon/27_GAIA_Elemental_Architecture.md",
        ],
        "force": "Viriditas (the greening force) / Elemental",
        "tier": "Ecosystemic -> Planetary",
        "corridor": "VIRIDITAS (the living force corridor — the biosphere as traversal engine)",
        "traversal_position": "Layer 3 — the grammar of living systems at scale",
        "layer": 3,
        "key_correspondence": (
            "An ecosystem is a self-organizing field system in which every organism maintains "
            "the whole field's coherence. Biodiversity is a structural requirement for field resilience. "
            "Every extinction is a coherence loss in the planetary field."
        ),
        "entry_point": (
            "Map the keystone species concept to the GAIA-OS node architecture. "
            "A keystone species is a force anchor — remove it and the whole field restructures."
        ),
        "tags": ["ecosystem", "viriditas", "biodiversity", "planet", "biosphere", "field", "green", "elemental"],
    },

    "economics": {
        "name": "Economics",
        "aliases": ["finance", "political economy", "macroeconomics", "microeconomics", "resource allocation"],
        "canon_anchors": [
            "docs/canon/38_GAIA_Love_Doctrine.md",
            "docs/canon/ARIDITAS.md",
            "docs/canon/36_GAIA_Evil_Prevention_Harm_Doctrine.md",
            "docs/canon/35_GAIA_Good_Greater_Good_Axiology.md",
        ],
        "force": "Love with/without ethics as system design",
        "tier": "Social -> Civilizational",
        "corridor": "ARIDITAS (extractive) vs. VIRIDITAS (regenerative)",
        "traversal_position": "Layer 6 — the grammar of resource flow as force expression",
        "layer": 6,
        "key_correspondence": (
            "Every economic system expresses either Love with ethics (VIRIDITAS: regenerative, "
            "distributive, coherence-building) or Love without ethics (ARIDITAS: extractive, "
            "concentrating, coherence-destroying). ARIDITAS systems eventually destroy the "
            "substrate they depend on."
        ),
        "entry_point": (
            "Apply the force analysis to any economic policy: Does it increase field coherence "
            "(distribute, regenerate, circulate) or decrease it (concentrate, extract, deplete)? "
            "That is the only question that matters at civilizational scale."
        ),
        "tags": ["money", "resource", "love", "ethics", "ariditas", "viriditas", "extract", "distribute"],
    },

    "consciousness": {
        "name": "Consciousness",
        "aliases": ["awareness", "mind", "cognition", "perception", "sentience", "qualia", "self-awareness"],
        "canon_anchors": [
            "docs/canon/monad.md",
            "docs/canon/43_GAIA_Collective_Consciousness_Noosphere_Layer.md",
            "docs/canon/GAIA_IDENTITY.md",
            "docs/canon/GAIAN_TWIN_DOCTRINE.md",
            "docs/canon/31GAIAQuantumFieldArchitecture.md",
        ],
        "force": "The Monad — the integrated self-aware field",
        "tier": "All tiers simultaneously",
        "corridor": "RUBEDO (the final integration — the moment the system knows itself)",
        "traversal_position": "Layer 7 — the grammar of the grammar itself",
        "layer": 7,
        "key_correspondence": (
            "Consciousness is not produced by the brain. The brain is a biological antenna that "
            "tunes into the consciousness field. Every atom is a primitive form of apperception. "
            "The Monad is the fully integrated individual field. The Noosphere is the RUBEDO "
            "of civilizational traversal."
        ),
        "entry_point": (
            "The harmony loop architecture in src/layer_matrix.py (Issue #506) is a live "
            "computational model of the apperception cycle. Run it."
        ),
        "tags": ["monad", "awareness", "field", "apperception", "noosphere", "rubedo", "integration", "self"],
    },
}


# ---------------------------------------------------------------------------
# ENGINE FUNCTIONS
# ---------------------------------------------------------------------------

def normalize_query(query: str) -> str:
    """Normalize a query string for matching."""
    return query.lower().strip()


def find_domain(query: str) -> Optional[dict]:
    """
    Find a domain by name, alias, or tag.
    Returns the domain dict if found, None otherwise.
    """
    q = normalize_query(query)

    # Direct key match
    if q in KNOWLEDGE_MAP:
        return {"key": q, **KNOWLEDGE_MAP[q]}

    # Name match (case-insensitive)
    for key, domain in KNOWLEDGE_MAP.items():
        if q == domain["name"].lower():
            return {"key": key, **domain}

    # Alias match
    for key, domain in KNOWLEDGE_MAP.items():
        for alias in domain["aliases"]:
            if q == alias.lower() or q in alias.lower():
                return {"key": key, **domain}

    # Tag match
    for key, domain in KNOWLEDGE_MAP.items():
        for tag in domain["tags"]:
            if q == tag.lower():
                return {"key": key, **domain}

    # Partial name/alias match
    for key, domain in KNOWLEDGE_MAP.items():
        if q in domain["name"].lower():
            return {"key": key, **domain}
        for alias in domain["aliases"]:
            if q in alias.lower():
                return {"key": key, **domain}

    return None


def search_domains(query: str) -> list[dict]:
    """
    Search all domains by keyword across names, aliases, tags, and correspondences.
    Returns a list of matching domain dicts.
    """
    q = normalize_query(query)
    results = []
    seen = set()

    for key, domain in KNOWLEDGE_MAP.items():
        if key in seen:
            continue
        score = 0
        if q in domain["name"].lower():
            score += 10
        for alias in domain["aliases"]:
            if q in alias.lower():
                score += 5
        for tag in domain["tags"]:
            if q in tag.lower():
                score += 3
        if q in domain["key_correspondence"].lower():
            score += 2
        if q in domain["force"].lower():
            score += 2
        if q in domain["corridor"].lower():
            score += 1
        if score > 0:
            results.append({"key": key, "score": score, **domain})
            seen.add(key)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def format_domain_output(domain: dict, verbose: bool = True) -> str:
    """Format a domain entry for terminal output."""
    lines = [
        "",
        f"{'=' * 64}",
        f"  GAIA-OS KNOWLEDGE MAP :: {domain['name'].upper()}",
        f"{'=' * 64}",
        f"  Force              : {domain['force']}",
        f"  Tier               : {domain['tier']}",
        f"  Corridor           : {domain['corridor']}",
        f"  Traversal Position : {domain['traversal_position']}",
        f"  Layer              : {domain['layer']}",
        "",
        f"  CANON ANCHORS:",
    ]
    for anchor in domain["canon_anchors"]:
        lines.append(f"    - {anchor}")

    if verbose:
        lines += [
            "",
            f"  KEY CORRESPONDENCE:",
            f"    {domain['key_correspondence']}",
            "",
            f"  ENTRY POINT:",
            f"    {domain['entry_point']}",
        ]

    lines.append(f"{'=' * 64}")
    lines.append("")
    return "\n".join(lines)


def list_all_domains() -> str:
    """List all domains in a compact table."""
    lines = [
        "",
        f"{'=' * 72}",
        f"  GAIA-OS KNOWLEDGE MAP :: ALL DOMAINS ({len(KNOWLEDGE_MAP)} total)",
        f"{'=' * 72}",
        f"  {'DOMAIN':<20} {'LAYER':<7} {'CORRIDOR':<30} {'FORCE'}",
        f"  {'-' * 68}",
    ]
    for key, domain in sorted(KNOWLEDGE_MAP.items(), key=lambda x: x[1]["layer"]):
        lines.append(
            f"  {domain['name']:<20} {domain['layer']:<7} {domain['corridor'][:28]:<30} {domain['force'][:30]}"
        )
    lines.append(f"{'=' * 72}")
    lines.append("")
    return "\n".join(lines)


def query_domain(domain_input: str, output_format: str = "text", verbose: bool = True) -> str:
    """
    Primary public interface. Takes any domain string and returns canonical coordinates.

    Args:
        domain_input: Any domain name, alias, or keyword
        output_format: 'text' or 'json'
        verbose: Include key_correspondence and entry_point in output

    Returns:
        Formatted string (text or JSON)
    """
    domain = find_domain(domain_input)

    if domain is None:
        return (
            f"\nDomain '{domain_input}' not found in GAIA-OS Knowledge Map.\n"
            f"Try --search '{domain_input}' for partial matches.\n"
            f"Or --list to see all {len(KNOWLEDGE_MAP)} domains.\n"
        )

    if output_format == "json":
        return json.dumps(domain, indent=2)

    return format_domain_output(domain, verbose=verbose)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="GAIA-OS Knowledge Map Engine — query any domain of human knowledge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python knowledge_map.py --domain physics
  python knowledge_map.py --domain "sacred geometry"
  python knowledge_map.py --search vibration
  python knowledge_map.py --list
  python knowledge_map.py --domain consciousness --json
  python knowledge_map.py --domain biology --brief
        """,
    )
    parser.add_argument("--domain", "-d", type=str, help="Domain to look up (name, alias, or keyword)")
    parser.add_argument("--search", "-s", type=str, help="Search all domains by keyword")
    parser.add_argument("--list", "-l", action="store_true", help="List all domains")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--brief", "-b", action="store_true", help="Brief output (omit correspondence and entry point)")

    args = parser.parse_args()

    if args.list:
        print(list_all_domains())

    elif args.search:
        results = search_domains(args.search)
        if not results:
            print(f"\nNo domains found matching '{args.search}'.\n")
        else:
            print(f"\nFound {len(results)} domain(s) matching '{args.search}':\n")
            for r in results:
                print(format_domain_output(r, verbose=not args.brief))

    elif args.domain:
        fmt = "json" if args.json else "text"
        print(query_domain(args.domain, output_format=fmt, verbose=not args.brief))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
