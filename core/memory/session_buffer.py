"""M0 Session Buffer — Canon C17: ephemeral in-session working memory.

The Session Buffer is GAIA's working memory during an active session.
It is NEVER persisted automatically.
Transfer to M1 (Episodic) requires explicit Human Principal authorisation.

It behaves like a scratchpad: fast writes, ordered retrieval, full clear on exit.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .layers import MemoryLayer, MemoryRecord, MemoryScope, MemoryTag


class SessionBuffer:
    """M0: In-session working memory. Ephemeral. Never auto-persisted.

    Lifecycle:
      1. Created when a session opens.
      2. Records are appended as the session progresses.
      3. At session close: HP may authorise transfer to M1; otherwise cleared.
    """

    def __init__(self, session_id: str, gaian_id: str, human_principal_id: str) -> None:
        self.session_id = session_id
        self.gaian_id = gaian_id
        self.human_principal_id = human_principal_id
        self._records: list[MemoryRecord] = []
        self._opened_at: datetime = datetime.now(timezone.utc)
        self._is_closed: bool = False

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def append(
        self,
        content: str,
        tags: Optional[list[MemoryTag]] = None,
        structured_data: Optional[dict[str, Any]] = None,
        confidence: float = 1.0,
        source: str = "SESSION",
    ) -> MemoryRecord:
        """Append a record to the session buffer."""
        if self._is_closed:
            raise RuntimeError(
                f"Session {self.session_id} is closed. Cannot append to a closed buffer."
            )
        record = MemoryRecord(
            layer=MemoryLayer.M0_SESSION,
            scope=MemoryScope.PRIVATE,
            gaian_id=self.gaian_id,
            human_principal_id=self.human_principal_id,
            session_id=self.session_id,
            content=content,
            structured_data=structured_data or {},
            tags=tags or [],
            confidence=confidence,
            source=source,
        )
        self._records.append(record)
        return record

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def all(self, active_only: bool = True) -> list[MemoryRecord]:
        """Return all records in chronological order."""
        records = self._records
        if active_only:
            records = [r for r in records if r.is_active]
        return list(records)

    def by_tag(self, tag: MemoryTag) -> list[MemoryRecord]:
        """Filter buffer records by a specific tag."""
        return [r for r in self.all() if tag in r.tags]

    def recent(self, n: int = 10) -> list[MemoryRecord]:
        """Return the n most recent records."""
        return self.all()[-n:]

    def count(self) -> int:
        return len([r for r in self._records if r.is_active])

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> list[MemoryRecord]:
        """Close the session buffer. Returns all records for optional M1 transfer.

        After close, no new records can be appended.
        The records returned are candidates for HP-authorised M1 persistence.
        """
        self._is_closed = True
        return self.all()

    def clear(self) -> None:
        """Discard all records. Called when HP does NOT authorise M1 transfer."""
        self._records.clear()

    @property
    def is_closed(self) -> bool:
        return self._is_closed

    @property
    def duration_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self._opened_at).total_seconds()

    def __repr__(self) -> str:
        return (
            f"<SessionBuffer session={self.session_id[:8]} "
            f"records={self.count()} closed={self._is_closed}>"
        )
