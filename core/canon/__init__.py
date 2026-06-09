"""
core/canon
==========
Canon contract types: CanonEntry, CanonValidator, RegisterSignal.

Import surface
--------------
  from core.canon import CanonEntry, CanonValidator, RegisterSignal
  from core.canon import CanonEntryError, CanonConflictError, ValidationResult
"""
from core.canon.canon_entry import (
    CanonEntry,
    CanonEntryError,
    RegisterSignal,
)
from core.canon.canon_validator import (
    CanonConflictError,
    CanonValidator,
    ValidationResult,
)

__all__ = [
    "CanonConflictError",
    "CanonEntry",
    "CanonEntryError",
    "CanonValidator",
    "RegisterSignal",
    "ValidationResult",
]
