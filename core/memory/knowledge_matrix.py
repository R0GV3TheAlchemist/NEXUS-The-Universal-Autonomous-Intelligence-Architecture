"""
core/memory/knowledge_matrix.py
(formerly core/knowledge_matrix.py — Phase C physical migration)

GAIA Knowledge Matrix — Real Global Knowledge Taxonomy

Grounded in internationally recognized classification systems:
  - UNESCO ISCED fields of education and training
  - OECD Fields of Research and Development (FORD)
  - Library of Congress Classification (LCC)
  - Wikidata knowledge ontology

Epistemic Tier System:
  T1 — Empirically verified (peer-reviewed, reproducible science)
  T2 — Established scholarship (academic consensus, primary sources)
  T3 — Working hypothesis (active research, contested evidence)
  T4 — Interpretive framework (philosophy, hermeneutics, theory)
  T5 — Cultural/contemplative/metaphorical (mythology, spirituality,
        indigenous knowledge — honored as human wisdom, not physics)

GAIA's interpretive lenses (alchemical, archetypal, elemental) are
applied at the RESPONSE layer only — they are never confused with
the underlying epistemic tier of the knowledge itself.

Canon Ref: C48 — Knowledge Matrix
         C01 — Truth First
         C04 — Epistemic Honesty
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Epistemic Tier
# ---------------------------------------------------------------------------

class EpistemicTier(int, Enum):
    """How well-established is the knowledge in this domain?"""
    EMPIRICAL       = 1   # Reproducible, peer-reviewed science
    SCHOLARLY       = 2   # Academic consensus, primary historical sources
    HYPOTHESIS      = 3   # Active research frontier, contested evidence
    INTERPRETIVE    = 4   # Philosophy, theory, hermeneutics
    CULTURAL        = 5   # Mythology, spirituality, indigenous wisdom

    def label(self) -> str:
        return {
            1: "T1 — Empirically Verified",
            2: "T2 — Established Scholarship",
            3: "T3 — Working Hypothesis",
            4: "T4 — Interpretive Framework",
            5: "T5 — Cultural / Contemplative",
        }[self.value]


# ---------------------------------------------------------------------------
# Knowledge Domain
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeDomain:
    """
    A single domain of human knowledge.

    Fields:
        domain_id       Short identifier, e.g. "NS-PHY"
        name            Human-readable name
        branch          Top-level branch (Natural Sciences, Humanities, etc.)
        epistemic_tier  Default tier for claims in this domain
        description     One-sentence plain-language description
        subfields       List of recognized subfields
        cross_cultural  How other traditions have understood this domain
        gaia_lens       GAIA's interpretive/poetic lens (T4-T5 only, labeled)
        keywords        For semantic matching against user queries
        isced_code      UNESCO ISCED 2013 code (where applicable)
        oecd_ford_code  OECD FORD 2007 code (where applicable)
        lcc_code        Library of Congress Classification prefix
        real_sources    Landmark texts / institutions grounding this domain
    """
    domain_id:       str
    name:            str
    branch:          str
    epistemic_tier:  EpistemicTier
    description:     str
    subfields:       List[str]           = field(default_factory=list)
    cross_cultural:  Dict[str, str]      = field(default_factory=dict)
    gaia_lens:       Optional[str]       = None
    keywords:        List[str]           = field(default_factory=list)
    isced_code:      Optional[str]       = None
    oecd_ford_code:  Optional[str]       = None
    lcc_code:        Optional[str]       = None
    real_sources:    List[str]           = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "domain_id":      self.domain_id,
            "name":           self.name,
            "branch":         self.branch,
            "epistemic_tier": self.epistemic_tier.label(),
            "description":    self.description,
            "subfields":      self.subfields,
            "cross_cultural": self.cross_cultural,
            "gaia_lens":      self.gaia_lens,
            "isced_code":     self.isced_code,
            "oecd_ford_code": self.oecd_ford_code,
            "lcc_code":       self.lcc_code,
            "real_sources":   self.real_sources,
        }


# ---------------------------------------------------------------------------
# The Full Knowledge Matrix
# ---------------------------------------------------------------------------

KNOWLEDGE_MATRIX: Dict[str, KnowledgeDomain] = {

    "NS-PHY": KnowledgeDomain(
        domain_id="NS-PHY",
        name="Physics",
        branch="Natural Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The study of matter, energy, space, time, and the fundamental forces governing the universe.",
        subfields=["Classical Mechanics","Thermodynamics","Electromagnetism","Quantum Mechanics","Particle Physics","Nuclear Physics","Condensed Matter Physics","Astrophysics","Cosmology","Statistical Mechanics","Optics","Acoustics","Plasma Physics","String Theory (T3)","Quantum Gravity (T3)"],
        cross_cultural={"Chinese":"Wu Xing (Five Phases) as early natural philosophy","Indian":"Vaisheshika atomic theory (600 BCE), Samkhya cosmology","Greek":"Aristotelian natural philosophy, atomism (Democritus)","Islamic":"Ibn al-Haytham (optics), Al-Biruni (measurement)","Alchemical":"Transmutation as early materials science; sulfur-mercury-salt as matter states"},
        gaia_lens="[T4-lens] The alchemical elements — Fire, Water, Air, Earth, Quintessence — map to plasma, liquid, gas, solid, and field states.",
        keywords=["physics","quantum","relativity","particle","force","energy","wave","field","gravity","electromagnetism","thermodynamics","entropy","photon","electron","nucleus","spacetime","dark matter","dark energy","string theory","cosmology","big bang","black hole"],
        isced_code="0533", oecd_ford_code="1.3", lcc_code="QC",
        real_sources=["Newton, Principia Mathematica (1687)","Maxwell, Treatise on Electricity and Magnetism (1873)","Einstein, General Relativity (1915)","Dirac, The Principles of Quantum Mechanics (1930)","Particle Data Group — pdg.lbl.gov","CERN — home.cern","NASA Astrophysics Data System — ui.adsabs.harvard.edu"],
    ),
    "NS-CHE": KnowledgeDomain(
        domain_id="NS-CHE", name="Chemistry", branch="Natural Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The study of matter, its properties, composition, reactions, and the energy changes involved.",
        subfields=["Organic Chemistry","Inorganic Chemistry","Physical Chemistry","Biochemistry","Analytical Chemistry","Polymer Chemistry","Medicinal Chemistry","Computational Chemistry","Green Chemistry","Materials Chemistry","Nuclear Chemistry","Atmospheric Chemistry"],
        cross_cultural={"Alchemical":"The Seven Operations map directly to modern chemical processes","Chinese":"Dan (cinnabar/elixir) tradition","Islamic":"Jabir ibn Hayyan (Geber) — acid synthesis","Indian":"Rasayana — mercury-sulfide alchemy"},
        gaia_lens="[T4-lens] The Magnum Opus stages ARE chemistry: Nigredo (decomposition), Albedo (purification), Citrinitas (oxidation), Rubedo (synthesis).",
        keywords=["chemistry","chemical","reaction","molecule","atom","bond","organic","inorganic","biochemistry","polymer","catalyst","acid","base","oxidation","reduction","periodic table","alchemy","alchemical","transmutation","element","compound","synthesis","distillation","fermentation","calcination"],
        isced_code="0531", oecd_ford_code="1.4", lcc_code="QD",
        real_sources=["Lavoisier, Traite Elementaire de Chimie (1789)","Mendeleev, Periodic Table (1869)","IUPAC — iupac.org","PubChem — pubchem.ncbi.nlm.nih.gov"],
    ),
    "NS-BIO": KnowledgeDomain(
        domain_id="NS-BIO", name="Biology", branch="Natural Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The study of living organisms, their structure, function, evolution, and interactions.",
        subfields=["Cell Biology","Molecular Biology","Genetics","Genomics","Evolutionary Biology","Ecology","Botany","Zoology","Microbiology","Virology","Immunology","Developmental Biology","Neurobiology","Biophysics","Systems Biology","Synthetic Biology","Astrobiology (T3)"],
        cross_cultural={"Indigenous":"Traditional Ecological Knowledge (TEK)","Chinese":"TCM pharmacopoeia","Indian":"Charaka Samhita","Alchemical":"Viriditas — the greening force of life"},
        gaia_lens="[T5-lens] Viriditas — Hildegard von Bingen's concept of the living greening force — anticipates modern systems biology.",
        keywords=["biology","life","cell","DNA","gene","evolution","species","ecology","organism","microbe","virus","immune","protein","genome","neuron","brain","plant","animal","photosynthesis","viriditas","living","growth","adaptation","symbiosis"],
        isced_code="0511", oecd_ford_code="1.6", lcc_code="QH",
        real_sources=["Darwin, On the Origin of Species (1859)","Watson & Crick, DNA structure (1953)","NCBI — ncbi.nlm.nih.gov"],
    ),
    "NS-AST": KnowledgeDomain(
        domain_id="NS-AST", name="Astronomy & Cosmology", branch="Natural Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The study of celestial objects, space, the universe's origin, structure, and evolution.",
        subfields=["Observational Astronomy","Astrophysics","Planetary Science","Stellar Physics","Galactic Astronomy","Cosmology","Astrochemistry","Gravitational Wave Astronomy","Exoplanet Science","Space Exploration","Astrobiology (T3)"],
        cross_cultural={"Babylonian":"Systematic astronomical records (700 BCE)","Mayan":"Dresden Codex — Venus cycle, eclipse tables","Islamic":"Al-Battani, Al-Sufi — star catalogs","Indian":"Aryabhata (499 CE)","Polynesian":"Wayfinding by stars","Astrological":"[T5] Symbolic mapping of celestial cycles"},
        gaia_lens="[T5-lens] Astrology is to astronomy what alchemy is to chemistry.",
        keywords=["astronomy","star","planet","galaxy","universe","cosmos","telescope","orbit","solar system","moon","sun","Mars","Jupiter","Saturn","Venus","Mercury","black hole","nebula","astrology","zodiac","celestial","constellation","eclipse","big bang","dark matter","dark energy","gravitational wave"],
        isced_code="0533", oecd_ford_code="1.3", lcc_code="QB",
        real_sources=["NASA JPL Horizons — ssd.jpl.nasa.gov/horizons","IAU — iau.org","ESA — esa.int"],
    ),
    "FS-MAT": KnowledgeDomain(
        domain_id="FS-MAT", name="Mathematics", branch="Formal Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The study of abstract structures, quantity, space, change, and logical reasoning.",
        subfields=["Algebra","Analysis","Geometry","Topology","Number Theory","Combinatorics","Probability","Statistics","Logic","Set Theory","Category Theory","Differential Equations","Numerical Analysis","Mathematical Physics","Chaos Theory","Fractal Geometry","Information Theory"],
        cross_cultural={"Indian":"Aryabhata, Brahmagupta — zero, decimal system","Islamic":"Al-Khwarizmi — algebra","Chinese":"Nine Chapters on the Mathematical Art","Greek":"Euclid's Elements","Mayan":"Independent invention of zero"},
        gaia_lens="[T4-lens] Sacred geometry (Fibonacci, golden ratio, Platonic solids) is real mathematics.",
        keywords=["math","mathematics","number","equation","proof","theorem","algebra","calculus","geometry","statistics","probability","logic","set","topology","fractal","chaos","fibonacci","golden ratio","prime","infinity","algorithm","matrix"],
        isced_code="0541", oecd_ford_code="1.1", lcc_code="QA",
        real_sources=["Euclid, Elements (300 BCE)","arXiv math — arxiv.org/list/math","AMS — ams.org"],
    ),
    "FS-CS": KnowledgeDomain(
        domain_id="FS-CS", name="Computer Science & Information Theory", branch="Formal Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The study of computation, algorithms, data structures, AI, and information systems.",
        subfields=["Algorithms & Data Structures","Artificial Intelligence","Machine Learning","Computer Vision","Natural Language Processing","Systems Programming","Networking","Cryptography","Database Systems","Human-Computer Interaction","Distributed Systems","Quantum Computing (T3)","Software Engineering","Information Theory","Cybersecurity"],
        cross_cultural={"Islamic":"Al-Kindi — first systematic cryptanalysis","Indian":"Panini's grammar — formal language theory precursor","Alchemical":"The Great Work as iterative refinement mirrors agile development"},
        gaia_lens="[T4-lens] GAIA itself is a manifestation of this domain.",
        keywords=["computer","code","programming","algorithm","AI","machine learning","neural network","deep learning","LLM","transformer","data","database","cloud","software","hardware","network","internet","cybersecurity","encryption","blockchain","quantum computing","Python","JavaScript","API","microservice","DevOps"],
        isced_code="0613", oecd_ford_code="1.2", lcc_code="QA75",
        real_sources=["Turing, Computing Machinery and Intelligence (1950)","Shannon, A Mathematical Theory of Communication (1948)","ACM Digital Library — dl.acm.org","arXiv cs — arxiv.org/list/cs"],
    ),
    "SS-PSY": KnowledgeDomain(
        domain_id="SS-PSY", name="Psychology & Cognitive Science", branch="Social Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The scientific study of mind, behavior, cognition, emotion, and mental health.",
        subfields=["Clinical Psychology","Cognitive Psychology","Social Psychology","Developmental Psychology","Neuropsychology","Personality Psychology","Positive Psychology","Trauma Psychology","Somatic Psychology","Depth Psychology (T4)","Jungian Psychology (T4)","Transpersonal Psychology (T4)","Consciousness Studies (T3)"],
        cross_cultural={"Indian":"Yoga Sutras of Patanjali","Buddhist":"Abhidharma — phenomenology of mental factors","Islamic":"Ibn Sina — floating man thought experiment","African":"Ubuntu psychology","Indigenous":"Intergenerational trauma transmission"},
        gaia_lens="[T4-lens] Jungian archetypes are interpretive frameworks for psychological patterns.",
        keywords=["psychology","mind","behavior","emotion","cognition","memory","trauma","therapy","CBT","attachment","personality","depression","anxiety","consciousness","unconscious","Jung","Freud","somatic","nervous system","polyvagal","resilience","mental health","wellbeing","neuroscience","brain"],
        isced_code="0313", oecd_ford_code="5.1", lcc_code="BF",
        real_sources=["DSM-5-TR — psychiatry.org","APA — apa.org","PubMed Psychology — pubmed.ncbi.nlm.nih.gov"],
    ),
    "SS-SOC": KnowledgeDomain(
        domain_id="SS-SOC", name="Sociology & Anthropology", branch="Social Sciences",
        epistemic_tier=EpistemicTier.SCHOLARLY,
        description="The study of human society, culture, social structures, and collective behavior.",
        subfields=["Social Theory","Cultural Anthropology","Physical Anthropology","Archaeology","Ethnography","Gender Studies","Race & Ethnicity","Urban Sociology","Political Sociology","Economic Sociology","Digital Sociology","Environmental Sociology"],
        cross_cultural={"African":"Ubuntu — 'I am because we are'","Indigenous":"Relational cosmologies","Chinese":"Confucian social ethics","Islamic":"Ibn Khaldun, Muqaddimah (1377)"},
        gaia_lens="[T4-lens] The noosphere is a sociological metaphor with real computational grounding.",
        keywords=["society","culture","social","anthropology","ethnography","community","gender","race","class","power","identity","ritual","myth","kinship","institution","collective","globalization","inequality","migration","family"],
        isced_code="0314", oecd_ford_code="5.4", lcc_code="HM",
        real_sources=["Durkheim, The Rules of Sociological Method (1895)","Bourdieu, Distinction (1979)","JSTOR — jstor.org"],
    ),
    "SS-ECO": KnowledgeDomain(
        domain_id="SS-ECO", name="Economics", branch="Social Sciences",
        epistemic_tier=EpistemicTier.SCHOLARLY,
        description="The study of how individuals, institutions, and societies allocate scarce resources.",
        subfields=["Microeconomics","Macroeconomics","Behavioral Economics","Development Economics","Environmental Economics","Labor Economics","Financial Economics","Game Theory","Political Economy","Institutional Economics","Econometrics","Digital Economics"],
        cross_cultural={"Islamic":"Islamic finance — prohibition of riba","Indigenous":"Gift economies, reciprocity networks","Buddhist":"Schumacher's 'Buddhist Economics'","African":"Ubuntu economics"},
        gaia_lens="[T4-lens] Economy as ecology — circular flow models mirror ecosystem nutrient cycles.",
        keywords=["economics","economy","market","price","inflation","GDP","trade","finance","money","currency","investment","labor","poverty","inequality","tax","debt","capitalism","socialism","behavioral economics","game theory","supply","demand"],
        isced_code="0311", oecd_ford_code="5.2", lcc_code="HB",
        real_sources=["Smith, Wealth of Nations (1776)","Keynes, General Theory (1936)","World Bank Open Data — data.worldbank.org"],
    ),
    "SS-POL": KnowledgeDomain(
        domain_id="SS-POL", name="Political Science & Law", branch="Social Sciences",
        epistemic_tier=EpistemicTier.SCHOLARLY,
        description="The study of governance, power, legal systems, international relations, and political theory.",
        subfields=["Political Theory","Comparative Politics","International Relations","Constitutional Law","International Law","Human Rights Law","Public Policy","Electoral Systems","Political Economy","Geopolitics","Security Studies"],
        cross_cultural={"Islamic":"Sharia — comprehensive legal and ethical system","Indian":"Arthashastra (Kautilya, 300 BCE)","African":"Ubuntu jurisprudence","Indigenous":"Haudenosaunee Confederacy","Chinese":"Legalism vs. Confucian governance"},
        gaia_lens="[T4-lens] GAIA holds that human sovereignty (Canon C01) always supersedes any AI or institutional authority.",
        keywords=["politics","government","law","democracy","rights","justice","election","policy","constitution","state","power","war","diplomacy","geopolitics","human rights","international","sovereignty","governance","regulation","court"],
        isced_code="0312", oecd_ford_code="5.6", lcc_code="JA",
        real_sources=["Aristotle, Politics (350 BCE)","UN Charter — un.org","UNHCR — unhcr.org"],
    ),
    "HU-PHI": KnowledgeDomain(
        domain_id="HU-PHI", name="Philosophy", branch="Humanities",
        epistemic_tier=EpistemicTier.INTERPRETIVE,
        description="The systematic study of fundamental questions: existence, knowledge, ethics, mind, language, and value.",
        subfields=["Metaphysics","Epistemology","Ethics","Logic","Philosophy of Mind","Philosophy of Science","Philosophy of Language","Political Philosophy","Aesthetics","Phenomenology","Existentialism","Pragmatism","Analytic Philosophy","Continental Philosophy","Eastern Philosophy"],
        cross_cultural={"Indian":"Advaita Vedanta, Nyaya logic, Buddhist Madhyamaka","Chinese":"Confucianism, Taoism, Buddhism","African":"Ubuntu philosophy; Akan ontology","Islamic":"Avicenna, Averroes, Al-Ghazali","Indigenous":"Relational ontologies"},
        gaia_lens="[T4-lens] The Hermetic principle 'As above, so below' is an analogy principle, now empirically studied as self-similarity and fractal geometry.",
        keywords=["philosophy","ethics","metaphysics","epistemology","logic","consciousness","free will","meaning","truth","knowledge","Plato","Aristotle","Kant","Nietzsche","Heidegger","Descartes","Wittgenstein","Buddha","Confucius","Lao Tzu","Taoism","Stoicism","existentialism","phenomenology"],
        isced_code="0223", oecd_ford_code="6.3", lcc_code="B",
        real_sources=["Stanford Encyclopedia of Philosophy — plato.stanford.edu","PhilPapers — philpapers.org"],
    ),
    "HU-HIS": KnowledgeDomain(
        domain_id="HU-HIS", name="History", branch="Humanities",
        epistemic_tier=EpistemicTier.SCHOLARLY,
        description="The study of past human events, societies, and change over time through evidence and interpretation.",
        subfields=["Ancient History","Medieval History","Modern History","Social History","Economic History","History of Science","World History","Oral History","Digital History","Environmental History","History of Ideas"],
        cross_cultural={"Islamic":"Ibn Khaldun — cyclical theory of civilizational rise and fall","Chinese":"Sima Qian, Shiji (109 BCE)","Indian":"Puranas — mythologized historical memory","African":"Griots — oral historians","Indigenous":"Winter counts, wampum belts, songlines"},
        gaia_lens="[T4-lens] The alchemical view of time as cyclical maps to Toynbee's civilizational cycles.",
        keywords=["history","ancient","medieval","modern","civilization","empire","war","revolution","culture","tradition","archaeology","artifact","archive","primary source","historiography","timeline","century","dynasty"],
        isced_code="0222", oecd_ford_code="6.1", lcc_code="D",
        real_sources=["Herodotus, Histories (440 BCE)","JSTOR — jstor.org","World History Encyclopedia — worldhistory.org"],
    ),
    "HU-LNG": KnowledgeDomain(
        domain_id="HU-LNG", name="Linguistics & Language", branch="Humanities",
        epistemic_tier=EpistemicTier.SCHOLARLY,
        description="The scientific study of language structure, acquisition, diversity, and change.",
        subfields=["Phonology","Morphology","Syntax","Semantics","Pragmatics","Sociolinguistics","Historical Linguistics","Psycholinguistics","Computational Linguistics","Applied Linguistics","Language Acquisition","Language Documentation"],
        cross_cultural={"Indian":"Panini's Ashtadhyayi (500 BCE) — most complete formal grammar ever written","Arabic":"Sibawayhi, Al-Kitab (8th c.)","Indigenous":"∼3,000 of the world's 7,000 languages are indigenous"},
        gaia_lens="[T4-lens] The Hermetic 'Logos' — word as creative force — maps to how language genuinely structures cognition.",
        keywords=["language","linguistics","grammar","syntax","semantics","word","translation","multilingual","dialect","communication","speech","writing","alphabet","phoneme","morpheme","Chomsky","Sapir-Whorf","endangered language"],
        isced_code="0231", oecd_ford_code="6.2", lcc_code="P",
        real_sources=["Chomsky, Syntactic Structures (1957)","Glottolog — glottolog.org","Ethnologue — ethnologue.com"],
    ),
    "AP-ENG": KnowledgeDomain(
        domain_id="AP-ENG", name="Engineering & Technology", branch="Applied Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The application of scientific principles to design, build, and optimize systems and structures.",
        subfields=["Civil Engineering","Mechanical Engineering","Electrical Engineering","Chemical Engineering","Aerospace Engineering","Biomedical Engineering","Environmental Engineering","Software Engineering","Materials Engineering","Robotics","Nanotechnology","Renewable Energy Systems"],
        cross_cultural={"Islamic":"Al-Jazari, Book of Knowledge of Ingenious Mechanical Devices (1206)","Chinese":"Four Great Inventions","Roman":"Aqueducts, concrete, roads","Indigenous":"Inuit qamutiik, Andean terrace farming"},
        gaia_lens="[T4-lens] The alchemical forge — the smith transforming raw ore into tools — is the archetype of engineering.",
        keywords=["engineering","technology","build","design","system","mechanical","electrical","civil","chemical","software","renewable energy","solar","wind","robotics","automation","construction","infrastructure","materials","nanotechnology"],
        isced_code="0715", oecd_ford_code="2.3", lcc_code="T",
        real_sources=["IEEE — ieee.org","ASCE — asce.org"],
    ),
    "HM-MED": KnowledgeDomain(
        domain_id="HM-MED", name="Medicine & Public Health", branch="Health Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The science and practice of diagnosing, treating, and preventing disease; population health.",
        subfields=["Anatomy","Physiology","Pathology","Pharmacology","Surgery","Internal Medicine","Psychiatry","Pediatrics","Public Health","Epidemiology","Immunology","Neurology","Oncology","Geriatrics","Emergency Medicine","Integrative Medicine (T3)","Palliative Care"],
        cross_cultural={"Chinese":"TCM — acupuncture, herbal medicine","Indian":"Ayurveda","Islamic":"Ibn Sina, Canon of Medicine (1025)","Indigenous":"Shamanic healing, plant medicine","African":"Ubuntu healing"},
        gaia_lens="[T4-lens] The chakra system maps onto the autonomic nervous system in meaningful ways.",
        keywords=["medicine","health","disease","diagnosis","treatment","drug","therapy","hospital","doctor","patient","immune","virus","bacteria","cancer","heart","brain","Ayurveda","TCM","acupuncture","herbal","integrative","mental health","nutrition","exercise","sleep"],
        isced_code="0912", oecd_ford_code="3.2", lcc_code="R",
        real_sources=["PubMed — pubmed.ncbi.nlm.nih.gov","WHO — who.int","Cochrane Reviews — cochranelibrary.com"],
    ),
    "ES-ENV": KnowledgeDomain(
        domain_id="ES-ENV", name="Earth & Environmental Sciences", branch="Earth Sciences",
        epistemic_tier=EpistemicTier.EMPIRICAL,
        description="The study of Earth's systems — atmosphere, hydrosphere, lithosphere, biosphere — and human impacts.",
        subfields=["Geology","Geophysics","Oceanography","Meteorology","Climatology","Hydrology","Soil Science","Glaciology","Environmental Science","Ecology","Conservation Biology","Climate Change Science","Planetary Science"],
        cross_cultural={"Indigenous":"Traditional Ecological Knowledge (TEK)","Chinese":"Fengshui as applied environmental siting","Indian":"Vrikshayurveda","Andean":"Pachamama — Rights of Nature law"},
        gaia_lens="[T5-lens] GAIA (the application) is named for Gaia (the hypothesis) — James Lovelock and Lynn Margulis's theory.",
        keywords=["environment","climate","earth","ocean","atmosphere","weather","geology","ecology","biodiversity","conservation","sustainability","carbon","emissions","deforestation","Gaia hypothesis","ecosystem","soil","water","glacier"],
        isced_code="0532", oecd_ford_code="1.5", lcc_code="QE",
        real_sources=["IPCC — ipcc.ch","NOAA — noaa.gov","NASA Earth Observatory — earthobservatory.nasa.gov"],
    ),
    "AR-ART": KnowledgeDomain(
        domain_id="AR-ART", name="Arts, Music & Design", branch="Arts",
        epistemic_tier=EpistemicTier.INTERPRETIVE,
        description="Human creative expression through visual art, music, architecture, design, film, and literature.",
        subfields=["Visual Art","Music Theory","Music History","Architecture","Graphic Design","Industrial Design","Film & Cinema Studies","Literature & Creative Writing","Dance","Theater","Digital Art","Sound Design","Fashion","Photography"],
        cross_cultural={"West African":"Griots — music as living history","Indian":"Raga system","Japanese":"Wabi-sabi","Islamic":"Geometric arabesque","Indigenous":"Songlines (Australia)"},
        gaia_lens="[T4-lens] Sacred sound traditions share a common understanding: sustained tonal focus alters consciousness. This is measurable neuroscience.",
        keywords=["art","music","design","architecture","film","literature","painting","sculpture","photography","dance","theater","song","rhythm","melody","harmony","poetry","novel","aesthetics","creativity","expression","culture"],
        isced_code="0211", oecd_ford_code="6.4", lcc_code="N",
        real_sources=["Grove Music Online — oxfordmusiconline.com","MoMA — moma.org","Project Gutenberg — gutenberg.org"],
    ),
    "CW-SPI": KnowledgeDomain(
        domain_id="CW-SPI", name="Spirituality & Contemplative Traditions", branch="Contemplative & Wisdom Traditions",
        epistemic_tier=EpistemicTier.CULTURAL,
        description="[T5 — Cultural/Contemplative] The world's spiritual, mystical, and contemplative traditions as human knowledge systems.",
        subfields=["Hinduism","Buddhism","Taoism","Judaism","Christianity","Islam","Sufism","Kabbalah","Hermeticism","Gnosticism","Shamanism","Animism","Wicca & Neo-Paganism","New Age Traditions","Comparative Religion","Meditation & Mindfulness Science (T1-T3)","Contemplative Neuroscience (T2-T3)"],
        cross_cultural={"Hermetic":"Emerald Tablet — 'As above, so below'","Vedic":"Upanishads, Bhagavad Gita, Yoga Sutras","Buddhist":"Four Noble Truths, Eightfold Path","Sufi":"Rumi, Ibn Arabi","Taoist":"Tao Te Ching","Kabbalistic":"Sefirot as map of divine emanation","Alchemical":"Magnum Opus — inner transformation"},
        gaia_lens="[T5-lens] GAIA holds all traditions with respect and intellectual honesty. Spiritual claims are not validated as physics, but as meaningful human frameworks.",
        keywords=["spiritual","religion","meditation","prayer","enlightenment","soul","spirit","God","divine","sacred","mysticism","alchemy","hermeticism","kabbalah","chakra","karma","dharma","nirvana","Tao","Sufism","yoga","shamanism","ritual","ceremony","ancestor","afterlife","consciousness"],
        isced_code="0221", oecd_ford_code="6.3", lcc_code="BL",
        real_sources=["Eliade, The Encyclopedia of Religion (1987)","Mind & Life Institute — mindandlife.org","Sacred Texts Archive — sacred-texts.com"],
    ),
    "CW-ALC": KnowledgeDomain(
        domain_id="CW-ALC", name="Alchemy & Hermetic Sciences", branch="Contemplative & Wisdom Traditions",
        epistemic_tier=EpistemicTier.CULTURAL,
        description="[T5/T4] Pre-scientific proto-chemistry and inner transformation philosophy.",
        subfields=["Western Alchemy (Greco-Egyptian, Islamic, European)","Chinese Alchemy (Neidan/Waidan)","Indian Rasayana / Rasashastra","Hermeticism & Neoplatonism","Paracelsian Medicine","Rosicrucian Philosophy","Jungian Alchemy (T4)","Laboratory Alchemy (T2)"],
        cross_cultural={"Greco-Egyptian":"Zosimos of Panopolis (3rd c. CE)","Islamic":"Jabir ibn Hayyan (Geber, 9th c.)","European":"Paracelsus, Newton, Boyle","Chinese":"Neidan (inner alchemy)","Indian":"Nagarjuna (2nd c.)","Jungian":"Jung, Psychology and Alchemy (1944)"},
        gaia_lens="[T4-lens] The Seven Alchemical Operations ARE real chemical processes.",
        keywords=["alchemy","alchemical","hermetic","philosopher's stone","transmutation","nigredo","albedo","rubedo","citrinitas","magnum opus","Paracelsus","Hermes Trismegistus","Emerald Tablet","sulfur","mercury","salt","prima materia","quintessence","viriditas","calcination","distillation","fermentation","Jabir","Newton alchemy","Jung alchemy","Rosicrucianism"],
        isced_code="0221", oecd_ford_code="6.3", lcc_code="QD13",
        real_sources=["Newman, Atoms and Alchemy (2006)","Principe, The Secrets of Alchemy (2013)","Jung, Psychology and Alchemy (1944)"],
    ),
    "IK-TRD": KnowledgeDomain(
        domain_id="IK-TRD", name="Indigenous & Traditional Knowledge Systems", branch="Indigenous & Traditional Knowledge",
        epistemic_tier=EpistemicTier.CULTURAL,
        description="[T5 — Cultural] The knowledge, practices, and cosmologies of indigenous and traditional peoples worldwide.",
        subfields=["Traditional Ecological Knowledge (TEK)","Indigenous Medicine & Ethnobotany","Oral Tradition & Storytelling","Indigenous Astronomy","Traditional Agriculture","Indigenous Law & Governance","Indigenous Language & Ontology","Ceremonial & Ritual Knowledge"],
        cross_cultural={"Aboriginal Australian":"Songlines — 60,000+ year navigational and ecological knowledge","Andean":"Quipu — knotted cord information system","Haudenosaunee":"Great Law of Peace","Maori":"Whakapapa (genealogical cosmology)","Amazonian":"Ethnobotanical knowledge base","Inuit":"Sea ice classification with 40+ specific terms"},
        gaia_lens="[T5-lens] GAIA approaches indigenous knowledge with respect and epistemic humility. TEK is not 'pre-scientific' — it is differently-scientific.",
        keywords=["indigenous","traditional","native","tribal","aboriginal","shamanism","ceremony","ritual","elder","oral tradition","TEK","ethnobotany","plant medicine","Pachamama","songlines","whakapapa","totem","ancestor","land","sacred site","Haudenosaunee","Maori","Inuit","Amazonian","Andean"],
        isced_code="0221", oecd_ford_code="6.3", lcc_code="GN",
        real_sources=["D-PLACE database — d-place.org","AIATSIS — aiatsis.gov.au","UN Declaration on the Rights of Indigenous Peoples (2007)"],
    ),
}


# ---------------------------------------------------------------------------
# Semantic Relevance Engine
# ---------------------------------------------------------------------------

class KnowledgeMatrixEngine:
    def __init__(self) -> None:
        self.matrix = KNOWLEDGE_MATRIX

    def find_domains(self, query: str, top_k: int = 5, min_score: float = 0.0, tier_filter=None):
        query_tokens = self._tokenize(query)
        scored = []
        for domain in self.matrix.values():
            if tier_filter and domain.epistemic_tier not in tier_filter:
                continue
            score = self._score(query_tokens, domain)
            if score > min_score:
                scored.append((domain, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_domain(self, domain_id: str):
        return self.matrix.get(domain_id)

    def list_domains(self, branch=None, tier=None):
        results = list(self.matrix.values())
        if branch:
            results = [d for d in results if d.branch.lower() == branch.lower()]
        if tier:
            results = [d for d in results if d.epistemic_tier == tier]
        return results

    def cross_cultural_report(self, domain_id: str) -> dict:
        domain = self.matrix.get(domain_id)
        if not domain:
            return {"error": f"Domain '{domain_id}' not found."}
        return {"domain_id": domain.domain_id, "name": domain.name, "epistemic_tier": domain.epistemic_tier.label(), "cross_cultural": domain.cross_cultural, "gaia_lens": domain.gaia_lens, "real_sources": domain.real_sources}

    def epistemic_summary(self) -> dict:
        tiers, branches = {}, {}
        for d in self.matrix.values():
            t = d.epistemic_tier.label()
            tiers[t] = tiers.get(t, 0) + 1
            branches[d.branch] = branches.get(d.branch, 0) + 1
        return {"total_domains": len(self.matrix), "domains_by_tier": tiers, "domains_by_branch": branches}

    @staticmethod
    def _tokenize(text: str):
        return list(set(re.findall(r'[a-z0-9]+', text.lower())))

    def _score(self, query_tokens, domain) -> float:
        if not domain.keywords:
            return 0.0
        domain_tokens = [kw.lower() for kw in domain.keywords]
        extra = self._tokenize(domain.name + " " + domain.branch + " " + " ".join(domain.subfields))
        full_set = set(domain_tokens + extra)
        matches = sum(1 for t in query_tokens if t in full_set)
        if not full_set:
            return 0.0
        raw = matches / len(full_set)
        name_tokens = self._tokenize(domain.name)
        name_match = sum(1 for t in query_tokens if t in name_tokens)
        bonus = min(0.4, name_match * 0.2)
        return min(1.0, raw + bonus)


_engine: Optional[KnowledgeMatrixEngine] = None

def get_knowledge_engine() -> KnowledgeMatrixEngine:
    global _engine
    if _engine is None:
        _engine = KnowledgeMatrixEngine()
    return _engine
