from __future__ import annotations

MASTER_NUMBERS: frozenset[int] = frozenset({11, 22, 33})

# Pythagorean letter-to-number mapping
LETTER_MAP: dict[str, int] = {
    "A": 1, "J": 1, "S": 1,
    "B": 2, "K": 2, "T": 2,
    "C": 3, "L": 3, "U": 3,
    "D": 4, "M": 4, "V": 4,
    "E": 5, "N": 5, "W": 5,
    "F": 6, "O": 6, "X": 6,
    "G": 7, "P": 7, "Y": 7,
    "H": 8, "Q": 8, "Z": 8,
    "I": 9, "R": 9,
}

VOWELS: frozenset[str] = frozenset("AEIOU")
# Y is treated as a vowel only when vowel_mode="y-as-vowel"
VOWELS_Y: frozenset[str] = frozenset("AEIOUY")

TRAITS: dict[int, dict] = {
    1:  {
        "keywords": ["leadership", "independence", "originality", "ambition"],
        "shadow": ["ego", "stubbornness", "isolation"],
        "summary": "The Initiator — driven to forge new paths alone.",
    },
    2:  {
        "keywords": ["cooperation", "sensitivity", "diplomacy", "patience"],
        "shadow": ["codependency", "indecision", "oversensitivity"],
        "summary": "The Mediator — seeks harmony and partnership.",
    },
    3:  {
        "keywords": ["creativity", "self-expression", "joy", "communication"],
        "shadow": ["scattered energy", "superficiality", "self-doubt"],
        "summary": "The Creator — channels life through art and words.",
    },
    4:  {
        "keywords": ["structure", "discipline", "reliability", "practicality"],
        "shadow": ["rigidity", "repression", "workaholic tendencies"],
        "summary": "The Builder — establishes order from chaos.",
    },
    5:  {
        "keywords": ["freedom", "adventure", "adaptability", "curiosity"],
        "shadow": ["restlessness", "irresponsibility", "overindulgence"],
        "summary": "The Explorer — thrives in change and variety.",
    },
    6:  {
        "keywords": ["nurturing", "responsibility", "community", "healing"],
        "shadow": ["martyrdom", "control", "perfectionism"],
        "summary": "The Caregiver — devoted to home, family, and service.",
    },
    7:  {
        "keywords": ["introspection", "wisdom", "mysticism", "analysis"],
        "shadow": ["isolation", "distrust", "cynicism"],
        "summary": "The Seeker — drawn inward toward truth and spirit.",
    },
    8:  {
        "keywords": ["power", "abundance", "authority", "manifestation"],
        "shadow": ["greed", "control", "materialism"],
        "summary": "The Manifestor — masters the material world.",
    },
    9:  {
        "keywords": ["compassion", "completion", "humanitarianism", "wisdom"],
        "shadow": ["bitterness", "possessiveness", "martyrdom"],
        "summary": "The Sage — carries the wisdom of all previous numbers.",
    },
    11: {
        "keywords": ["vision", "intuition", "illumination", "spiritual messenger"],
        "shadow": ["anxiety", "hypersensitivity", "impracticality"],
        "summary": "The Visionary — a master channel for higher truths.",
    },
    22: {
        "keywords": ["master builder", "large-scale vision", "pragmatic idealism", "legacy"],
        "shadow": ["overwhelm", "self-doubt", "destructive ambition"],
        "summary": "The Architect — turns grand dreams into lasting structures.",
    },
    33: {
        "keywords": ["master teacher", "unconditional love", "selfless service", "cosmic healing"],
        "shadow": ["self-sacrifice", "martyrdom", "unrealistic ideals"],
        "summary": "The Master Healer — embodies love as a living principle.",
    },
}
