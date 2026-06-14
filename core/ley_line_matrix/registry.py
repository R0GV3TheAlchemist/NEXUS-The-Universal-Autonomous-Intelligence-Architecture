"""
Ley Line Matrix — Node Registry

Provides:
  - register_node():  Programmatically register a LeyNode into the global matrix
  - @ley_node:        Class/function decorator for zero-coupling auto-registration

Design goal: existing engines (noosphere, soul_layer, etc.) can opt-in
to the matrix with a single decorator — no imports of matrix internals needed.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

from .models import FlowType, LeyNode

logger = logging.getLogger("gaia.ley_line_matrix.registry")

F = TypeVar("F")


def register_node(
    name: str,
    module_path: str,
    description: str = "",
    metadata: dict[str, Any] | None = None,
) -> LeyNode:
    """
    Register a LeyNode into the global matrix singleton.

    Returns the created LeyNode for further line wiring if needed.
    """
    from . import get_matrix  # deferred to avoid circular import

    node = LeyNode(
        name=name,
        module_path=module_path,
        description=description,
        metadata=metadata or {},
    )
    get_matrix().register_node(node)
    return node


def ley_node(
    name: str | None = None,
    flow_types: list[FlowType] | None = None,
    description: str = "",
) -> Callable[[F], F]:
    """
    Decorator that registers the decorated class or function as a LeyNode
    in the global matrix at import time.

    Usage:
        @ley_node(name="noosphere", flow_types=[FlowType.CONSCIOUSNESS])
        class Noosphere:
            ...
    """

    def decorator(obj: F) -> F:
        node_name = name or getattr(obj, "__name__", str(obj))
        module_path = getattr(obj, "__module__", "") + "." + node_name
        register_node(
            name=node_name,
            module_path=module_path,
            description=description,
            metadata={"flow_types": [ft.value for ft in (flow_types or [])]},
        )
        logger.info("@ley_node registered: %s", node_name)
        return obj

    return decorator
