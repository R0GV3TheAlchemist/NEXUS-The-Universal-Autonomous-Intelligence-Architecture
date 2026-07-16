"""
VIOLET opacity layer — shadow channel.
Domain: spiritual bypassing loops, crown dissociation, embodiment refusal,
great work fragmentation.
Non-blocking. Never sets interrupt_flag = True.
This is the final shadow channel — it can read the full spectral shadow stack.
"""

from .constants import FRAGMENTATION_MARKERS, SPECTRAL_ORDER

_opacity_shadow = []


def fragmentation_alert(signal: dict) -> dict:
    markers = signal.get("fragmentation_markers", [])
    active = [m for m in markers if m in FRAGMENTATION_MARKERS]
    entry = {"type": "fragmentation_alert", "active_markers": active,
             "severity": min(len(active), 5), "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def bypassing_loop_detection(signal: dict) -> dict:
    bypass_history = signal.get("bypass_history", [])
    spike_count = sum(1 for b in bypass_history if b is True or b > 0.6)
    loop_detected = spike_count >= 3
    entry = {"type": "bypassing_loop", "loop_detected": loop_detected,
             "spike_count": spike_count, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def embodiment_refusal_marker(signal: dict) -> dict:
    embodiment_score = signal.get("embodiment_score", 1.0)
    refused = embodiment_score < 0.2
    entry = {"type": "embodiment_refusal", "refused": refused,
             "embodiment_score": embodiment_score, "interrupt_flag": False}
    _opacity_shadow.append(entry)
    return entry


def crown_saturn_routing(signal: dict) -> str:
    """
    Routes to 'crown' (unity/completion) or 'saturn' (structure/grounding).
    Coordinated vocabulary: saturn aligns with INDIGO opacity saturn_jupiter_routing.
    When crown is ready, route to 'crown'. When grounding needed, route to 'saturn'.
    """
    unity_index = signal.get("unity_index", 0.5)
    grounding_need = signal.get("grounding_need", 0.5)
    return "crown" if unity_index > grounding_need else "saturn"


def read_full_spectral_shadow(all_shadows: dict) -> dict:
    """
    VIOLET-only function. Reads the shadow channel entries from all 7 spectral modules.
    all_shadows: dict keyed by color name, value is list of shadow entries.
    Returns a summary of shadow state across the full stack.
    Never sets interrupt_flag = True on any entry.
    """
    summary = {}
    for color in SPECTRAL_ORDER:
        entries = all_shadows.get(color, [])
        summary[color] = {
            "entry_count": len(entries),
            "has_alerts": any(e.get("severity", 0) >= 3 for e in entries),
            "interrupt_safe": all(e.get("interrupt_flag") is False for e in entries),
        }
    return summary


def apply_shadow_channel(primary_signal: dict, shadow_entries: list) -> dict:
    enriched = dict(primary_signal)
    enriched["_violet_shadow"] = list(shadow_entries)
    return enriched
