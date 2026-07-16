"""
YELLOW clarity layer — depth-readable signals.
Domain: ego inflation vs. healthy will, shame collapse,
power dynamics, solar plexus integration.
"""

from .constants import SOLAR_ARCHETYPES, SEPARATION_MARKERS, INFLATION_MARKERS


def distinguish_will_ego(signal: dict) -> str:
    """
    Distinguishes authentic will from ego-driven control.
    Returns: 'authentic_will' | 'ego_control' | 'will_collapse' | 'integrated'
    """
    will_strength = signal.get("will_strength", 0.5)
    ego_clarity = signal.get("ego_clarity", 0.5)
    control_compulsion = signal.get("control_compulsion", 0.0)

    if control_compulsion > 0.7:
        return "ego_control"
    if will_strength < 0.2:
        return "will_collapse"
    if will_strength > 0.7 and ego_clarity > 0.7:
        return "authentic_will"
    return "integrated"


def detect_inflation_pattern(signal: dict) -> dict:
    markers = signal.get("inflation_markers", [])
    active = [m for m in markers if m in INFLATION_MARKERS]
    depth = signal.get("inflation_depth", 0.0)
    return {
        "inflation_present": len(active) > 0 or depth > 0.5,
        "active_markers": active,
        "depth": depth,
        "intervention_suggested": depth > 0.7,
    }


def classify_yellow_fire(signal: dict) -> str:
    separation_flag = signal.get("separation_flag", False)
    inflation_depth = signal.get("inflation_depth", 0.0)
    will_strength = signal.get("will_strength", 0.5)

    if separation_flag:
        return "separation"
    if inflation_depth > 0.6:
        return "inflation"
    if will_strength >= 0.75:
        return "solar_ignition"
    return "neutral"


def assess_power_health(signal: dict) -> dict:
    will_strength = signal.get("will_strength", 0.5)
    control_compulsion = signal.get("control_compulsion", 0.0)
    shame_index = signal.get("shame_index", 0.0)

    if will_strength > 0.75 and control_compulsion < 0.3 and shame_index < 0.3:
        status = "healthy"
    elif shame_index > 0.65:
        status = "shame_collapsed"
    elif control_compulsion > 0.65:
        status = "controlling"
    else:
        status = "developing"

    return {"status": status, "will_strength": will_strength, "shame_index": shame_index}


def map_solar_archetype(signal: dict) -> str:
    will_strength = signal.get("will_strength", 0.5)
    control_compulsion = signal.get("control_compulsion", 0.0)
    shame_index = signal.get("shame_index", 0.0)
    ego_clarity = signal.get("ego_clarity", 0.5)

    if will_strength >= 0.85 and ego_clarity >= 0.8:
        return "sovereign"
    if control_compulsion >= 0.7:
        return "tyrant"
    if shame_index >= 0.7:
        return "doormat"
    if will_strength >= 0.6:
        return "warrior_of_will"
    return "radiant_self"
