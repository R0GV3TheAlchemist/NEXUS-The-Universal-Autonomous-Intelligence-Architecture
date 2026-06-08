"""
core.runtime.orchestrator
=========================
GAIAOrchestrator — central nervous system of GAIA-OS.

One singleton is created at startup (via init_orchestrator()) and
accessed everywhere via get_orchestrator().

Every conversation turn follows this pipeline:

  ┌─────────────────────────────────────────────────────┐
  │              before_turn()                          │
  │  1. get/create session                              │
  │  2. retrieve top-k semantic memories                │
  │  3. apply perception operator → quantum kernel      │
  │  4. build memory_context block (text)               │
  │  5. build quantum_context block (text)              │
  │  6. build goal_context block (text)                 │
  │  7. audit: ACTION_PROPOSED                          │
  │  → return TurnContext (caller injects into prompt)  │
  └─────────────────────────────────────────────────────┘
               │
         [LLM call happens in the router]
               │
  ┌─────────────────────────────────────────────────────┐
  │              after_turn()                           │
  │  1. remember user message                           │
  │  2. remember GAIA reply                             │
  │  3. apply emotion + intention operators to kernel   │
  │  4. advance active goals (auto_advance)             │
  │  5. run scheduler batch (background tasks)          │
  │  6. prune memory if over capacity                   │
  │  7. audit: ACTION_EXECUTED                          │
  └─────────────────────────────────────────────────────┘

All errors are caught and logged — the orchestrator NEVER raises
an exception that would break the chat response to the user.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("gaia.orchestrator")

# ── lazy imports (all Phase 2 modules) ────────────────────────────────────────
# Imported lazily so that import errors in optional deps (sqlite-vec, numpy)
# never crash the whole server on startup.


def _import_memory():
    from core.memory import MemoryStore, MemoryItem, MemoryKind, MemoryTier, OllamaEmbedder, FallbackEmbedder
    return MemoryStore, MemoryItem, MemoryKind, MemoryTier, OllamaEmbedder, FallbackEmbedder


def _import_quantum():
    from core.quantum import (
        QuantumKernel, GAIA_BASIS_LABELS,
        make_perception_pipeline, make_emotion_pipeline, make_intention_pipeline,
    )
    return QuantumKernel, GAIA_BASIS_LABELS, make_perception_pipeline, make_emotion_pipeline, make_intention_pipeline


def _import_planner():
    from core.planner import GoalRegistry, PolicyEngine, TaskScheduler
    return GoalRegistry, PolicyEngine, TaskScheduler


def _import_audit():
    from core.audit import ActionLedger, AuditEvent, EventType
    return ActionLedger, AuditEvent, EventType


def _import_pruner():
    from core.memory import MemoryPruner
    return MemoryPruner


# ── TurnContext ────────────────────────────────────────────────────────────────

@dataclass
class TurnContext:
    """
    Carries all pre-turn context the router needs to enrich the LLM call.

    Attributes
    ----------
    user_id         : Owner of this turn.
    session_id      : Current session.
    memory_items    : Top-k recalled MemoryItem objects (already ranked).
    memory_context  : Pre-formatted text block ready for system prompt injection.
    quantum_context : QuantumKernel.context_block() string.
    goal_context    : Active goal description, or empty string.
    system_suffix   : All three blocks joined — inject at end of system prompt.
    kernel          : Live QuantumKernel for this session (for post-turn ops).
    started_at      : Unix timestamp of before_turn() call.
    """
    user_id:         str
    session_id:      str
    memory_items:    list   = field(default_factory=list)
    memory_context:  str    = ""
    quantum_context: str    = ""
    goal_context:    str    = ""
    system_suffix:   str    = ""
    kernel:          object = None   # QuantumKernel
    started_at:      float  = field(default_factory=time.time)


# ── GAIAOrchestrator ───────────────────────────────────────────────────────────

class GAIAOrchestrator:
    """
    Central orchestrator — initialise once, share everywhere.

    Parameters
    ----------
    db_dir        : Directory for SQLite files (memory + audit).  Defaults to ./data.
    embedder_type : 'ollama' | 'fallback'.  'ollama' requires Ollama running locally.
    memory_capacity : Max live memory rows per user before pruning.  Default 100_000.
    max_memory_k  : How many memories to retrieve per turn.  Default 12.
    scheduler_max_concurrent : Parallel task slots.  Default 4.
    """

    def __init__(
        self,
        db_dir:               str = "./data",
        embedder_type:        str = "ollama",
        memory_capacity:      int = 100_000,
        max_memory_k:         int = 12,
        scheduler_max_concurrent: int = 4,
    ) -> None:
        import os
        os.makedirs(db_dir, exist_ok=True)

        self._db_dir          = db_dir
        self._max_k           = max_memory_k
        self._memory_capacity = memory_capacity
        self._kernels: dict   = {}   # session_id → QuantumKernel

        self._ready   = False
        self._embedder_type = embedder_type

        # These are set in async_init()
        self.memory:    object = None
        self.pruner:    object = None
        self.goals:     object = None
        self.policy:    object = None
        self.scheduler: object = None
        self.ledger:    object = None

        from core.runtime.session import SessionRegistry
        self.sessions = SessionRegistry()

    async def async_init(self) -> None:
        """Async initialisation — call once from FastAPI lifespan."""
        try:
            MemoryStore, MemoryItem, MemoryKind, MemoryTier, OllamaEmbedder, FallbackEmbedder = _import_memory()
            if self._embedder_type == "ollama":
                try:
                    embedder = OllamaEmbedder()
                    log.info("[Orchestrator] Embedder: Ollama (nomic-embed-text)")
                except Exception:
                    embedder = FallbackEmbedder()
                    log.warning("[Orchestrator] Ollama embedder unavailable — using FallbackEmbedder.")
            else:
                embedder = FallbackEmbedder()
                log.info("[Orchestrator] Embedder: FallbackEmbedder")

            self.memory = MemoryStore(
                db_path=os.path.join(self._db_dir, "gaia_memory.sqlite"),
                embedder=embedder,
                capacity=self._memory_capacity,
            )
            MemoryPruner = _import_pruner()
            self.pruner = MemoryPruner(self.memory, capacity=self._memory_capacity)
            log.info("[Orchestrator] MemoryStore ready.")
        except Exception as exc:
            log.error("[Orchestrator] MemoryStore init failed: %s", exc)

        try:
            GoalRegistry, PolicyEngine, TaskScheduler = _import_planner()
            self.goals     = GoalRegistry()
            self.policy    = PolicyEngine()
            self.scheduler = TaskScheduler(
                max_concurrent=4,
                policy_engine=self.policy,
            )
            log.info("[Orchestrator] Planner + PolicyEngine + Scheduler ready.")
        except Exception as exc:
            log.error("[Orchestrator] Planner init failed: %s", exc)

        try:
            ActionLedger, AuditEvent, EventType = _import_audit()
            self.ledger = ActionLedger(
                db_path=os.path.join(self._db_dir, "gaia_audit.sqlite")
            )
            log.info("[Orchestrator] ActionLedger ready.")
        except Exception as exc:
            log.error("[Orchestrator] Ledger init failed: %s", exc)

        self._ready = True
        log.info("[Orchestrator] Fully initialised.")

    # ------------------------------------------------------------------
    # Kernel management
    # ------------------------------------------------------------------

    def _get_kernel(self, session_id: str, user_id: str) -> object:
        """Return existing kernel or create one for this session."""
        if session_id not in self._kernels:
            try:
                QuantumKernel, GAIA_BASIS_LABELS, *_ = _import_quantum()
                self._kernels[session_id] = QuantumKernel(
                    user_id=user_id,
                    session_id=session_id,
                )
            except Exception as exc:
                log.warning("[Orchestrator] QuantumKernel unavailable: %s", exc)
                return None
        return self._kernels.get(session_id)

    # ------------------------------------------------------------------
    # before_turn
    # ------------------------------------------------------------------

    async def before_turn(
        self,
        user_id:      str,
        user_message: str,
        session_id:   Optional[str] = None,
    ) -> TurnContext:
        """
        Run all pre-LLM steps for one conversation turn.
        Returns a TurnContext the router uses to enrich the system prompt.
        """
        session = self.sessions.get_or_create(user_id, session_id)
        sid     = session.session_id

        ctx = TurnContext(user_id=user_id, session_id=sid)

        # ── 1. Retrieve semantic memories ──────────────────────────────
        if self.memory:
            try:
                hits = await self.memory.retrieve(
                    user_id=user_id,
                    query=user_message,
                    top_k=self._max_k,
                )
                ctx.memory_items = hits
                if hits:
                    lines = []
                    for h in hits:
                        label = h.item.kind.value if hasattr(h.item, 'kind') else 'memory'
                        lines.append(f"[{label}] {h.item.text}")
                    ctx.memory_context = "## Recalled Memories\n" + "\n".join(lines)
            except Exception as exc:
                log.warning("[Orchestrator] Memory retrieval failed: %s", exc)

        # ── 2. Quantum kernel: perception step ─────────────────────────
        kernel = self._get_kernel(sid, user_id)
        ctx.kernel = kernel
        if kernel:
            try:
                _, _, make_perception_pipeline, _, _ = _import_quantum()
                ops = make_perception_pipeline(focus=0.6)
                kernel.step(ops, decoherence_rate=0.02)
                ctx.quantum_context = kernel.context_block()
            except Exception as exc:
                log.warning("[Orchestrator] Quantum step failed: %s", exc)

        # ── 3. Active goal context ─────────────────────────────────────
        if self.goals:
            try:
                active = self.goals.next_goal(user_id)
                if active:
                    nxt = active.next_step()
                    step_desc = nxt.description if nxt else "(all steps complete)"
                    ctx.goal_context = (
                        f"## Active Goal\n"
                        f"{active.title} ({active.progress:.0%} complete)\n"
                        f"Next step: {step_desc}"
                    )
            except Exception as exc:
                log.warning("[Orchestrator] Goal context failed: %s", exc)

        # ── 4. Compose system_suffix ───────────────────────────────────
        parts = [p for p in [
            ctx.quantum_context,
            ctx.memory_context,
            ctx.goal_context,
        ] if p]
        ctx.system_suffix = "\n\n".join(parts)

        # ── 5. Audit: proposed ────────────────────────────────────────
        self._audit(
            event_type_str="action_proposed",
            actor="user",
            user_id=user_id,
            session_id=sid,
            action="chat_turn",
            outcome="proposed",
            justification=user_message[:200],
        )

        return ctx

    # ------------------------------------------------------------------
    # after_turn
    # ------------------------------------------------------------------

    async def after_turn(
        self,
        user_id:      str,
        user_message: str,
        gaia_reply:   str,
        ctx:          TurnContext,
        importance:   float = 0.5,
    ) -> None:
        """
        Run all post-LLM steps: store memories, advance kernel,
        tick goals, run scheduler, prune, audit.
        """
        sid = ctx.session_id
        mem_refs = []

        # ── 1. Remember user message ───────────────────────────────────
        if self.memory:
            try:
                MemoryStore, MemoryItem, MemoryKind, MemoryTier, *_ = _import_memory()
                uid = await self.memory.remember(
                    user_id=user_id,
                    text=user_message,
                    role="user",
                    kind=MemoryKind.MESSAGE,
                    importance=importance,
                    session_id=sid,
                )
                mem_refs.append(str(uid))
            except Exception as exc:
                log.warning("[Orchestrator] Remember user msg failed: %s", exc)

        # ── 2. Remember GAIA reply ─────────────────────────────────────
        if self.memory:
            try:
                MemoryStore, MemoryItem, MemoryKind, MemoryTier, *_ = _import_memory()
                rid = await self.memory.remember(
                    user_id=user_id,
                    text=gaia_reply,
                    role="gaia",
                    kind=MemoryKind.MESSAGE,
                    importance=importance * 0.8,
                    session_id=sid,
                )
                mem_refs.append(str(rid))
            except Exception as exc:
                log.warning("[Orchestrator] Remember GAIA reply failed: %s", exc)

        # ── 3. Quantum kernel: emotion + intention step ────────────────
        if ctx.kernel:
            try:
                _, GAIA_BASIS_LABELS, _, make_emotion_pipeline, make_intention_pipeline = _import_quantum()
                # Neutral affect — real affect engine values would come from
                # the GAIANRuntime state snapshot in a future integration pass.
                neutral_affect = {
                    "emotion:calm":    0.3,
                    "emotion:joy":     0.1,
                    "intention:create": 0.4,
                }
                ops = make_emotion_pipeline(neutral_affect, GAIA_BASIS_LABELS)
                ctx.kernel.step(ops, decoherence_rate=0.01)
            except Exception as exc:
                log.warning("[Orchestrator] Post-turn quantum step failed: %s", exc)

        # ── 4. Auto-advance active goals ───────────────────────────────
        if self.goals:
            try:
                for g in self.goals.active(user_id=user_id):
                    g.auto_advance()
            except Exception as exc:
                log.warning("[Orchestrator] Goal auto-advance failed: %s", exc)

        # ── 5. Run scheduler batch (non-blocking fire-and-forget) ──────
        if self.scheduler:
            try:
                asyncio.create_task(self.scheduler.run_once())
            except Exception as exc:
                log.warning("[Orchestrator] Scheduler tick failed: %s", exc)

        # ── 6. Prune expired TTL items (lightweight, sync) ─────────────
        if self.pruner:
            try:
                self.pruner.prune_expired_ttl()
            except Exception as exc:
                log.warning("[Orchestrator] TTL prune failed: %s", exc)

        # ── 7. Audit: executed ────────────────────────────────────────
        latency = round((time.time() - ctx.started_at) * 1000)
        self._audit(
            event_type_str="action_executed",
            actor="gaia",
            user_id=user_id,
            session_id=sid,
            action="chat_turn",
            outcome="success",
            justification=f"Turn completed in {latency}ms. Reply length: {len(gaia_reply)} chars.",
            memory_refs=mem_refs,
            state_ref=sid,
        )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    async def remember(
        self,
        user_id:    str,
        text:       str,
        kind_str:   str = "note",
        importance: float = 0.5,
        session_id: Optional[str] = None,
    ) -> Optional[int]:
        """Store one memory item.  Returns the new row id, or None on error."""
        if not self.memory:
            return None
        try:
            MemoryStore, MemoryItem, MemoryKind, MemoryTier, *_ = _import_memory()
            kind = MemoryKind(kind_str) if kind_str in MemoryKind._value2member_map_ else MemoryKind.NOTE
            return await self.memory.remember(
                user_id=user_id,
                text=text,
                role="user",
                kind=kind,
                importance=importance,
                session_id=session_id,
            )
        except Exception as exc:
            log.warning("[Orchestrator] remember() failed: %s", exc)
            return None

    async def retrieve(
        self,
        user_id:  str,
        query:    str,
        top_k:    int = 10,
    ) -> list:
        """Retrieve top-k memories for a user.  Returns list of MemoryHit."""
        if not self.memory:
            return []
        try:
            return await self.memory.retrieve(user_id=user_id, query=query, top_k=top_k)
        except Exception as exc:
            log.warning("[Orchestrator] retrieve() failed: %s", exc)
            return []

    def verify_ledger(self) -> dict:
        """Run chain integrity check and return the result dict."""
        if not self.ledger:
            return {"ok": False, "reason": "Ledger not initialised"}
        result = self.ledger.verify_chain()
        return {
            "ok":           result.ok,
            "checked_rows": result.checked_rows,
            "failed_row_id": result.failed_row_id,
            "reason":        result.reason,
        }

    async def shutdown(self) -> None:
        """Graceful shutdown — flush scheduler and close ledger."""
        if self.scheduler:
            self.scheduler.stop()
        if self.ledger:
            self.ledger.close()
        log.info("[Orchestrator] Shutdown complete.")

    def status(self) -> dict:
        """Return a health/status dict for the /health endpoint."""
        return {
            "ready":            self._ready,
            "memory_ok":        self.memory is not None,
            "planner_ok":       self.goals is not None,
            "scheduler_ok":     self.scheduler is not None,
            "ledger_ok":        self.ledger is not None,
            "active_sessions":  len(self.sessions.active_sessions()),
            "active_kernels":   len(self._kernels),
            "scheduler_stats":  self.scheduler.stats() if self.scheduler else {},
            "goal_summary":     self.goals.summary() if self.goals else {},
        }

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _audit(
        self,
        event_type_str: str,
        actor:          str,
        user_id:        Optional[str]  = None,
        session_id:     Optional[str]  = None,
        action:         Optional[str]  = None,
        outcome:        Optional[str]  = None,
        justification:  str            = "",
        memory_refs:    list           = None,
        state_ref:      Optional[str]  = None,
        metadata:       dict           = None,
    ) -> None:
        if not self.ledger:
            return
        try:
            ActionLedger, AuditEvent, EventType = _import_audit()
            et = EventType(event_type_str) if event_type_str in EventType._value2member_map_ else EventType.SYSTEM_EVENT
            event = AuditEvent(
                event_type=et,
                actor=actor,
                user_id=user_id,
                session_id=session_id,
                action=action,
                outcome=outcome,
                justification=justification,
                memory_refs=memory_refs or [],
                state_ref=state_ref,
                metadata=metadata or {},
            )
            self.ledger.append(event)
        except Exception as exc:
            log.warning("[Orchestrator] Audit write failed: %s", exc)


# ── Global singleton ───────────────────────────────────────────────────────────

_orchestrator: Optional[GAIAOrchestrator] = None


def init_orchestrator(**kwargs) -> GAIAOrchestrator:
    """Create (or replace) the global orchestrator singleton."""
    global _orchestrator
    _orchestrator = GAIAOrchestrator(**kwargs)
    return _orchestrator


def get_orchestrator() -> GAIAOrchestrator:
    """Return the global orchestrator singleton.
    Raises RuntimeError if init_orchestrator() has not been called.
    """
    if _orchestrator is None:
        raise RuntimeError(
            "GAIAOrchestrator not initialised. "
            "Call init_orchestrator() and await async_init() in the FastAPI lifespan."
        )
    return _orchestrator
