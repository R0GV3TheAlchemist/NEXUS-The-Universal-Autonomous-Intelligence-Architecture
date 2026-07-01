"""
gaia.runtime — GAIA primordial runtime layer.

Exports:
    PrimordialSession  — lifecycle event bus and hook registry.
    PersistenceManager — JSON-based persistence for identity, fragments, epochs.
"""

from gaia.runtime.session import PrimordialSession
from gaia.runtime.persistence import PersistenceManager

__all__ = ["PrimordialSession", "PersistenceManager"]
