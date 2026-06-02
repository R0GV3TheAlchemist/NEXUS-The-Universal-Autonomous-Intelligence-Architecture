"""
core/task_graph.py -- GAIA TaskGraph, Sprint G-7 / Issue #170

Async-native DAG runner. Every node emits AsyncGAIATrace(TASK_NODE_EXEC).
See specs/architecture/GAIATRACE_SPEC.md for integration details.

Canon Refs: C01 (Sovereignty), C30 (No silent failures)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

try:
    from core.trace import AsyncGAIATrace, TraceEventType
    _TRACE_AVAILABLE = True
except ImportError:
    _TRACE_AVAILABLE = False


@dataclass
class EngineNode:
    engine_id:  str
    handler:    Callable[..., Coroutine[Any, Any, dict[str, Any]]]
    inputs:     list[str]      = field(default_factory=list)
    outputs:    list[str]      = field(default_factory=list)
    deps:       list[str]      = field(default_factory=list)
    timeout_ms: float          = 30_000.0
    canon_refs: list[str]      = field(default_factory=list)
    meta:       dict[str, Any] = field(default_factory=dict)


class TaskGraphError(Exception):
    """Raised for cycle detection, missing deps, or node timeout."""


class TaskGraph:
    """
    Async DAG runner. Nodes in the same topological wave run concurrently.
    Every _run_node() call is wrapped in AsyncGAIATrace(TASK_NODE_EXEC).
    """

    def __init__(self, gaian_id: str | None = None) -> None:
        self._nodes: dict[str, EngineNode] = {}
        self._gaian_id = gaian_id

    def add_node(self, node: EngineNode) -> "TaskGraph":
        if node.engine_id in self._nodes:
            raise TaskGraphError(f"Duplicate engine_id: '{node.engine_id}'")
        self._nodes[node.engine_id] = node
        return self

    def _resolve_order(self) -> list[list[str]]:
        """Kahn topological sort; raises TaskGraphError on cycle or missing dep."""
        for node in self._nodes.values():
            for dep in node.deps:
                if dep not in self._nodes:
                    raise TaskGraphError(
                        f"Node '{node.engine_id}' depends on missing node '{dep}'"
                    )
        in_degree: dict[str, int] = {nid: 0 for nid in self._nodes}
        for node in self._nodes.values():
            in_degree[node.engine_id] += len(node.deps)

        waves: list[list[str]] = []
        remaining = set(self._nodes.keys())
        while remaining:
            wave = [nid for nid in remaining if in_degree[nid] == 0]
            if not wave:
                raise TaskGraphError(f"Cycle detected. Remaining: {remaining}")
            waves.append(wave)
            for nid in wave:
                remaining.remove(nid)
                for node in self._nodes.values():
                    if nid in node.deps and node.engine_id in remaining:
                        in_degree[node.engine_id] -= 1
        return waves

    async def run_async(
        self,
        context: dict[str, Any],
        gaian_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute all nodes wave-by-wave; concurrent within each wave."""
        gid = gaian_id or self._gaian_id
        for wave in self._resolve_order():
            await asyncio.gather(
                *[self._run_node(self._nodes[nid], context, gid) for nid in wave]
            )
        return context

    async def _run_node(
        self,
        node: EngineNode,
        context: dict[str, Any],
        gaian_id: str | None,
    ) -> None:
        node_inputs = {k: context.get(k) for k in node.inputs}
        if _TRACE_AVAILABLE:
            trace_ctx: Any = AsyncGAIATrace(
                event=TraceEventType.TASK_NODE_EXEC,
                gaian_id=gaian_id,
                canon_refs=node.canon_refs,
                inputs={"engine_id": node.engine_id, "input_keys": node.inputs},
                meta=node.meta,
            )
        else:
            from contextlib import asynccontextmanager
            @asynccontextmanager
            async def _noop():
                yield None
            trace_ctx = _noop()

        async with trace_ctx as trace:
            try:
                result: dict[str, Any] = await asyncio.wait_for(
                    node.handler(**node_inputs),
                    timeout=node.timeout_ms / 1000,
                )
            except asyncio.TimeoutError:
                raise TaskGraphError(
                    f"Node '{node.engine_id}' timed out after {node.timeout_ms}ms"
                )
            context.update(result)
            if _TRACE_AVAILABLE and trace is not None:
                trace.record_output({"output_keys": list(result.keys())})

    def inspect(self) -> list[dict]:
        return [
            {
                "engine_id":  n.engine_id,
                "inputs":     n.inputs,
                "outputs":    n.outputs,
                "deps":       n.deps,
                "timeout_ms": n.timeout_ms,
                "canon_refs": n.canon_refs,
            }
            for n in self._nodes.values()
        ]

    def __len__(self) -> int:
        return len(self._nodes)

    def __repr__(self) -> str:
        return f"TaskGraph(nodes={len(self._nodes)}, gaian_id='{self._gaian_id}')"


async def _demo_run() -> None:
    async def node_a(dominant_hz: float = 528.0, **_: Any) -> dict:
        await asyncio.sleep(0.01)
        return {"synergy_factor": round(dominant_hz / 1000, 4)}

    async def node_b(synergy_factor: float = 0.0, **_: Any) -> dict:
        await asyncio.sleep(0.01)
        return {"affect_score": round(synergy_factor * 1.618, 4)}

    graph = TaskGraph(gaian_id="demo")
    graph.add_node(EngineNode("synergy", node_a, ["dominant_hz"], ["synergy_factor"], [], canon_refs=["C32"]))
    graph.add_node(EngineNode("affect",  node_b, ["synergy_factor"], ["affect_score"], ["synergy"], canon_refs=["C44"]))
    result = await graph.run_async({"dominant_hz": 528.0})
    print(json.dumps(result, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m core.task_graph")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect").set_defaults(func=lambda a: print(json.dumps(TaskGraph().inspect(), indent=2)))
    r = sub.add_parser("run")
    r.add_argument("--demo", action="store_true")
    r.set_defaults(func=lambda a: asyncio.run(_demo_run()) if a.demo else print("Use --demo", file=sys.stderr))
    return p


if __name__ == "__main__":
    _p = _build_parser()
    _a = _p.parse_args()
    _a.func(_a)
