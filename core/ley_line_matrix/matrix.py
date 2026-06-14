"""
Ley Line Matrix — Core Graph Engine

The LeyLineMatrix manages the full topology of nodes and lines,
handles pulse routing, tracks flow state, and exposes a snapshot API.

Backed by a weighted directed graph (networkx.DiGraph).
Bidirectional lines are stored as two directed edges.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    import networkx as nx
except ImportError:
    nx = None  # networkx is optional; matrix degrades gracefully

from .models import FlowType, LeyLine, LeyNode, LeyPulse

logger = logging.getLogger("gaia.ley_line_matrix")


class LeyLineMatrix:
    """
    The living graph of GAIA-OS Ley Lines.

    Key capabilities:
      - Register / deregister LeyNodes
      - Add / remove LeyLines between nodes
      - Route LeyPulses along shortest viable path
      - Track 'dark lines' (blocked/severed connections)
      - Expose topology snapshots for the visualizer
    """

    def __init__(self) -> None:
        self._nodes: dict[str, LeyNode] = {}
        self._lines: list[LeyLine] = []
        self._pulse_log: list[LeyPulse] = []
        self._graph = nx.DiGraph() if nx else None
        logger.info("LeyLineMatrix initialized.")

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def register_node(self, node: LeyNode) -> None:
        """Register a LeyNode into the matrix."""
        if node.name in self._nodes:
            logger.debug("Node '%s' already registered; skipping.", node.name)
            return
        self._nodes[node.name] = node
        if self._graph is not None:
            self._graph.add_node(node.name, node=node)
        logger.info("LeyNode registered: %s", node.name)

    def deregister_node(self, name: str) -> None:
        """Remove a LeyNode and all its connected lines."""
        if name not in self._nodes:
            return
        self._lines = [
            line for line in self._lines
            if line.source.name != name and line.target.name != name
        ]
        del self._nodes[name]
        if self._graph is not None:
            self._graph.remove_node(name)
        logger.info("LeyNode deregistered: %s", name)

    # ------------------------------------------------------------------
    # Line management
    # ------------------------------------------------------------------

    def add_line(self, line: LeyLine) -> None:
        """Add a LeyLine to the matrix."""
        # Auto-register nodes if not already present
        self.register_node(line.source)
        self.register_node(line.target)
        self._lines.append(line)
        weight = 1.0 - line.strength  # lower weight = stronger connection
        if self._graph is not None:
            self._graph.add_edge(
                line.source.name, line.target.name,
                weight=weight, line=line, flow_type=line.flow_type.value
            )
            if line.bidirectional:
                self._graph.add_edge(
                    line.target.name, line.source.name,
                    weight=weight, line=line, flow_type=line.flow_type.value
                )
        logger.debug("LeyLine added: %s", line.id)

    def block_line(self, source: str, target: str) -> None:
        """Mark a line as blocked (dark line)."""
        for line in self._lines:
            if line.source.name == source and line.target.name == target:
                line.blocked = True
                logger.warning("Dark line detected: %s -> %s", source, target)

    def unblock_line(self, source: str, target: str) -> None:
        """Restore a previously blocked line."""
        for line in self._lines:
            if line.source.name == source and line.target.name == target:
                line.blocked = False
                logger.info("Line restored: %s -> %s", source, target)

    # ------------------------------------------------------------------
    # Pulse routing
    # ------------------------------------------------------------------

    def emit(self, pulse: LeyPulse) -> bool:
        """
        Route a LeyPulse from origin to destination.

        Uses shortest-path routing (via networkx) over traversable lines.
        Quantum pulses use superposition routing (all viable paths).
        Returns True if the pulse was successfully routed.
        """
        if pulse.origin not in self._nodes:
            logger.warning("Pulse origin node not found: %s", pulse.origin)
            pulse.blocked = True
            self._pulse_log.append(pulse)
            return False

        if pulse.destination not in self._nodes:
            logger.warning("Pulse destination node not found: %s", pulse.destination)
            pulse.blocked = True
            self._pulse_log.append(pulse)
            return False

        if pulse.flow_type == FlowType.QUANTUM:
            return self._route_quantum(pulse)

        return self._route_standard(pulse)

    def _route_standard(self, pulse: LeyPulse) -> bool:
        """Route via shortest traversable path."""
        if self._graph is None:
            # Fallback: direct connection check
            return self._direct_route(pulse)

        # Build a subgraph excluding blocked lines
        active = nx.DiGraph()
        for u, v, data in self._graph.edges(data=True):
            line: LeyLine = data.get("line")
            if line and line.is_traversable():
                active.add_edge(u, v, **data)

        try:
            path = nx.shortest_path(active, pulse.origin, pulse.destination, weight="weight")
            pulse.routed = True
            pulse.metadata["path"] = path
            self._pulse_log.append(pulse)
            logger.debug(
                "Pulse routed [%s]: %s -> %s via %s",
                pulse.flow_type.value, pulse.origin, pulse.destination, path
            )
            return True
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pulse.blocked = True
            self._pulse_log.append(pulse)
            logger.warning(
                "No traversable path for pulse [%s]: %s -> %s",
                pulse.flow_type.value, pulse.origin, pulse.destination
            )
            return False

    def _route_quantum(self, pulse: LeyPulse) -> bool:
        """Quantum routing: pulse travels all viable simple paths simultaneously."""
        if self._graph is None:
            return self._direct_route(pulse)

        active = nx.DiGraph()
        for u, v, data in self._graph.edges(data=True):
            line: LeyLine = data.get("line")
            if line and line.is_traversable():
                active.add_edge(u, v, **data)

        try:
            paths = list(nx.all_simple_paths(active, pulse.origin, pulse.destination))
            if not paths:
                pulse.blocked = True
                self._pulse_log.append(pulse)
                return False
            pulse.routed = True
            pulse.metadata["quantum_paths"] = paths
            self._pulse_log.append(pulse)
            logger.debug(
                "Quantum pulse superposed across %d paths: %s -> %s",
                len(paths), pulse.origin, pulse.destination
            )
            return True
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pulse.blocked = True
            self._pulse_log.append(pulse)
            return False

    def _direct_route(self, pulse: LeyPulse) -> bool:
        """Fallback direct-connection check when networkx is unavailable."""
        for line in self._lines:
            if (
                line.source.name == pulse.origin
                and line.target.name == pulse.destination
                and line.is_traversable()
            ):
                pulse.routed = True
                pulse.metadata["path"] = [pulse.origin, pulse.destination]
                self._pulse_log.append(pulse)
                return True
        pulse.blocked = True
        self._pulse_log.append(pulse)
        return False

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot of the current matrix state."""
        dark_lines = [
            line.id for line in self._lines if line.blocked or not line.is_traversable()
        ]
        return {
            "nodes": [n for n in self._nodes],
            "lines": [line.id for line in self._lines],
            "dark_lines": dark_lines,
            "pulse_count": len(self._pulse_log),
            "routed": sum(1 for p in self._pulse_log if p.routed),
            "blocked": sum(1 for p in self._pulse_log if p.blocked),
        }

    def get_dark_lines(self) -> list[LeyLine]:
        """Return all lines that are currently blocked or severed."""
        return [line for line in self._lines if not line.is_traversable()]

    def pulse_log(self) -> list[LeyPulse]:
        """Return the full immutable pulse log."""
        return list(self._pulse_log)
