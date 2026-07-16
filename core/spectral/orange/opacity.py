"""
ORANGE opacity layer — shadow channel.
Domain: compulsive creativity, martyrdom loops,
persistent sacral wounding, passive boundary erosion.
Non-blocking. Never sets interrupt_flag = True.
"""

from .constants import DISSOLUTION_MARKERS, CALCINATION_MARKERS

_opacity_shadow = []


def calcination_alert(signal: dict) -> dict:
    """
    Fires a shadow-channel alert when calcination markers are detected.
    Appends to shadow log; never mutates primary signal.
    """
    markers = signal.get("calcination_markers", [])
    active = [m for m in markers if m in CALCINATION_MARKERS]
    entry = {
        "type": "calcination_alert",
        "active_markers": active,
        "severity": min(len(active), 5),
        "interrupt_flag": False,
    }
    _opacity_shadow.append(entry)
    return entry


def martyrdom_loop_detection(signal: dict) -> dict:
    """
    Detects persistent martyrdom loop patterns in the shadow channel.
    """
    guilt_history = signal.get("guilt_history", [])
    loop_count = sum(1 for g in guilt_history if g > 0.6)
    loop_detected = loop_count >= 3

    entry = {
        "type": "martyrdom_loop",
        "loop_detected": loop_detected,
        "loop_count": loop_count,
        "interrupt_flag": False,
    }
    _opacity_shadow.append(entry)
    return entry


def sacral_depletion_marker(signal: dict) -> dict:
    """
    Marks sacral depletion events in the shadow channel.
    """
    vitality = signal.get("vitality", 1.0)
    depletion_flag = vitality < 0.25

    entry = {
        "type": "sacral_depletion",
        "depletion_flag": depletion_flag,
        "vitality": vitality,
        "interrupt_flag": False,
    }
    _opacity_shadow.append(entry)
    return entry


def venus_aphrodite_routing(signal: dict) -> str:
    """
    Routes signal to venus (receptive/healing) or aphrodite (expressive/desire) channel.
    Coordinated vocabulary with clarity.map_creative_archetype.
    """
    desire_index = signal.get("desire_index", 0.5)
    receptivity = signal.get("receptivity", 0.5)

    if desire_index > receptivity:
        return "aphrodite"
    return "venus"


def apply_shadow_channel(primary_signal: dict, shadow_entries: list) -> dict:
    """
    Appends shadow channel data to a copy of primary_signal.
    Primary signal is NEVER mutated.
    Returns enriched copy.
    """
    enriched = dict(primary_signal)
    enriched["_orange_shadow"] = list(shadow_entries)
    return enriched
