"""
core/integration_engine.py

Formerly: synergy_engine.py

Orchestrates the integration of all GAIAN core modules into a unified
response pipeline. The integration engine is the final assembly point
before the GAIAN's response is dispatched — it combines signals from
all twelve core modules into a coherent, contextually appropriate output.

See also: C00 Foundational Cosmology — integration_engine naming.
"""

from core.synergy_engine import *  # noqa: F403
from core.synergy_engine import SynergyEngine as IntegrationEngine

__all__ = ["IntegrationEngine"]
