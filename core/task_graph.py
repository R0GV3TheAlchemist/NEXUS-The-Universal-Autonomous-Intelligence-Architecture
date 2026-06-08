"""
core/task_graph.py
==================
GAIA Execution DAG — Sprint G-7

Provides an explicit, declarative task graph for multi-engine orchestration.
Replaces imperative pipeline code with a topologically-sorted, concurrency-safe
execution model. Independent nodes execute concurrently via asyncio.gather;
dependent nodes wait for their upstream outputs to appear in the shared context.

Architecture
------------
    Intent → PlanNode → TaskGraph (DAG of EngineNodes)
           → AgentAllocator → ExecutionRunner → context dict

Canon Refs
----------
  C32 — Synergy Doctrine (all engines participate as a coherent whole)
  C30 — No silent failures (every node has a timeout and explicit status)
  C01 — Sovereignty (the execution plan is explicit and auditable)

GAIATrace Integration
---------------------
Pass a live GAIATrace / AsyncGAIATrace context via the optional `trace`
kwarg on ExecutionRunner.run() (propagated down to each _run_node call).
Two events are emitted per EngineNode execution:

  TASK_START — node engine_id, inputs snapshot, canon_refs
  TASK_END   — node engine_id, outputs, latency_ms, NodeStatus
  ERROR      — emitted on timeout or unhandled exception (before re-raise)

All trace operations are wrapped in try/except — a broken trace writer
never silences an EngineNode result.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, List, Optional

try:
    import networkx as nx  # type: ignore
except ImportError as _nx_err:  # pragma: no cover
    raise ImportError(
        "TaskGraph requires networkx. Install with: pip install networkx"
    ) from _nx_err

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NodeStatus(str, Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    COMPLETE = "complete"
    FAILED   = "failed"
    SKIPPED  = "skipped"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class EngineNode:
    """
    A single unit of work in the execution graph.

    Attributes
    ----------
    engine_id:
        Unique identifier for this node within the graph.
    inputs:
        Keys expected in the shared context dict before this node runs.
    outputs:
        Keys this node writes back to the shared context dict.
    depends_on:
        engine_ids of nodes that must reach COMPLETE status before
        this node is eligible to run.
    timeout_ms:
        Per-node execution timeout in milliseconds (default 5 000 ms).
    canon_refs:
        Canon document references forwarded to trace events.
    handler:
        Async callable: receives a sub-dict of the shared context
        (keys filtered to `inputs`) and returns a dict whose keys
        are written back to the shared context (must cover `outputs`).
        When None the node is SKIPPED.

    Runtime state (set by ExecutionRunner/TaskGraph, not by caller)
    ---------------------------------------------------------------
    status, error
    """
    engine_id:  str
    inputs:     List[str]
    outputs:    List[str]
    depends_on: List[str]
    timeout_ms: int  = 5_000
    canon_refs: List[str] = field(default_factory=list)
    handler:    Optional[Callable[..., Coroutine[Any, Any, dict]]] = None

    # Runtime state — set by TaskGraph, not by caller
    status: NodeStatus    = field(default=NodeStatus.PENDING, init=False)
    error:  Optional[Exception] = field(default=None, init=False)


@dataclass
class PlanNode:
    """
    GAIA’s decoded interpretation of an intent before graph construction.

    Attributes
    ----------
    intent_type:
        Registered key used to look up a PlanFactory builder.
        Examples: ``"synergy_compute"``, ``"memory_recall"``, ``"stage_session"``.
    gaian_id:
        Identifier of the Gaian this plan executes on behalf of.
    raw_input:
        Seed values injected into the shared context at graph construction
        time.  EngineNodes may read from and write back to this dict.
    canon_refs:
        Optional canon refs attached to the plan level (forwarded to trace).
    """
    intent_type: str
    gaian_id:    str
    raw_input:   Dict[str, Any]
    canon_refs:  List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Trace helpers
# ---------------------------------------------------------------------------

def _emit_task_start(
    trace: Any,
    node: EngineNode,
    inputs_snapshot: dict,
) -> None:
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={
                "event":     "TASK_START",
                "engine_id": node.engine_id,
                "inputs":    inputs_snapshot,
            },
            event_type=TraceEventType.TASK_START,
            canon_refs=node.canon_refs,
        )
    except Exception:
        pass


def _emit_task_end(
    trace: Any,
    node: EngineNode,
    result: dict,
    latency_ms: float,
) -> None:
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={
                "event":      "TASK_END",
                "engine_id":  node.engine_id,
                "status":     node.status.value,
                "outputs":    result,
                "latency_ms": round(latency_ms, 3),
            },
            event_type=TraceEventType.TASK_END,
            canon_refs=node.canon_refs,
        )
        trace.record_meta("latency_ms", round(latency_ms, 3))
    except Exception:
        pass


def _emit_node_error(
    trace: Any,
    node: EngineNode,
    exc: BaseException,
) -> None:
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={
                "event":      "TASK_ERROR",
                "engine_id":  node.engine_id,
                "error_type": type(exc).__name__,
                "detail":     str(exc),
            },
            event_type=TraceEventType.ERROR,
            canon_refs=node.canon_refs,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# TaskGraph
# ---------------------------------------------------------------------------

class TaskGraph:
    """
    Directed acyclic graph of EngineNodes for a single intent execution.

    Cycle detection is performed at construction time (not at run time).
    ``execute()`` processes topological generations concurrently via
    ``asyncio.gather``; nodes within the same generation are independent
    and run in parallel.

    Parameters
    ----------
    plan:
        The PlanNode describing the intent and seed context.
    nodes:
        List of EngineNode instances that form the graph.

    Raises
    ------
    ValueError
        If the dependency edges form a cycle.
    """

    def __init__(self, plan: PlanNode, nodes: List[EngineNode]) -> None:
        self.plan = plan
        self._graph: nx.DiGraph = nx.DiGraph()
        self._nodes: Dict[str, EngineNode] = {n.engine_id: n for n in nodes}
        self._context: Dict[str, Any] = dict(plan.raw_input)

        for node in nodes:
            self._graph.add_node(node.engine_id)
            for dep in node.depends_on:
                self._graph.add_edge(dep, node.engine_id)

        if not nx.is_directed_acyclic_graph(self._graph):
            cycles = list(nx.simple_cycles(self._graph))
            raise ValueError(
                f"TaskGraph for intent '{plan.intent_type}' contains cycles: {cycles}"
            )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(
        self,
        trace: Any = None,
    ) -> Dict[str, Any]:
        """
        Topological execution: independent nodes run concurrently;
        dependent nodes wait for their upstream outputs to appear in
        the shared context dict.

        Parameters
        ----------
        trace:
            Optional GAIATrace / AsyncGAIATrace context.  TASK_START and
            TASK_END events are emitted per node; ERROR events on failure.

        Returns
        -------
        dict
            The final shared context dict after all nodes have run.
        """
        for generation in nx.topological_generations(self._graph):
            await asyncio.gather(*[
                self._run_node(self._nodes[node_id], trace=trace)
                for node_id in generation
                if node_id in self._nodes
            ])
        return self._context

    async def _run_node(
        self,
        node: EngineNode,
        trace: Any = None,
    ) -> None:
        """
        Execute a single EngineNode, enforcing its timeout_ms budget.
        Emits TASK_START → TASK_END (or ERROR) trace events.
        """
        if not node.handler:
            node.status = NodeStatus.SKIPPED
            return

        inputs_snapshot = {
            k: self._context[k]
            for k in node.inputs
            if k in self._context
        }

        # TRACE: TASK_START
        _emit_task_start(trace, node, inputs_snapshot)

        node.status = NodeStatus.RUNNING
        t0 = time.perf_counter()

        try:
            result: dict = await asyncio.wait_for(
                node.handler(inputs_snapshot),
                timeout=node.timeout_ms / 1_000,
            )
            self._context.update(result)
            node.status = NodeStatus.COMPLETE

        except asyncio.TimeoutError as exc:
            node.status = NodeStatus.FAILED
            node.error  = exc
            _emit_node_error(trace, node, exc)
            # Timeout does NOT propagate — other nodes in the generation
            # continue; callers inspect failed_nodes() afterwards.
            return

        except Exception as exc:
            node.status = NodeStatus.FAILED
            node.error  = exc
            _emit_node_error(trace, node, exc)
            raise

        latency_ms = (time.perf_counter() - t0) * 1_000

        # TRACE: TASK_END
        _emit_task_end(trace, node, result, latency_ms)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def failed_nodes(self) -> List[EngineNode]:
        """Return all nodes that reached FAILED status."""
        return [n for n in self._nodes.values() if n.status == NodeStatus.FAILED]

    def skipped_nodes(self) -> List[EngineNode]:
        """Return all nodes that were SKIPPED (no handler)."""
        return [n for n in self._nodes.values() if n.status == NodeStatus.SKIPPED]

    def execution_order(self) -> List[List[str]]:
        """Return topological generations (parallel batches) as a nested list."""
        return [list(g) for g in nx.topological_generations(self._graph)]

    def summary(self) -> dict:
        """Return a lightweight status summary suitable for logging or traces."""
        return {
            "plan":     self.plan.intent_type,
            "gaian_id": self.plan.gaian_id,
            "order":    self.execution_order(),
            "nodes": [
                {
                    "id":     n.engine_id,
                    "status": n.status.value,
                    "error":  str(n.error) if n.error else None,
                }
                for n in self._nodes.values()
            ],
        }


# ---------------------------------------------------------------------------
# PlanFactory
# ---------------------------------------------------------------------------

class PlanFactory:
    """
    Registry that maps intent_type strings to TaskGraph builder functions.

    Usage
    -----
    Register a builder::

        @PlanFactory.register("my_intent")
        def _build_my_graph(plan: PlanNode) -> TaskGraph:
            return TaskGraph(plan, [...])

    Build a graph from a plan::

        graph = PlanFactory.build(plan)
        context = await graph.execute(trace=t)
    """

    _registry: Dict[str, Callable[[PlanNode], TaskGraph]] = {}

    @classmethod
    def register(
        cls,
        intent_type: str,
    ) -> Callable:
        """Decorator that registers a builder function for `intent_type`."""
        def decorator(
            fn: Callable[[PlanNode], TaskGraph],
        ) -> Callable[[PlanNode], TaskGraph]:
            cls._registry[intent_type] = fn
            return fn
        return decorator

    @classmethod
    def build(cls, plan: PlanNode) -> TaskGraph:
        """
        Build and return a TaskGraph for the given PlanNode.

        Raises
        ------
        ValueError
            If no builder is registered for ``plan.intent_type``.
        """
        builder = cls._registry.get(plan.intent_type)
        if not builder:
            registered = list(cls._registry.keys())
            raise ValueError(
                f"No TaskGraph registered for intent: {plan.intent_type!r}. "
                f"Registered: {registered}"
            )
        return builder(plan)

    @classmethod
    def registered_intents(cls) -> List[str]:
        """Return all currently registered intent_type strings."""
        return list(cls._registry.keys())


# ---------------------------------------------------------------------------
# Built-in plan templates  (C32 — three most common intent types)
# ---------------------------------------------------------------------------

@PlanFactory.register("synergy_compute")
def _build_synergy_graph(plan: PlanNode) -> TaskGraph:
    """
    synergy_compute graph (C32)
    ---------------------------
    schumann  ┬───────────┬
    emotional ┘──> synergy   (depends on both)
    """
    return TaskGraph(plan, [
        EngineNode(
            engine_id="schumann",
            inputs=["gaian_state"],
            outputs=["schumann_score"],
            depends_on=[],
            canon_refs=["C42"],
        ),
        EngineNode(
            engine_id="emotional",
            inputs=["gaian_state"],
            outputs=["emotional_score"],
            depends_on=[],
            canon_refs=["C32"],
        ),
        EngineNode(
            engine_id="synergy",
            inputs=["gaian_state", "schumann_score", "emotional_score"],
            outputs=["synergy_reading"],
            depends_on=["schumann", "emotional"],
            canon_refs=["C32"],
        ),
    ])


@PlanFactory.register("memory_recall")
def _build_memory_recall_graph(plan: PlanNode) -> TaskGraph:
    """
    memory_recall graph (C01 / C30)
    --------------------------------
    embed  ──> search ──> rerank
    """
    return TaskGraph(plan, [
        EngineNode(
            engine_id="embed",
            inputs=["query"],
            outputs=["query_embedding"],
            depends_on=[],
            canon_refs=["C01"],
        ),
        EngineNode(
            engine_id="search",
            inputs=["query_embedding"],
            outputs=["recall_candidates"],
            depends_on=["embed"],
            canon_refs=["C01"],
        ),
        EngineNode(
            engine_id="rerank",
            inputs=["query", "recall_candidates"],
            outputs=["recalled_memories"],
            depends_on=["search"],
            canon_refs=["C01"],
        ),
    ])


@PlanFactory.register("stage_session")
def _build_stage_session_graph(plan: PlanNode) -> TaskGraph:
    """
    stage_session graph (C32 / C30)
    --------------------------------
    affect  ┬───────────┬
    codex   ┘──> ceremony ──> arc_update
    """
    return TaskGraph(plan, [
        EngineNode(
            engine_id="affect",
            inputs=["gaian_state"],
            outputs=["affect_reading"],
            depends_on=[],
            canon_refs=["C32"],
        ),
        EngineNode(
            engine_id="codex",
            inputs=["gaian_state"],
            outputs=["codex_stage"],
            depends_on=[],
            canon_refs=["C32"],
        ),
        EngineNode(
            engine_id="ceremony",
            inputs=["gaian_state", "affect_reading", "codex_stage"],
            outputs=["ceremony_result"],
            depends_on=["affect", "codex"],
            canon_refs=["C32"],
        ),
        EngineNode(
            engine_id="arc_update",
            inputs=["gaian_state", "ceremony_result"],
            outputs=["arc_delta"],
            depends_on=["ceremony"],
            canon_refs=["C32"],
        ),
    ])


# ---------------------------------------------------------------------------
# AgentAllocator  (G-7: single-agent stub; G-8+: distributed expansion)
# ---------------------------------------------------------------------------

class AgentAllocator:
    """
    Maps TaskGraph EngineNodes to available agents/workers.

    G-7 implementation
    -------------------
    Single-agent, single-machine: all nodes execute on the local event loop
    via ``asyncio.gather``.  The interface is stable for G-8 expansion to
    distributed agents (each running a subset of nodes in their own loop).

    G-8+ expansion points
    ----------------------
    - ``allocate()`` will return a mapping of ``engine_id → AgentHandle``
    - ``AgentHandle.run_node()`` will dispatch via gRPC / message queue
    - ``TaskGraph.execute()`` will call ``allocator.allocate(graph)`` and
      route each node to its assigned agent
    """

    def __init__(self, agents: Optional[List[Any]] = None) -> None:
        # G-7: single implicit agent (the local asyncio event loop)
        self._agents = agents or []

    def allocate(
        self,
        graph: TaskGraph,
    ) -> Dict[str, Any]:
        """
        Return a mapping of engine_id → agent.
        G-7: all nodes map to ``None`` (local execution).
        """
        return {node_id: None for node_id in graph._nodes}

    def agent_count(self) -> int:
        """Number of registered remote agents (0 in G-7)."""
        return len(self._agents)


# ---------------------------------------------------------------------------
# ExecutionRunner
# ---------------------------------------------------------------------------

class ExecutionRunner:
    """
    Top-level entry point: PlanNode → TaskGraph → execute() → context dict.

    Usage
    -----
    ::

        runner = ExecutionRunner()

        plan = PlanNode(
            intent_type="synergy_compute",
            gaian_id="luna",
            raw_input={"gaian_state": gaian_state_dict},
            canon_refs=["C32"],
        )

        with GAIATrace(gaian_id="luna", canon_refs=["C32"]) as trace:
            context = await runner.run(plan, trace=trace)

        print(context["synergy_reading"])

    Parameters
    ----------
    allocator:
        Optional AgentAllocator.  Defaults to a new single-agent allocator.
    """

    def __init__(
        self,
        allocator: Optional[AgentAllocator] = None,
    ) -> None:
        self._allocator = allocator or AgentAllocator()

    async def run(
        self,
        plan: PlanNode,
        trace: Any = None,
    ) -> Dict[str, Any]:
        """
        Build the TaskGraph for `plan` and execute it.

        Parameters
        ----------
        plan:
            Decoded intent + seed context.
        trace:
            Optional GAIATrace / AsyncGAIATrace context for per-node
            TASK_START / TASK_END / ERROR trace events.

        Returns
        -------
        dict
            Final shared context dict after all nodes have executed.

        Raises
        ------
        ValueError
            If ``plan.intent_type`` has no registered PlanFactory builder.
        Exception
            Any unhandled exception from an EngineNode handler propagates
            up (C30 — no silent failures).
        """
        graph = PlanFactory.build(plan)
        return await graph.execute(trace=trace)
