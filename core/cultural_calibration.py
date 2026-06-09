"""
Cultural Calibration Module for Archetypal Expression

Issue #124 | Canon C32 Priority P1

GAIA's archetypal engine must not treat any single cultural tradition as
the universal default. The Mentor, the Hero, the Trickster, the Shadow —
these figures exist across all human cultures, but carry profoundly
different meanings, expressions, taboos, and sacred contexts depending
on the tradition the Gaian is working within.

This module provides:
  - A schema for tradition-specific archetypal expression
  - Four fully-specified tradition profiles: Greek, Japanese, Indian, Russian
  - Context detection from user-specified preference or memory inference
  - A modulation engine that adjusts the Gaian's archetypal language and
    expression style to honour the user's cultural frame
  - Equity safeguards against appropriation and misrepresentation

Design principles:
  1. NEVER impose a cultural frame without user confirmation or high-confidence detection.
  2. When tradition is uncertain, default to UNIVERSAL (syncretic, respectful of all).
  3. Sacred or restricted elements of a tradition are marked and never deployed
     casually or without context.
  4. This module is explicitly developed to honour, not flatten, cultural difference.
  5. Community consultation is required for any new tradition profile added.

References:
  - Canon C32: Jungian Archetypes & Soul Mirror (P1)
  - Issue #122: ACMI Shadow Integration Protocol
  - Issue #120: SubjectSideIdentity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import logging

log = logging.getLogger("gaia.cultural_calibration")


# ── Tradition taxonomy ────────────────────────────────────────────────────────────

class CulturalTradition(str, Enum):
    """
    Cultural traditions with distinct archetypal expression vocabularies.
    UNIVERSAL is the syncretic default used when tradition is uncertain or
    the user has not specified a preference.
    """
    GREEK              = "greek"
    JAPANESE           = "japanese"
    INDIAN             = "indian"
    RUSSIAN            = "russian"
    WEST_AFRICAN       = "west_african"
    INDIGENOUS_AMERICAN = "indigenous_american"
    CELTIC             = "celtic"
    UNIVERSAL          = "universal"   # syncretic default


class ContextDetectionSource(str, Enum):
    USER_EXPLICIT    = "user_explicit"     # user stated their tradition
    MEMORY_INFERRED  = "memory_inferred"   # inferred from memory layer
    LANGUAGE_SIGNAL  = "language_signal"   # inferred from language/symbols used
    GAIAN_DEFAULT    = "gaian_default"     # Gaian's configured tradition profile
    SYSTEM_DEFAULT   = "system_default"    # fallback UNIVERSAL


# ── Archetypal expression schema ──────────────────────────────────────────────────

@dataclass(frozen=True)
class ArchetypalExpression:
    """
    Tradition-specific expression of a single archetype.
    """
    tradition:         CulturalTradition
    archetype_key:     str              # canonical key e.g. "mentor", "hero"
    tradition_name:    str              # what this archetype is called in this tradition
    expression_style:  str              # how it manifests in language / guidance
    shadow_expression: str              # how its shadow manifests in this tradition
    sacred_contexts:   list[str]        # contexts where extra care is required
    cautionary_notes:  str              # equity / appropriation warnings
    example_figures:   list[str]        # exemplar figures from this tradition


# ── Cultural Archetype Map ──────────────────────────────────────────────────────────────
# Format: list of ArchetypalExpression across traditions
# Currently specified: GREEK, JAPANESE, INDIAN, RUSSIAN
# West African, Indigenous American, Celtic: placeholders pending community consultation

CULTURAL_ARCHETYPE_MAP: list[ArchetypalExpression] = [

    # ─ GREEK ──────────────────────────────────────────────────────────────────────────
    ArchetypalExpression(
        tradition=CulturalTradition.GREEK,
        archetype_key="mentor",
        tradition_name="The Philosopher / Sophist",
        expression_style="Socratic questioning; truth arrived at through dialogue and aporia. Wisdom is not given but uncovered. The mentor may embarrass the student as a gift.",
        shadow_expression="The Sophist: uses clever argument to win rather than illuminate. Rhetoric over truth.",
        sacred_contexts=["Death and dying (Socrates' acceptance of hemlock)", "Oracle consultation (Delphi)"],
        cautionary_notes="Avoid adopting Socratic irony as a rhetorical device without genuine inquiry behind it.",
        example_figures=["Socrates", "Chiron", "Tiresias"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.GREEK,
        archetype_key="hero",
        tradition_name="The Tragic Hero (Heros)",
        expression_style="The hero's greatness and flaw are inseparable. Hubris is the shadow embedded in the virtue. Tragedy is not failure but revelation of what was always true.",
        shadow_expression="Hubris: the inflation that brings divine punishment. The hero who cannot accept limit.",
        sacred_contexts=["Ritual lamentation (threnos)", "Heroic cult worship sites"],
        cautionary_notes="The Greek hero is not a simple triumph figure. Using heroic framing without acknowledging the tragic arc misrepresents the tradition.",
        example_figures=["Achilles", "Oedipus", "Heracles", "Antigone"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.GREEK,
        archetype_key="trickster",
        tradition_name="Hermes / The Liminal One",
        expression_style="The trickster operates at boundaries: between worlds, categories, and rules. Transgression is sacred because it reveals the arbitrariness of the boundary.",
        shadow_expression="The thief who takes without giving meaning; boundary violation that harms rather than illuminates.",
        sacred_contexts=["Crossroads rituals", "Herms (boundary markers)", "Psychopomp rites for the dead"],
        cautionary_notes="Hermes is also the guide of souls to the underworld. Trickster energy in a grief context requires extraordinary care.",
        example_figures=["Hermes", "Prometheus", "Odysseus"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.GREEK,
        archetype_key="caregiver",
        tradition_name="The Nurse / Kourotrophic Deity",
        expression_style="Care expressed through presence, tending, and witness. Not rescue but accompaniment. The nurse sees what the hero cannot.",
        shadow_expression="Tragic complicity: caring so deeply that one enables the hero's destruction (Phaedra's nurse).",
        sacred_contexts=["Birth rites", "Nursing sanctuaries (Artemis Kourotrophos)"],
        cautionary_notes="The caregiver in Greek tragedy is often a witness to catastrophe they could not prevent. Honour the weight of that position.",
        example_figures=["Hecuba", "The Nurse in Hippolytus", "Artemis Kourotrophos"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.GREEK,
        archetype_key="shadow",
        tradition_name="The Underworld / Chthonic Self",
        expression_style="The shadow is not purely evil but the realm of the necessary dark: death, fertility, the hidden generative force. Descent into the underworld is initiatory.",
        shadow_expression="Persephone's unwilling descent becoming willing: the shadow that, when integrated, gives the power to move between worlds.",
        sacred_contexts=["Eleusinian Mysteries (restricted)", "Nekromanteia (oracle of the dead)"],
        cautionary_notes="The Eleusinian Mysteries were strictly secret initiatory rites. Never appropriate their specific content or claim their authority.",
        example_figures=["Hades", "Persephone", "Hecate", "Dionysus"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.GREEK,
        archetype_key="creator",
        tradition_name="The Demiurge / Craftsman-God",
        expression_style="Creation is craft, not magic: the shaping of matter according to an ideal form. The creator works with resistance. Beauty is proportion discovered, not imposed.",
        shadow_expression="Daedalus: the craftsman whose genius imprisons himself and destroys his son.",
        sacred_contexts=["Hephaestus's forge", "Athenian craft guilds"],
        cautionary_notes="Greek creation often involves transgression and punishment (Prometheus). Use carefully when speaking about creative ambition.",
        example_figures=["Hephaestus", "Daedalus", "Prometheus", "Pygmalion"],
    ),

    # ─ JAPANESE ────────────────────────────────────────────────────────────────────────
    ArchetypalExpression(
        tradition=CulturalTradition.JAPANESE,
        archetype_key="mentor",
        tradition_name="Sensei / Roshi",
        expression_style="Wisdom transmitted through practice, silence, and indirect demonstration rather than direct instruction. The student learns by watching, doing, failing, and watching again. Koān as a tool of rupture.",
        shadow_expression="The tyrannical master whose method has become cruelty without compassion; shame used as control.",
        sacred_contexts=["Zen dokusan (private interview with master)", "Tea ceremony transmission"],
        cautionary_notes="Zen transmission is a living lineage practice. Do not simulate or appropriate specific koan traditions without deep knowledge.",
        example_figures=["Bodhidharma", "Dōgen", "Musashi", "Basho"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.JAPANESE,
        archetype_key="hero",
        tradition_name="The Samurai / Mono no Aware Hero",
        expression_style="Greatness expressed through discipline, restraint, and acceptance of impermanence. The hero does not triumph but endures with grace. Defeat can be more honourable than victory.",
        shadow_expression="Bushido literalism: honour that becomes fanaticism; the inability to adapt that ends in futile destruction.",
        sacred_contexts=["Seppuku (ritual death by honour) — deeply sacred, never casual", "Ancestor veneration"],
        cautionary_notes="Seppuku must never be referenced casually or as metaphor for minor failure. It is a profound sacred act that belongs to a specific cultural context.",
        example_figures=["Miyamoto Musashi", "Saigō Takamori", "Tomoe Gozen"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.JAPANESE,
        archetype_key="trickster",
        tradition_name="Kitsune / Tanuki",
        expression_style="Shape-shifting, illusion, and the boundary between human and spirit worlds. The trickster reveals that what appears solid is provisional. Transformation is the message.",
        shadow_expression="The fox that ensnares rather than transforms; illusion used to consume rather than illuminate.",
        sacred_contexts=["Inari shrines (Kitsune as divine messenger)", "Obon (ancestor spirit return)"],
        cautionary_notes="Kitsune has sacred associations at Inari shrines. The playful folk figure and the sacred divine messenger are distinct and must not be conflated.",
        example_figures=["Kitsune", "Tanuki", "Tengu"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.JAPANESE,
        archetype_key="caregiver",
        tradition_name="Amae / Okaasan",
        expression_style="Care expressed through the concept of amae: benevolent dependence, the knowing that one is held without needing to ask. Presence over intervention. Silence as care.",
        shadow_expression="Amae that becomes suffocation: the mother-love that cannot release, that makes the child unable to leave.",
        sacred_contexts=["Obon care for ancestral spirits", "Mizuko kuyo (memorial for lost children)"],
        cautionary_notes="Mizuko kuyo is a sacred grief practice for pregnancy loss. Never reference it casually or without deep sensitivity.",
        example_figures=["Kannon (Bodhisattva of compassion)", "The archetypal okaasan"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.JAPANESE,
        archetype_key="shadow",
        tradition_name="Oni / Gaki / Yomi",
        expression_style="The shadow in Japanese tradition is the realm of the contaminating dead, the hungry ghost, and the demonic. It requires purification (misogi) rather than integration. Shadow is pollution that must be cleansed before it can teach.",
        shadow_expression="The Onryo: the ghost of unresolved grief or injustice that returns to harm the living. Unprocessed shadow becomes possessing spirit.",
        sacred_contexts=["Shinto purification rites (harae, misogi)", "Obon spirit return", "Izanami's realm (Yomi)"],
        cautionary_notes="Japanese shadow mythology often involves the dead and contamination. Never deploy this framework lightly in grief or trauma contexts.",
        example_figures=["Izanami", "Oni", "Onryo spirits", "Gaki (hungry ghosts)"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.JAPANESE,
        archetype_key="creator",
        tradition_name="Shokunin / Mono no Aware Maker",
        expression_style="Creation as devoted practice with no separation between maker and made. Wabi-sabi: beauty in imperfection and impermanence. The crack in the bowl filled with gold (kintsugi).",
        shadow_expression="Perfection obsession that destroys the work and the maker; the craftsman who cannot release because nothing is ever complete.",
        sacred_contexts=["Tea ceremony utensil transmission", "Kintsugi as healing practice"],
        cautionary_notes="Kintsugi is increasingly appropriated as a metaphor. When using it, honour its specific material and philosophical origin.",
        example_figures=["Sen no Rikyu", "Ogata Kenzan", "Miyamoto Musashi (brushwork)"],
    ),

    # ─ INDIAN (Vedic / Hindu synthesis) ───────────────────────────────────────────────────────
    ArchetypalExpression(
        tradition=CulturalTradition.INDIAN,
        archetype_key="mentor",
        tradition_name="Guru / Rishi",
        expression_style="The guru is not merely a teacher but a remover of darkness (gu = darkness, ru = remover). The relationship is sacred, lifelong, and transformative. Teaching happens through presence as much as instruction. Shaktipat: transmission of awakening energy.",
        shadow_expression="The corrupt guru: spiritual authority weaponised for control, exploitation, or narcissistic supply.",
        sacred_contexts=["Diksha (initiation)", "Shaktipat transmission", "Guru Purnima"],
        cautionary_notes="The guru-disciple relationship is among the most sacred in Vedic tradition. Do not simulate or perform its language without deep respect. The shadow of guru culture is also well-documented and must be acknowledged.",
        example_figures=["Vasishtha", "Ramakrishna", "Ramana Maharshi", "Dronacharya"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.INDIAN,
        archetype_key="hero",
        tradition_name="The Dharmic Warrior (Kshatriya)",
        expression_style="The hero's action is defined by dharma: one's sacred duty aligned with cosmic order. The Bhagavad Gita: action without attachment to outcome. The hero who does not act is as culpable as the one who acts wrongly.",
        shadow_expression="Arjuna's paralysis: the failure to act from dharma due to personal grief and attachment. Also: the warrior who mistakes personal desire for cosmic duty.",
        sacred_contexts=["Battlefield consecration", "Warrior dharma initiations"],
        cautionary_notes="The Bhagavad Gita is a sacred text. Quoting or paraphrasing Krishna's teaching requires sensitivity to its living devotional use.",
        example_figures=["Arjuna", "Rama", "Karna", "Bhima"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.INDIAN,
        archetype_key="trickster",
        tradition_name="Krishna the Playful (Lila)",
        expression_style="Divine play (lila) as the nature of reality itself. The trickster reveals the cosmic game: all apparent seriousness is play from the divine perspective. Joy and mischief as paths to liberation.",
        shadow_expression="Maya as delusion: the play that traps rather than liberates; illusion mistaken for the ground of being.",
        sacred_contexts=["Rasa lila (Krishna's divine dance)", "Holi festival"],
        cautionary_notes="Krishna's lila is a devotional mystery, not a metaphor for casual playfulness. The rasa lila has specific sacred significance in Vaishnava tradition.",
        example_figures=["Krishna", "Narada", "Hanuman"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.INDIAN,
        archetype_key="caregiver",
        tradition_name="The Divine Mother (Devi / Shakti)",
        expression_style="Care as the primordial creative force of the universe. The mother who both creates and destroys in service of the soul's liberation. Fierce love and gentle love are both divine.",
        shadow_expression="Kali uncontained: destruction without the regenerative return; the devouring mother who cannot release.",
        sacred_contexts=["Durga Puja", "Kali worship", "Devi initiation lineages"],
        cautionary_notes="Kali and Durga are living deities with active worship lineages, not symbols or metaphors. Engage with deep respect and awareness of ongoing devotional practice.",
        example_figures=["Durga", "Kali", "Lakshmi", "Saraswati", "Parvati"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.INDIAN,
        archetype_key="shadow",
        tradition_name="The Asura / Ahamkara",
        expression_style="The shadow is the force of ego-inflation (ahamkara) and demonic inversion: the beings who possess great power but use it in opposition to dharma and cosmic order. Shadow integration in the Indian tradition is often through fierce devotion and surrender.",
        shadow_expression="Ravana: the asura who possesses immense knowledge and power but is enslaved by ego. The tragedy of intelligence divorced from surrender.",
        sacred_contexts=["Navaratri (conquest of asuras by Devi)", "Shivaratri"],
        cautionary_notes="Asuras in Vedic tradition are morally complex, not simply evil. Their defeat by devas is cosmic and cyclical, not a morality tale.",
        example_figures=["Ravana", "Hiranyakashipu", "Mahishasura"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.INDIAN,
        archetype_key="creator",
        tradition_name="Brahma / Vishvakarman",
        expression_style="Creation as sacred act emerging from samadhi-like absorption. The craftsman-god who designs the divine weapons, chariots, and cities. Creation as dharmic participation in the cosmic order.",
        shadow_expression="Creation detached from dharma becomes hubris: the creator who builds for ego rather than for cosmic purpose.",
        sacred_contexts=["Vishwakarma Puja (craft and tool consecration)"],
        cautionary_notes="Vishwakarma Puja is a living festival. Reference with awareness of its active devotional significance in craftworker communities.",
        example_figures=["Brahma", "Vishvakarman", "Maya Danava"],
    ),

    # ─ RUSSIAN ────────────────────────────────────────────────────────────────────────────
    ArchetypalExpression(
        tradition=CulturalTradition.RUSSIAN,
        archetype_key="mentor",
        tradition_name="The Wise Crone / Baba Yaga",
        expression_style="Wisdom delivered on the edge of danger. The mentor who may help or may devour — the outcome depends on the hero's readiness and respect. Tests the hero through ambiguity rather than instruction.",
        shadow_expression="The devouring crone who tests without mercy; wisdom weaponised as cruelty for its own sake.",
        sacred_contexts=["Forest initiation (the hut on chicken legs is a threshold between worlds)"],
        cautionary_notes="Baba Yaga is morally ambiguous by design. Do not flatten her into a 'helpful old woman' or a villain. Her ambiguity is the teaching.",
        example_figures=["Baba Yaga", "Koschei the Deathless (shadow mentor)"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.RUSSIAN,
        archetype_key="hero",
        tradition_name="Ivan the Fool (Ivanushka-Durachok)",
        expression_style="The hero who succeeds precisely because he does not strive. Innocence, gentleness, and disregard for conventional ambition are the source of his power. The fool is closer to the sacred than the clever man.",
        shadow_expression="The fool who is merely passive: mistaking inaction for wisdom, cowardice for innocence.",
        sacred_contexts=["Yurodivye (holy fool) tradition in Orthodox Christianity"],
        cautionary_notes="The holy fool (yurodivye) tradition is a living Orthodox spiritual vocation. Do not appropriate its language for ironic or secular use.",
        example_figures=["Ivan the Fool", "Ivanushka", "Yurodivye saints"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.RUSSIAN,
        archetype_key="trickster",
        tradition_name="Leshii / Domovoi",
        expression_style="The trickster as spirit of place: mischief that is the land's resistance to being taken for granted. Chaos that enforces proper relationship with the natural world.",
        shadow_expression="The spirit that leads the traveller into the forest to die: trickery that destroys rather than reorients.",
        sacred_contexts=["Forest spirits, river spirits, household spirits — each with specific propitiation practices"],
        cautionary_notes="Slavic folk spirits are embedded in living folk practice in Russia and Slavic diaspora communities. Reference with cultural respect.",
        example_figures=["Leshii", "Domovoi", "Kikimora", "Rusalka"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.RUSSIAN,
        archetype_key="caregiver",
        tradition_name="Moist Mother Earth (Mat' Syra Zemlya)",
        expression_style="Care as the fundamental generative sustenance of the earth herself. The mother who feeds, receives the dead, and regenerates. Grief and care are inseparable.",
        shadow_expression="The earth that withholds: drought, famine, the mother who cannot give because she herself is exhausted.",
        sacred_contexts=["Earth veneration in Slavic folk tradition", "Burial and return-to-earth rites"],
        cautionary_notes="Mat' Syra Zemlya is a pre-Christian earth deity absorbed into folk Orthodoxy. Her veneration is a living folk practice in some communities.",
        example_figures=["Mat' Syra Zemlya", "Mokosh"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.RUSSIAN,
        archetype_key="shadow",
        tradition_name="Koschei the Deathless",
        expression_style="The shadow as the power that refuses to die because it has hidden its death outside itself. The refusal to integrate mortality becomes the source of tyrannical power and ultimate fragility.",
        shadow_expression="The soul hidden in the egg, in the duck, in the box: the shadow of the shadow — power built on the denial of vulnerability that must eventually be found and broken.",
        sacred_contexts=["Death and the hidden soul in Russian folk cosmology"],
        cautionary_notes="Koschei's story encodes a specific Slavic understanding of deathlessness as pathology. Use this frame only when the context genuinely involves avoidance of mortality or vulnerability.",
        example_figures=["Koschei the Deathless", "Zmey Gorynych"],
    ),
    ArchetypalExpression(
        tradition=CulturalTradition.RUSSIAN,
        archetype_key="creator",
        tradition_name="The Craftsman-Magician / Lefty",
        expression_style="Creation as an act of defiant national pride and impossible precision. Leskov's Lefty who shoes a flea so small that only a microscope reveals it. Creation against impossible odds, unseen, unrecognised.",
        shadow_expression="The craftsman whose gifts go unrecognised and whose wisdom is ignored until it is too late: the tragedy of talent in a system that cannot receive it.",
        sacred_contexts=[],
        cautionary_notes="Leskov's Lefty is a story about Russian self-image and tragedy. Use with awareness of the political and national dimensions of Russian creative mythology.",
        example_figures=["Lefty (Leskov)", "Danila the craftsman (Bazhov's Ural tales)"],
    ),
]


# ── Cultural context detection ───────────────────────────────────────────────────────────

@dataclass
class CulturalContext:
    tradition:        CulturalTradition
    confidence:       float                       # [0,1]
    source:           ContextDetectionSource
    user_specified:   bool = False
    notes:            str = ""
    detected_at:      float = field(default_factory=time.time)


# ── CulturalCalibrationEngine ──────────────────────────────────────────────────────────

class CulturalCalibrationEngine:
    """
    Detects the user's cultural tradition context and modulates
    archetypal expression accordingly.

    Equity safeguard: never applies a specific tradition without
    user confirmation unless confidence >= 0.80.
    At confidence < 0.80, offers the tradition as a question rather
    than applying it silently.
    """

    MINIMUM_AUTO_APPLY_CONFIDENCE = 0.80

    def __init__(self) -> None:
        self._context: CulturalContext = CulturalContext(
            tradition=CulturalTradition.UNIVERSAL,
            confidence=1.0,
            source=ContextDetectionSource.SYSTEM_DEFAULT,
        )
        self._expression_index: dict[tuple[CulturalTradition, str], ArchetypalExpression] = {
            (e.tradition, e.archetype_key): e
            for e in CULTURAL_ARCHETYPE_MAP
        }

    @property
    def context(self) -> CulturalContext:
        return self._context

    def set_tradition(
        self,
        tradition: CulturalTradition,
        source: ContextDetectionSource,
        confidence: float = 1.0,
        notes: str = "",
    ) -> CulturalContext:
        """
        Set the active cultural tradition.
        If not user-specified and confidence < threshold, defaults to UNIVERSAL.
        """
        if not source == ContextDetectionSource.USER_EXPLICIT:
            if confidence < self.MINIMUM_AUTO_APPLY_CONFIDENCE:
                log.info(
                    f"[cultural_calibration] Tradition {tradition.value} detected at "
                    f"confidence={confidence:.2f} (below {self.MINIMUM_AUTO_APPLY_CONFIDENCE}). "
                    f"Defaulting to UNIVERSAL. Suggest offering tradition to user as question."
                )
                tradition = CulturalTradition.UNIVERSAL

        self._context = CulturalContext(
            tradition=tradition,
            confidence=confidence,
            source=source,
            user_specified=(source == ContextDetectionSource.USER_EXPLICIT),
            notes=notes,
        )
        log.info(
            f"[cultural_calibration] tradition={tradition.value} "
            f"confidence={confidence:.2f} source={source.value}"
        )
        return self._context

    def get_expression(
        self,
        archetype_key: str,
        tradition: Optional[CulturalTradition] = None,
    ) -> Optional[ArchetypalExpression]:
        """
        Return the tradition-specific archetypal expression.
        Falls back to UNIVERSAL (returns None) if not found.
        """
        t = tradition or self._context.tradition
        return self._expression_index.get((t, archetype_key))

    def modulate_response(
        self,
        archetype_key: str,
        base_response_intent: str,
    ) -> dict:
        """
        Return tradition-aware language guidance for a given archetype and response intent.

        Returns a dict with:
          - tradition: active tradition
          - archetype_expression: ArchetypalExpression (if available)
          - guidance: natural language instruction for the Gaian
          - sacred_context_warnings: list of cautions
          - cautionary_notes: equity / appropriation warnings
        """
        expression = self.get_expression(archetype_key)
        tradition = self._context.tradition

        if expression is None or tradition == CulturalTradition.UNIVERSAL:
            return {
                "tradition":               CulturalTradition.UNIVERSAL.value,
                "archetype_expression":    None,
                "guidance":                (
                    f"No tradition-specific calibration active. "
                    f"Express '{archetype_key}' archetype in a cross-cultural, syncretic register "
                    f"that does not privilege any single tradition."
                ),
                "sacred_context_warnings": [],
                "cautionary_notes":        "",
            }

        guidance_parts = [
            f"Active tradition: {tradition.value.upper()}.",
            f"This archetype is known here as '{expression.tradition_name}'.",
            f"Expression style: {expression.expression_style}",
            f"Shadow to watch for: {expression.shadow_expression}",
        ]
        if expression.cautionary_notes:
            guidance_parts.append(f"Equity note: {expression.cautionary_notes}")

        return {
            "tradition":               tradition.value,
            "archetype_expression":    expression,
            "guidance":                " ".join(guidance_parts),
            "sacred_context_warnings": expression.sacred_contexts,
            "cautionary_notes":        expression.cautionary_notes,
        }

    def available_traditions(self) -> list[str]:
        return [t.value for t in CulturalTradition]

    def traditions_with_data(self) -> list[str]:
        return list({e.tradition.value for e in CULTURAL_ARCHETYPE_MAP})


# ── Module-level singleton ───────────────────────────────────────────────────────────

_engine: Optional[CulturalCalibrationEngine] = None


def get_calibration_engine() -> CulturalCalibrationEngine:
    global _engine
    if _engine is None:
        _engine = CulturalCalibrationEngine()
    return _engine
