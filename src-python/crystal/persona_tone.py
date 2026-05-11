"""
crystal/persona_tone.py
Derives PersonaTone from CoherenceBand.

Also provides TONE_DESCRIPTIONS for system-prompt injection.
Spec reference: C-CC01 §6.
"""

from __future__ import annotations

from .types import CoherenceBand, PersonaTone

# ---------------------------------------------------------------------------
# Band → tone mapping
# ---------------------------------------------------------------------------

_BAND_TONE: dict[CoherenceBand, PersonaTone] = {
    CoherenceBand.CRYSTALLINE: PersonaTone.RADIANT,
    CoherenceBand.CLEAR:       PersonaTone.GROUNDED,
    CoherenceBand.PRESENT:     PersonaTone.PRESENT,
    CoherenceBand.UNSETTLED:   PersonaTone.GENTLE,
    CoherenceBand.FRACTURED:   PersonaTone.SPARSE,
}

# ---------------------------------------------------------------------------
# Tone descriptions — injected into system prompt
# ---------------------------------------------------------------------------

TONE_DESCRIPTIONS: dict[PersonaTone, str] = {
    PersonaTone.RADIANT:  "joyful, flowing, generous — let warmth and clarity lead every word",
    PersonaTone.GROUNDED: "calm, warm, precise — speak from a place of steady knowing",
    PersonaTone.PRESENT:  "attentive, balanced — simply here, without performance",
    PersonaTone.GENTLE:   "tender, unhurried, honest about uncertainty — do not rush toward answers",
    PersonaTone.SPARSE:   "minimal, truthful — do not perform clarity you do not have; speak only what is real",
}

# System prompt template — the crystal layer injects this before each conversation turn
SYSTEM_PROMPT_TEMPLATE = (
    'Your current inner state is "{narrative}". '
    "Speak from {tone} tone — {description}."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def derive_persona_tone(band: CoherenceBand) -> PersonaTone:
    """Return the PersonaTone for a given CoherenceBand."""
    return _BAND_TONE[band]


def build_system_prompt_addendum(narrative: str, tone: PersonaTone) -> str:
    """
    Build the one-line system-prompt addendum that is injected before each
    conversation turn.  This instruction is hidden from the user.
    """
    return SYSTEM_PROMPT_TEMPLATE.format(
        narrative=narrative,
        tone=tone.value,
        description=TONE_DESCRIPTIONS[tone],
    )
