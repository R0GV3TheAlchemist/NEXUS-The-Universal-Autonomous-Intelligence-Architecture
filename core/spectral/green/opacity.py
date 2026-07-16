"""
GREEN opacity layer — shadow channel.
Domain: heart armoring, compassion fatigue, grief freeze, codependency loops.
Non-blocking. Never sets interrupt_flag = True.
"""

from .constants import GRIEF_MARKERS

_opacity_shadow = []


def grief_freeze_alert(signal: dict) -> dict:
    markers = signal.get("grief_markers", [])
    active = [m for m in markers if m in GRIEF_MARKERS]
    entry = {"type": "grief_freeze_alert", "active_markers": active,
             "severity": min(len(active), 5), "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def compassion_fatigue_detection(signal: dict) -> dict:
    fatigue_history = signal.get("fatigue_history", [])
    spike_count = sum(1 for f in fatigue_history if f > 0.65)
    fatigue_detected = spike_count >= 3
    entry = {"type": "compassion_fatigue", "fatigue_detected": fatigue_detected,
             "spike_count": spike_count, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def heart_armoring_marker(signal: dict) -> dict:
    coherence = signal.get("coherence", 1.0)
    armored = coherence < 0.25
    entry = {"type": "heart_armoring", "armored": armored,
             "coherence": coherence, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def mercury_venus_routing(signal: dict) -> str:
    """
    Routes to 'mercury' (communication/bridge) or 'venus' (receptive/love).
    Coordinated vocabulary: venus aligns with ORANGE opacity venus_aphrodite_routing.
    """
    bridge_stability = signal.get("bridge_stability", 0.5)
    love_index = signal.get("love_index", 0.5)
    return "mercury" if bridge_stability > love_index else "venus"


def apply_shadow_channel(primary_signal: dict, shadow_entries: list) -> dict:
    enriched = dict(primary_signal)
    enriched["_green_shadow"] = list(shadow_entries)
    return enriched
