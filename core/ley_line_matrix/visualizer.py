"""
Ley Line Matrix — Topology Visualizer

Exposes the matrix topology and live flow state as a JSON structure
suitable for the GAIA-OS /ui layer.

For rich visualization, pass the output to a frontend graph renderer
(e.g. D3.js force graph, Cytoscape.js, or the GAIA UI canvas).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("gaia.ley_line_matrix.visualizer")


def render_topology(matrix=None) -> dict[str, Any]:
    """
    Return a JSON-serializable graph topology of the current matrix.

    Output format:
      {
        "nodes": [{"id": str, "active": bool, "module_path": str}, ...],
        "edges": [{"source": str, "target": str, "flow_type": str,
                   "strength": float, "blocked": bool}, ...],
        "stats": {"pulse_count": int, "routed": int, "blocked": int,
                  "dark_lines": int}
      }
    """
    from . import get_matrix

    m = matrix or get_matrix()
    snapshot = m.snapshot()

    nodes = [
        {
            "id": node.name,
            "active": node.active,
            "module_path": node.module_path,
            "description": node.description,
        }
        for node in m._nodes.values()
    ]

    edges = [
        {
            "source": line.source.name,
            "target": line.target.name,
            "flow_type": line.flow_type.value,
            "strength": line.strength,
            "blocked": line.blocked,
            "bidirectional": line.bidirectional,
        }
        for line in m._lines
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "pulse_count": snapshot["pulse_count"],
            "routed": snapshot["routed"],
            "blocked": snapshot["blocked"],
            "dark_lines": len(snapshot["dark_lines"]),
        },
    }


def render_pulse_log(limit: int = 50, matrix=None) -> list[dict[str, Any]]:
    """
    Return the last `limit` pulse log entries as JSON-serializable dicts.
    """
    from . import get_matrix

    m = matrix or get_matrix()
    log = m.pulse_log()[-limit:]
    return [
        {
            "pulse_id": p.pulse_id,
            "origin": p.origin,
            "destination": p.destination,
            "flow_type": p.flow_type.value,
            "frequency_hz": p.frequency_hz,
            "routed": p.routed,
            "blocked": p.blocked,
            "timestamp": p.timestamp.isoformat(),
            "path": p.metadata.get("path") or p.metadata.get("quantum_paths"),
        }
        for p in log
    ]
