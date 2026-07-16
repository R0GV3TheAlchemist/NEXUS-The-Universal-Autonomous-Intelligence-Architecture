"""
core/identity/gaian/__init__.py

Public surface for GAIA's Gaian substrate layer.

The Gaian substrate defines *what an agent can do* — its capabilities,
roles, and the charter rules that bind its behaviour.  It is the
complementary layer to the Avatar (which defines how an agent expresses
itself) and to Auth (which proves who it is).

Three primitives:
  GaianNode    — a single capability-bearing agent node
  GaianLattice — a DAG of nodes with inheritance traversal
  GaianCharter — the sovereign rule set that governs all nodes

Usage:
    from core.identity.gaian import GaianNode, GaianLattice, GaianCharter

Canon Refs: C01 (Sovereignty), C03 (Capability), C08 (Hierarchy), C15 (Consent)
"""

from .gaian_node import GaianNode, NodeRole, Capability
from .gaian_lattice import GaianLattice, LatticeEdge
from .gaian_charter import GaianCharter, CharterRule, RuleVerdict

__all__ = [
    "GaianNode",
    "NodeRole",
    "Capability",
    "GaianLattice",
    "LatticeEdge",
    "GaianCharter",
    "CharterRule",
    "RuleVerdict",
]
