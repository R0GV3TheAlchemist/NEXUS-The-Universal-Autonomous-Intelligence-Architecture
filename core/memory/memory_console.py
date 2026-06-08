"""
core/memory/memory_console.py

The Visible Memory & State Console.
Browse, edit, delete, archive, and explain GAIA's memory about a Gaian.

This is the runtime implementation of C-SENTINEL Article 4 (Memory Sovereignty):
  "All data a Sentinel holds about its Gaian belongs to the Gaian.
   The Gaian may inspect, correct, export, or delete any memory."

Canon Reference: C01 (Gaian Sovereignty), C-SENTINEL Article 4
Issue:          #213
Version:        1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from core.memory.memory_store import (
    MemoryCategory,
    MemoryEntry,
    MemoryTier,
    ProvenanceSource,
    SessionState,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ConsoleAction(Enum):
    """Actions the Gaian can take on a memory entry."""
    READ    = "read"
    EDIT    = "edit"
    DELETE  = "delete"
    ARCHIVE = "archive"
    EXPLAIN = "explain"
    EXPORT  = "export"


class ConsoleStatus(Enum):
    """Result status of a console operation."""
    OK           = "ok"
    NOT_FOUND    = "not_found"
    INVALID      = "invalid"
    FORBIDDEN    = "forbidden"


# ---------------------------------------------------------------------------
# Result Types
# ---------------------------------------------------------------------------

@dataclass
class ConsoleResult:
    """
    The result of any console operation.

    Attributes:
        status:    OK, NOT_FOUND, INVALID, or FORBIDDEN.
        message:   Human-readable description of the result.
        entry:     The affected MemoryEntry, if applicable.
        data:      Arbitrary extra payload (e.g. export dict, explanation string).
    """
    status:  ConsoleStatus
    message: str
    entry:   Optional[MemoryEntry] = None
    data:    Optional[dict]        = None


@dataclass
class ExplanationResult:
    """
    Answers "Why am I seeing this?" for a recalled memory.
    Acceptance Criterion: A "why am I seeing this?" explanation is visible for active context.
    """
    memory_id:    str
    key:          str
    value:        str
    explanation:  str                   # Plain-language reason this memory is active
    confidence:   float
    last_used_at: Optional[datetime]
    last_used_context: Optional[str]


# ---------------------------------------------------------------------------
# MemoryConsole
# ---------------------------------------------------------------------------

class MemoryConsole:
    """
    The Visible Memory & State Console.

    The single point of truth for all Gaian-facing memory operations.
    Every read, edit, delete, archive, and explain action flows through here.

    The console enforces C-SENTINEL Article 4 at every operation:
      - No memory is hidden from the Gaian
      - Every operation is logged for the Observability Layer (Issue #222)
      - Deletions are permanent (no shadow copies)
      - Exports are complete and human-readable

    Usage:
        console = MemoryConsole(gaian_id="gaian-001")
        console.store(entry)
        result = console.read(entry_id)
        result = console.explain(entry_id, active_response="Here is your summary...")
        result = console.delete(entry_id)
    """

    def __init__(self, gaian_id: str) -> None:
        self.gaian_id = gaian_id
        self._store: dict[str, MemoryEntry] = {}
        self._session_state: Optional[SessionState] = None

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def store(self, entry: MemoryEntry) -> ConsoleResult:
        """
        Add or update a memory entry.
        If an entry with the same key already exists in the same tier,
        the existing entry is updated rather than duplicated.
        """
        existing = self._find_by_key(entry.key, entry.tier)
        if existing:
            existing.value          = entry.value
            existing.provenance     = entry.provenance
            existing.updated_at     = datetime.now(timezone.utc)
            existing.tags           = entry.tags
            existing.explanation    = entry.explanation
            logger.info("[MemoryConsole] gaian=%s updated memory key=%s id=%s",
                        self.gaian_id, entry.key, existing.id)
            return ConsoleResult(
                status=ConsoleStatus.OK,
                message=f"Memory '{entry.key}' updated.",
                entry=existing,
            )

        self._store[entry.id] = entry
        logger.info("[MemoryConsole] gaian=%s stored memory key=%s id=%s tier=%s",
                    self.gaian_id, entry.key, entry.id, entry.tier.value)
        return ConsoleResult(
            status=ConsoleStatus.OK,
            message=f"Memory '{entry.key}' stored.",
            entry=entry,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self, memory_id: str) -> ConsoleResult:
        """
        Retrieve a single memory entry by ID.
        Acceptance Criterion: Memory objects are browsable.
        """
        entry = self._store.get(memory_id)
        if entry is None:
            return ConsoleResult(
                status=ConsoleStatus.NOT_FOUND,
                message=f"No memory found with id '{memory_id}'.",
            )
        return ConsoleResult(
            status=ConsoleStatus.OK,
            message=f"Memory '{entry.key}' retrieved.",
            entry=entry,
            data=entry.to_dict(),
        )

    def browse(
        self,
        tier: Optional[MemoryTier]     = None,
        category: Optional[MemoryCategory] = None,
        tag: Optional[str]             = None,
    ) -> list[MemoryEntry]:
        """
        Return all memory entries matching the given filters.
        Omitting all filters returns every non-archived durable memory.
        Acceptance Criterion: Memory objects are browsable in a dedicated UI.
        """
        results = list(self._store.values())

        if tier is not None:
            results = [e for e in results if e.tier == tier]
        else:
            # Default: exclude archived entries
            results = [e for e in results if e.tier != MemoryTier.ARCHIVED]

        if category is not None:
            results = [e for e in results if e.category == category]

        if tag is not None:
            results = [e for e in results if tag in e.tags]

        return sorted(results, key=lambda e: e.updated_at, reverse=True)

    # ------------------------------------------------------------------
    # Edit
    # ------------------------------------------------------------------

    def edit(self, memory_id: str, new_value: str) -> ConsoleResult:
        """
        Update the value of an existing memory entry.
        Acceptance Criterion: Memory entries support edit action with immediate effect.
        """
        entry = self._store.get(memory_id)
        if entry is None:
            return ConsoleResult(
                status=ConsoleStatus.NOT_FOUND,
                message=f"No memory found with id '{memory_id}'.",
            )
        if entry.tier == MemoryTier.ARCHIVED:
            return ConsoleResult(
                status=ConsoleStatus.FORBIDDEN,
                message="Archived memories cannot be edited. Restore first.",
                entry=entry,
            )

        old_value       = entry.value
        entry.value     = new_value
        entry.updated_at = datetime.now(timezone.utc)
        # When Gaian edits a memory, provenance upgrades to GAIAN_EXPLICIT
        entry.provenance.source     = ProvenanceSource.GAIAN_EXPLICIT
        entry.provenance.confidence = 1.0

        logger.info(
            "[MemoryConsole] gaian=%s edited memory id=%s key=%s old=%r new=%r",
            self.gaian_id, memory_id, entry.key, old_value, new_value,
        )
        return ConsoleResult(
            status=ConsoleStatus.OK,
            message=f"Memory '{entry.key}' updated.",
            entry=entry,
            data={"old_value": old_value, "new_value": new_value},
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, memory_id: str) -> ConsoleResult:
        """
        Permanently delete a memory entry.
        No shadow copies. Deletion is immediate and irreversible.
        C-SENTINEL Article 4: "Deletion requests must be honored immediately and permanently."
        Acceptance Criterion: Memory entries support delete action with immediate effect.
        """
        entry = self._store.pop(memory_id, None)
        if entry is None:
            return ConsoleResult(
                status=ConsoleStatus.NOT_FOUND,
                message=f"No memory found with id '{memory_id}'.",
            )
        logger.warning(
            "[MemoryConsole] gaian=%s DELETED memory id=%s key=%s — permanent",
            self.gaian_id, memory_id, entry.key,
        )
        return ConsoleResult(
            status=ConsoleStatus.OK,
            message=f"Memory '{entry.key}' permanently deleted.",
            entry=entry,
        )

    # ------------------------------------------------------------------
    # Archive
    # ------------------------------------------------------------------

    def archive(self, memory_id: str) -> ConsoleResult:
        """
        Soft-delete a memory entry — retained for audit, invisible to active context.
        Acceptance Criterion: Memory entries support archive action.
        """
        entry = self._store.get(memory_id)
        if entry is None:
            return ConsoleResult(
                status=ConsoleStatus.NOT_FOUND,
                message=f"No memory found with id '{memory_id}'.",
            )
        if entry.tier == MemoryTier.ARCHIVED:
            return ConsoleResult(
                status=ConsoleStatus.OK,
                message=f"Memory '{entry.key}' is already archived.",
                entry=entry,
            )

        entry.tier       = MemoryTier.ARCHIVED
        entry.updated_at = datetime.now(timezone.utc)
        logger.info("[MemoryConsole] gaian=%s archived memory id=%s key=%s",
                    self.gaian_id, memory_id, entry.key)
        return ConsoleResult(
            status=ConsoleStatus.OK,
            message=f"Memory '{entry.key}' archived.",
            entry=entry,
        )

    # ------------------------------------------------------------------
    # Explain
    # ------------------------------------------------------------------

    def explain(self, memory_id: str, active_response: Optional[str] = None) -> ConsoleResult:
        """
        Answer "Why am I seeing this?" for a recalled memory.

        Args:
            memory_id:       The ID of the memory to explain.
            active_response: The response text where this memory was recalled (optional).

        Acceptance Criterion: A "why am I seeing this?" explanation is visible for active context.
        """
        entry = self._store.get(memory_id)
        if entry is None:
            return ConsoleResult(
                status=ConsoleStatus.NOT_FOUND,
                message=f"No memory found with id '{memory_id}'.",
            )

        explanation = self._build_explanation(entry, active_response)
        entry.explanation       = explanation
        entry.last_used_at      = datetime.now(timezone.utc)
        entry.last_used_context = active_response

        result = ExplanationResult(
            memory_id=entry.id,
            key=entry.key,
            value=entry.value,
            explanation=explanation,
            confidence=entry.provenance.confidence,
            last_used_at=entry.last_used_at,
            last_used_context=active_response,
        )

        return ConsoleResult(
            status=ConsoleStatus.OK,
            message="Explanation generated.",
            entry=entry,
            data={
                "explanation":        result.explanation,
                "confidence":         result.confidence,
                "last_used_at":       result.last_used_at.isoformat() if result.last_used_at else None,
                "last_used_context":  result.last_used_context,
            },
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_all(self) -> list[dict]:
        """
        Export every memory entry as a complete, human-readable list.
        C-SENTINEL Article 4: "Memory exports must be complete, human-readable,
        and available on demand."
        """
        return [entry.to_dict() for entry in self._store.values()]

    # ------------------------------------------------------------------
    # Session State
    # ------------------------------------------------------------------

    def set_session_state(self, session_state: SessionState) -> None:
        """Register the current session's state."""
        self._session_state = session_state

    def get_session_state(self) -> Optional[SessionState]:
        """Retrieve current session state. Returns None if no session is active."""
        return self._session_state

    def clear_session_state(self) -> None:
        """
        Clear session state at session end.
        Session-scoped memories are NOT automatically promoted to durable.
        """
        self._session_state = None
        logger.info("[MemoryConsole] gaian=%s session state cleared", self.gaian_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_by_key(self, key: str, tier: MemoryTier) -> Optional[MemoryEntry]:
        """Find an existing entry by key + tier combination."""
        for entry in self._store.values():
            if entry.key == key and entry.tier == tier:
                return entry
        return None

    def _build_explanation(self, entry: MemoryEntry, active_response: Optional[str]) -> str:
        """
        Build a plain-language explanation of why a memory is active.
        """
        source_map = {
            ProvenanceSource.GAIAN_EXPLICIT:    "you told me this directly",
            ProvenanceSource.GAIAN_IMPLICIT:    "I inferred this from something you said or did",
            ProvenanceSource.SENTINEL_INFERRED: "I observed this pattern over time",
            ProvenanceSource.SYSTEM_GENERATED:  "this was recorded automatically by the system",
            ProvenanceSource.IMPORTED:          "this was imported with your consent",
        }
        source_desc  = source_map.get(entry.provenance.source, "this was recorded")
        confidence_pct = int(entry.provenance.confidence * 100)
        tier_desc    = "a lasting memory" if entry.tier == MemoryTier.DURABLE else "a session note"

        base = (
            f"This is {tier_desc}: '{entry.key} = {entry.value}'. "
            f"I know this because {source_desc} "
            f"(confidence: {confidence_pct}%). "
        )

        if entry.provenance.origin_context:
            base += f"It was first recorded when: \"{entry.provenance.origin_context}\". "

        if active_response:
            base += "I used it in this response because it was relevant to the current context."

        return base.strip()
