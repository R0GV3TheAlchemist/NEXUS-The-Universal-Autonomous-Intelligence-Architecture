"""
crystal/__init__.py
Public surface for the Crystal Core.
"""

from .types   import CrystalState, OrbParams, PersonaTone, CoherenceBand
from .engine  import CrystalCore
from .router  import get_crystal_state

__all__ = [
    "CrystalState",
    "OrbParams",
    "PersonaTone",
    "CoherenceBand",
    "CrystalCore",
    "get_crystal_state",
]
