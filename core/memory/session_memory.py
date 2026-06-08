"""
core/memory/session_memory.py
(formerly core/session_memory.py — Phase C physical migration)

GAIA — Session Memory Manager

Manages per-session (in-memory) conversation state for the active query pipeline.
This is separate from GAIAN long-term memory — it handles the ephemeral context
within a single browser session / server instance.

The session memory feeds into:
  1. The synthesizer (conversation context window for the LLM)
  2. The server (to associate queries with active GAIAN)

Canon Ref: C17 (Persistent Memory and Identity Architecture Spec)
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SessionTurn:
    query: str
    answer: str
    timestamp: float = field(default_factory=time.time)
    source_count: int = 0


class SessionMemory:
    """
    Rolling conversation memory for a single session.
    Stores the last N query/answer pairs for context injection.
    """
    MAX_TURNS = 8

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns: list[SessionTurn] = []
        self.active_gaian_slug: Optional[str] = None
        self.created_at = time.time()
        self.last_active = time.time()

    def add_turn(self, query: str, answer: str, source_count: int = 0):
        self.turns.append(SessionTurn(
            query=query,
            answer=answer,
            source_count=source_count
        ))
        # Keep rolling window
        if len(self.turns) > self.MAX_TURNS:
            self.turns = self.turns[-self.MAX_TURNS:]
        self.last_active = time.time()

    def get_context_messages(self) -> list[dict]:
        """
        Return recent turns as LLM-ready message dicts.
        Includes last 6 turns (3 exchanges) for context efficiency.
        """
        messages = []
        for turn in self.turns[-6:]:
            messages.append({"role": "user", "content": turn.query})
            messages.append({"role": "assistant", "content": turn.answer[:600]})
        return messages

    def get_context_summary(self) -> str:
        """
        Return a brief text summary of recent conversation for prompt injection.
        """
        if not self.turns:
            return ""
        recent = self.turns[-3:]
        lines = []
        for t in recent:
            lines.append(f"User asked: {t.query[:80]}")
            lines.append(f"GAIA answered: {t.answer[:120]}...")
        return "Recent conversation context:\n" + "\n".join(lines)


# ------------------------------------------------------------------ #
#  Global Session Store                                                #
# ------------------------------------------------------------------ #

_sessions: dict[str, SessionMemory] = {}
SESSION_TTL = 3600  # 1 hour — sessions expire after inactivity


def get_or_create_session(session_id: str) -> SessionMemory:
    """Get existing session or create a new one."""
    _cleanup_expired_sessions()
    if session_id not in _sessions:
        _sessions[session_id] = SessionMemory(session_id)
    return _sessions[session_id]


def get_session(session_id: str) -> Optional[SessionMemory]:
    """Get existing session or None."""
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def _cleanup_expired_sessions():
    """Remove sessions inactive for more than SESSION_TTL seconds."""
    now = time.time()
    expired = [sid for sid, s in _sessions.items() if now - s.last_active > SESSION_TTL]
    for sid in expired:
        del _sessions[sid]
