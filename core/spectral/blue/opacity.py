"""
BLUE opacity layer — shadow channel.
Domain: voice suppression loops, perception distortion, truth avoidance.
Non-blocking. Never sets interrupt_flag = True.
"""

from .constants import SILENCE_MARKERS

_opacity_shadow = []


def silence_alert(signal: dict) -> dict:
    markers = signal.get("silence_markers", [])
    active = [m for m in markers if m in SILENCE_MARKERS]
    entry = {"type": "silence_alert", "active_markers": active,
             "severity": min(len(active), 5), "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def distortion_loop_detection(signal: dict) -> dict:
    distortion_history = signal.get("distortion_history", [])
    spike_count = sum(1 for d in distortion_history if d > 0.6)
    loop_detected = spike_count >= 3
    entry = {"type": "distortion_loop", "loop_detected": loop_detected,
             "spike_count": spike_count, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def perception_fog_marker(signal: dict) -> dict:
    fog = signal.get("perception_fog", 0.0)
    fogged = fog > 0.5
    entry = {"type": "perception_fog", "fogged": fogged,
             "fog_level": fog, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def jupiter_mercury_routing(signal: dict) -> str:
    """
    Routes to 'jupiter' (expansion/vision) or 'mercury' (precision/communication).
    Coordinated vocabulary: mercury aligns with GREEN opacity mercury_venus_routing.
    """
    vision_index = signal.get("vision_index", 0.5)
    precision_index = signal.get("precision_index", 0.5)
    return "jupiter" if vision_index > precision_index else "mercury"


def apply_shadow_channel(primary_signal: dict, shadow_entries: list) -> dict:
    enriched = dict(primary_signal)
    enriched["_blue_shadow"] = list(shadow_entries)
    return enriched
