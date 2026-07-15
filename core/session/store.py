"""GAIA Session Store — module-level singleton dict.

All session state (including gaia.session.primordial) lives here.
Import SESSION_STORE from this module — never instantiate a new dict.

Usage::

    from core.session.store import SESSION_STORE

    SESSION_STORE["gaia.session.primordial"]   # always present after boot
    SESSION_STORE["my.custom.key"] = value
"""
from __future__ import annotations

from typing import Any, Dict

# Module-level singleton — always the same object; safe to import anywhere.
SESSION_STORE: Dict[str, Any] = {}
