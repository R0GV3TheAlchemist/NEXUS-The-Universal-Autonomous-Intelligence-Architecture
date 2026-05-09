"""
core/planner/goal_store.py
Goal persistence layer for GAIA-OS.

Goals are stored in memory.json under the "goals" key.
Each goal carries Spiritus metadata so the GAIAN's
pneuma_flow and spiritu_stage are recorded at creation/update.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_MEMORY_PATH = Path("memory.json")


def _load_memory() -> Dict[str, Any]:
    if _MEMORY_PATH.exists():
        try:
            return json.loads(_MEMORY_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_memory(data: Dict[str, Any]) -> None:
    _MEMORY_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Goal schema
# ---------------------------------------------------------------------------

class GoalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class GoalPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Goal:
    """
    A single GAIAN goal.

    Attributes
    ----------
    id              : stable UUID string
    title           : short human-readable label
    description     : full intent / context
    status          : GoalStatus enum
    priority        : GoalPriority enum
    steps           : ordered list of step dicts {id, label, done}
    tags            : free-form list of strings
    due_date        : optional ISO-8601 date string
    created_at      : ISO-8601 UTC timestamp
    updated_at      : ISO-8601 UTC timestamp
    spiritu_stage   : SpirituStage.name captured at creation/last update
    pneuma_flow     : float 0-1 captured at creation/last update
    breath_rhythm   : float 0-1 captured at creation/last update
    parent_id       : optional parent goal UUID (for sub-goals)
    """

    def __init__(
        self,
        title: str,
        description: str = "",
        priority: GoalPriority = GoalPriority.MEDIUM,
        steps: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        spiritu_stage: str = "CALCINATION",
        pneuma_flow: float = 0.0,
        breath_rhythm: float = 0.0,
        parent_id: Optional[str] = None,
        *,
        _id: Optional[str] = None,
        _created_at: Optional[str] = None,
        _updated_at: Optional[str] = None,
        _status: GoalStatus = GoalStatus.ACTIVE,
    ):
        now = datetime.now(timezone.utc).isoformat()
        self.id: str = _id or str(uuid.uuid4())
        self.title: str = title
        self.description: str = description
        self.status: GoalStatus = _status
        self.priority: GoalPriority = priority
        self.steps: List[Dict[str, Any]] = steps or []
        self.tags: List[str] = tags or []
        self.due_date: Optional[str] = due_date
        self.created_at: str = _created_at or now
        self.updated_at: str = _updated_at or now
        self.spiritu_stage: str = spiritu_stage
        self.pneuma_flow: float = pneuma_flow
        self.breath_rhythm: float = breath_rhythm
        self.parent_id: Optional[str] = parent_id

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "steps": self.steps,
            "tags": self.tags,
            "due_date": self.due_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "spiritu_stage": self.spiritu_stage,
            "pneuma_flow": self.pneuma_flow,
            "breath_rhythm": self.breath_rhythm,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Goal":
        return cls(
            title=d["title"],
            description=d.get("description", ""),
            priority=GoalPriority(d.get("priority", "medium")),
            steps=d.get("steps", []),
            tags=d.get("tags", []),
            due_date=d.get("due_date"),
            spiritu_stage=d.get("spiritu_stage", "CALCINATION"),
            pneuma_flow=d.get("pneuma_flow", 0.0),
            breath_rhythm=d.get("breath_rhythm", 0.0),
            parent_id=d.get("parent_id"),
            _id=d.get("id"),
            _created_at=d.get("created_at"),
            _updated_at=d.get("updated_at"),
            _status=GoalStatus(d.get("status", "active")),
        )

    def progress(self) -> float:
        """Return completion ratio of steps (0.0 – 1.0)."""
        if not self.steps:
            return 0.0
        done = sum(1 for s in self.steps if s.get("done", False))
        return done / len(self.steps)


# ---------------------------------------------------------------------------
# GoalStore — the public CRUD interface
# ---------------------------------------------------------------------------

class GoalStore:
    """
    Persists goals inside memory.json["goals"].
    Thread-safety: single-process only (no file locking).
    For production, swap _load / _save with a DB backend.
    """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_goals(self) -> Dict[str, Dict]:
        mem = _load_memory()
        return mem.get("goals", {})

    def _write_goals(self, goals: Dict[str, Dict]) -> None:
        mem = _load_memory()
        mem["goals"] = goals
        _save_memory(mem)

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        steps: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        spiritu_stage: str = "CALCINATION",
        pneuma_flow: float = 0.0,
        breath_rhythm: float = 0.0,
        parent_id: Optional[str] = None,
    ) -> Goal:
        goal = Goal(
            title=title,
            description=description,
            priority=GoalPriority(priority),
            steps=steps or [],
            tags=tags or [],
            due_date=due_date,
            spiritu_stage=spiritu_stage,
            pneuma_flow=pneuma_flow,
            breath_rhythm=breath_rhythm,
            parent_id=parent_id,
        )
        goals = self._read_goals()
        goals[goal.id] = goal.to_dict()
        self._write_goals(goals)
        return goal

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def get(self, goal_id: str) -> Optional[Goal]:
        goals = self._read_goals()
        raw = goals.get(goal_id)
        return Goal.from_dict(raw) if raw else None

    def list_all(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> List[Goal]:
        goals = [Goal.from_dict(d) for d in self._read_goals().values()]
        if status:
            goals = [g for g in goals if g.status.value == status]
        if priority:
            goals = [g for g in goals if g.priority.value == priority]
        if tag:
            goals = [g for g in goals if tag in g.tags]
        if parent_id is not None:
            goals = [g for g in goals if g.parent_id == parent_id]
        return sorted(goals, key=lambda g: g.created_at, reverse=True)

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update(
        self,
        goal_id: str,
        **kwargs: Any,
    ) -> Optional[Goal]:
        """
        Partial update. Pass any Goal field as a kwarg.
        'steps', 'tags' are replaced wholesale if provided.
        Returns None if goal not found.
        """
        goals = self._read_goals()
        raw = goals.get(goal_id)
        if raw is None:
            return None

        allowed = {
            "title", "description", "status", "priority",
            "steps", "tags", "due_date",
            "spiritu_stage", "pneuma_flow", "breath_rhythm",
            "parent_id",
        }
        for k, v in kwargs.items():
            if k in allowed:
                # Coerce enums back to their .value for storage
                if k == "status" and isinstance(v, GoalStatus):
                    v = v.value
                if k == "priority" and isinstance(v, GoalPriority):
                    v = v.value
                raw[k] = v

        raw["updated_at"] = datetime.now(timezone.utc).isoformat()
        goals[goal_id] = raw
        self._write_goals(goals)
        return Goal.from_dict(raw)

    def complete_step(self, goal_id: str, step_id: str) -> Optional[Goal]:
        """Mark a single step as done."""
        goal = self.get(goal_id)
        if goal is None:
            return None
        for step in goal.steps:
            if step.get("id") == step_id:
                step["done"] = True
        return self.update(goal_id, steps=goal.steps)

    def add_step(
        self,
        goal_id: str,
        label: str,
        done: bool = False,
    ) -> Optional[Goal]:
        """Append a new step to a goal."""
        goal = self.get(goal_id)
        if goal is None:
            return None
        goal.steps.append({"id": str(uuid.uuid4()), "label": label, "done": done})
        return self.update(goal_id, steps=goal.steps)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def delete(self, goal_id: str) -> bool:
        """Hard delete. Returns True if deleted, False if not found."""
        goals = self._read_goals()
        if goal_id not in goals:
            return False
        del goals[goal_id]
        self._write_goals(goals)
        return True

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        all_goals = self.list_all()
        by_status: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        for g in all_goals:
            by_status[g.status.value] = by_status.get(g.status.value, 0) + 1
            by_priority[g.priority.value] = by_priority.get(g.priority.value, 0) + 1
        avg_progress = (
            sum(g.progress() for g in all_goals) / len(all_goals)
            if all_goals else 0.0
        )
        return {
            "total": len(all_goals),
            "by_status": by_status,
            "by_priority": by_priority,
            "avg_progress": round(avg_progress, 3),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

goal_store = GoalStore()
