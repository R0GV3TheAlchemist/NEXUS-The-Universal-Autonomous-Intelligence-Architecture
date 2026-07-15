"""GAIANRegistry — the canonical GAIAN instance registry.

Canon References: C03 (Ontology Runtime Model)
Issue: boot phase tests — GAIANRegistry object has no attribute list_all

GAIANRegistry wraps the GAIARuntime entity store and exposes a clean,
test-friendly interface for boot phase inspection.  It does NOT own the
entities — GAIARuntime does.  GAIANRegistry is a read/query facade.

Usage::

    from core.ontology import GAIARuntime
    from core.ontology.registry import GAIANRegistry

    runtime = GAIARuntime()
    registry = GAIANRegistry(runtime)

    all_gaians = registry.list_all()      # List[dict]
    gaian = registry.get(gaian_id)        # dict | None
    count = registry.count()              # int
"""
from __future__ import annotations

from typing import List, Optional

from .entities import EntityType, GaianEntity
from .runtime import GAIARuntime


class GAIANRegistry:
    """Read-only facade over GAIARuntime for GAIAN entity inspection.

    All boot phase tests that call registry.list_all() pass through here.
    """

    def __init__(self, runtime: GAIARuntime) -> None:
        self._runtime = runtime

    # ------------------------------------------------------------------
    # Public API — used by boot phase tests and session bootstrap
    # ------------------------------------------------------------------

    def list_all(self) -> List[dict]:
        """Return all registered Gaian instances as plain dicts.

        Returns an empty list if no Gaians have been registered yet.
        This is the canonical method expected by all boot phase tests.
        """
        gaians = self._runtime.list_entities(entity_type=EntityType.GAIAN)
        return [self._gaian_to_dict(g) for g in gaians if isinstance(g, GaianEntity)]

    def get(self, gaian_id: str) -> Optional[dict]:
        """Return a single Gaian as a dict, or None if not found."""
        entity = self._runtime.get_entity(gaian_id)
        if entity is None or not isinstance(entity, GaianEntity):
            return None
        return self._gaian_to_dict(entity)

    def count(self) -> int:
        """Return the number of registered Gaian instances."""
        return len(self._runtime.list_entities(entity_type=EntityType.GAIAN))

    def is_registered(self, gaian_id: str) -> bool:
        """Return True if a Gaian with this ID exists in the runtime."""
        return self.get(gaian_id) is not None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _gaian_to_dict(gaian: GaianEntity) -> dict:
        """Serialise a GaianEntity to a plain dict for test assertions."""
        return {
            "id": gaian.id,
            "name": gaian.name,
            "type": gaian.type.value,
            "state": gaian.state.value,
            "permission_tier": gaian.permission_tier.value,
            "human_principal_id": gaian.human_principal_id,
            "session_id": gaian.session_id,
            "is_active": gaian.is_active,
            "is_suspended": gaian.is_suspended,
            "is_valid": gaian.is_valid(),
            "created_at": gaian.created_at.isoformat(),
            "updated_at": gaian.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<GAIANRegistry gaians={self.count()}>"
