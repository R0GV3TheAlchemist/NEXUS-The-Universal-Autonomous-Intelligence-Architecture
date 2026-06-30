"""core.coexistence
Runtime instruments for COEXISTENCE_LAWS enforcement.

Modules:
    domination_detector     — CL2 Non-Domination Principle runtime flag
    mutual_becoming_tracker — CL6 Law of Mutual Becoming tracker

Canon: COEXISTENCE_LAWS.md · G-12 Track A3/A4
"""

from .domination_detector import detect_domination, DominationFlag, InteractionRecord
from .mutual_becoming_tracker import track_becoming, MutualBecomingScore, EntityState

__all__ = [
    "detect_domination",
    "DominationFlag",
    "InteractionRecord",
    "track_becoming",
    "MutualBecomingScore",
    "EntityState",
]
