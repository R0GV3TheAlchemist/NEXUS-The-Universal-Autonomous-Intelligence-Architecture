"""
core/sentinel/constants.py
==========================
Single source of truth for all SENTINEL alert levels, thresholds,
hex colours, and metadata.

The five-level alert hierarchy:
  1  ADVISORY    — informational, no action required
  2  CAUTION     — elevated awareness, monitor closely
  3  WARNING     — action recommended, log and surface
  4  CRITICAL    — action required, may trigger interrupt
  5  EMERGENCY   — immediate interrupt + Constitutional escalation

© 2024-2026 R0GV3 The Alchemist — GAIA Project. All rights reserved.
AGPL-3.0 Licensed. Unauthorised derivative works are prohibited.
"""

from enum import IntEnum


class AlertLevel(IntEnum):
    ADVISORY   = 1
    CAUTION    = 2
    WARNING    = 3
    CRITICAL   = 4
    EMERGENCY  = 5


# ---------------------------------------------------------------------------
# Human-readable labels
# ---------------------------------------------------------------------------

ALERT_LEVEL_LABEL: dict[AlertLevel, str] = {
    AlertLevel.ADVISORY:  "ADVISORY",
    AlertLevel.CAUTION:   "CAUTION",
    AlertLevel.WARNING:   "WARNING",
    AlertLevel.CRITICAL:  "CRITICAL",
    AlertLevel.EMERGENCY: "EMERGENCY",
}

# ---------------------------------------------------------------------------
# Hex colour per level (UI / spectral display)
# ---------------------------------------------------------------------------

ALERT_LEVEL_HEX: dict[AlertLevel, str] = {
    AlertLevel.ADVISORY:  "#5B8DB8",  # calm blue — informational
    AlertLevel.CAUTION:   "#D4A017",  # amber — heightened awareness
    AlertLevel.WARNING:   "#E07B39",  # orange — action recommended
    AlertLevel.CRITICAL:  "#DC2626",  # red — action required
    AlertLevel.EMERGENCY: "#CC2200",  # deep crimson — full interrupt
}

# ---------------------------------------------------------------------------
# Threshold rules
# ---------------------------------------------------------------------------

# Minimum level at which SENTINEL triggers an execution interrupt.
# Levels below this are logged and surfaced but do not halt execution.
INTERRUPT_THRESHOLD: AlertLevel = AlertLevel.CRITICAL

# Minimum level at which SENTINEL escalates to the Constitutional Layer.
# The Constitutional Layer has absolute veto authority over all outputs.
CONSTITUTIONAL_ESCALATION_THRESHOLD: AlertLevel = AlertLevel.EMERGENCY

# Maximum number of unresolved alerts before SENTINEL forces a WARNING
# elevation on all subsequent alerts regardless of their declared level.
UNRESOLVED_SATURATION_LIMIT: int = 50

# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

SENTINEL_VERSION: str = "1.0.0"
