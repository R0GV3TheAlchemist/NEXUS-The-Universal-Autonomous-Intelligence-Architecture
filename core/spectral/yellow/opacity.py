"""
YELLOW opacity layer — shadow channel.
Domain: ego inflation loops, shame spirals, will suppression.
Non-blocking. Never sets interrupt_flag = True.
"""

from .constants import INFLATION_MARKERS

_opacity_shadow = []


def inflation_alert(signal: dict) -> dict:
    markers = signal.get("inflation_markers", [])
    active = [m for m in markers if m in INFLATION_MARKERS]
    entry = {"type": "inflation_alert", "active_markers": active,
             "severity": min(len(active), 5), "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def shame_spiral_detection(signal: dict) -> dict:
    shame_history = signal.get("shame_history", [])
    spike_count = sum(1 for s in shame_history if s > 0.65)
    spiral_detected = spike_count >= 3
    entry = {"type": "shame_spiral", "spiral_detected": spiral_detected,
             "spike_count": spike_count, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def will_suppression_marker(signal: dict) -> dict:
    will_strength = signal.get("will_strength", 1.0)
    suppressed = will_strength < 0.25
    entry = {"type": "will_suppression", "suppressed": suppressed,
             "will_strength": will_strength, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def sol_luna_routing(signal: dict) -> str:
    """
    Routes to 'sol' (active will/assertion) or 'luna' (receptive/reflective).
    Coordinated vocabulary with clarity.map_solar_archetype.
    """
    will_strength = signal.get("will_strength", 0.5)
    receptivity = signal.get("receptivity", 0.5)
    return "sol" if will_strength > receptivity else "luna"


def apply_shadow_channel(primary_signal: dict, shadow_entries: list) -> dict:
    enriched = dict(primary_signal)
    enriched["_yellow_shadow"] = list(shadow_entries)
    return enriched
