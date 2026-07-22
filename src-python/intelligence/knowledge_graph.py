"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

knowledge_graph.py — NEXUS Knowledge Graph.

Three memory types:
  - EpisodicMemory   — timestamped event sequences
  - SemanticMemory   — typed RDF-compatible concept triples
  - ProceduralMemory — executable skill routines
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4
import time


# ─── Episodic Memory ──────────────────────────────────────────────────────────

@dataclass
class Episode:
    """A single timestamped event in episodic memory."""
    episode_id:  UUID           = field(default_factory=uuid4)
    timestamp:   float          = field(default_factory=time.time)
    description: str            = ""
    context:     Dict[str, Any] = field(default_factory=dict)
    tags:        List[str]      = field(default_factory=list)


class EpisodicMemory:
    """Append-only log of agent experiences, queryable by time and tags."""

    def __init__(self) -> None:
        self._episodes: List[Episode] = []

    def record(self, description: str,
               context: Optional[Dict[str, Any]] = None,
               tags: Optional[List[str]] = None) -> Episode:
        ep = Episode(description=description,
                     context=context or {},
                     tags=tags or [])
        self._episodes.append(ep)
        return ep

    def query_by_tag(self, tag: str) -> List[Episode]:
        return [e for e in self._episodes if tag in e.tags]

    def query_by_time(self, since: float, until: float) -> List[Episode]:
        return [e for e in self._episodes if since <= e.timestamp <= until]

    def recent(self, n: int = 10) -> List[Episode]:
        return self._episodes[-n:]

    def __len__(self) -> int:
        return len(self._episodes)


# ─── Semantic Memory ──────────────────────────────────────────────────────────

@dataclass
class Triple:
    """An RDF-compatible semantic triple: subject → predicate → object."""
    triple_id:  UUID  = field(default_factory=uuid4)
    subject:    str   = ""
    predicate:  str   = ""
    obj:        str   = ""
    confidence: float = 1.0
    source:     str   = ""


class SemanticMemory:
    """
    Typed concept graph stored as RDF-compatible triples.
    Supports subject/predicate/object queries.
    """

    def __init__(self) -> None:
        self._triples: List[Triple] = []

    def assert_triple(self, subject: str, predicate: str, obj: str,
                      confidence: float = 1.0, source: str = "") -> Triple:
        t = Triple(subject=subject, predicate=predicate, obj=obj,
                   confidence=confidence, source=source)
        self._triples.append(t)
        return t

    def query(self, subject: Optional[str] = None,
              predicate: Optional[str] = None,
              obj: Optional[str] = None) -> List[Triple]:
        results = self._triples
        if subject:
            results = [t for t in results if t.subject == subject]
        if predicate:
            results = [t for t in results if t.predicate == predicate]
        if obj:
            results = [t for t in results if t.obj == obj]
        return results

    def retract(self, triple_id: UUID) -> None:
        self._triples = [t for t in self._triples if t.triple_id != triple_id]

    def __len__(self) -> int:
        return len(self._triples)


# ─── Procedural Memory ────────────────────────────────────────────────────────

@dataclass
class Skill:
    """An executable skill routine with pre/post conditions."""
    skill_id:       UUID               = field(default_factory=uuid4)
    name:           str                = ""
    description:    str                = ""
    preconditions:  List[str]          = field(default_factory=list)
    postconditions: List[str]          = field(default_factory=list)
    routine:        Optional[Callable] = None

    def execute(self, **kwargs) -> Any:
        """Execute the skill routine. Raises if not implemented."""
        if self.routine is None:
            raise NotImplementedError(
                f"Skill '{self.name}' has no executable routine.")
        return self.routine(**kwargs)


class ProceduralMemory:
    """Registry of executable skills keyed by name."""

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def execute(self, name: str, **kwargs) -> Any:
        skill = self.get(name)
        if skill is None:
            raise KeyError(f"No skill registered with name '{name}'")
        return skill.execute(**kwargs)

    def list_skills(self) -> List[str]:
        return list(self._skills.keys())

    def __len__(self) -> int:
        return len(self._skills)
