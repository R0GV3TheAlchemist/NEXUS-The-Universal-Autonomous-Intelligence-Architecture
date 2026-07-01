"""Skill Registry — definition and lookup of callable GAIA skills.

A Skill describes what GAIA can do: its name, category, parameters,
consent requirements, and the callable that executes it. The registry
maps names to Skill definitions and supports discovery queries.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence


class SkillCategory(str, Enum):
    MEMORY = "memory"
    RESEARCH = "research"
    COMMUNICATION = "communication"
    COMPUTATION = "computation"
    FILE = "file"
    CONNECTOR = "connector"
    SYNTHESIS = "synthesis"
    REFLECTION = "reflection"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class Skill:
    """A single callable capability unit.

    Attributes:
        name: Unique snake_case identifier.
        description: Human-readable one-liner shown in skill discovery.
        category: Logical grouping for routing and filtering.
        handler: The Python callable that performs the skill.
        required_params: Parameter names that must be present in the call.
        optional_params: Parameter names that may be present.
        requires_consent: Whether the action_gate must confirm before execution.
        is_async: Whether the handler is a coroutine.
        tags: Free-form labels for search and filter.
    """

    name: str
    description: str
    handler: Callable[..., Any]
    category: SkillCategory = SkillCategory.CUSTOM
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    requires_consent: bool = False
    is_async: bool = False
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.is_async = inspect.iscoroutinefunction(self.handler)

    def matches(self, query: str) -> bool:
        q = query.lower()
        return (
            q in self.name.lower()
            or q in self.description.lower()
            or any(q in tag.lower() for tag in self.tags)
        )


class SkillRegistry:
    """Central registry for all GAIA skills.

    Skills are registered by name and are retrieved for execution by
    the SkillExecutor or the agentic loop's tool-routing step.
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered.")
        self._skills[skill.name] = skill

    def register_many(self, skills: Sequence[Skill]) -> None:
        for skill in skills:
            self.register(skill)

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def require(self, name: str) -> Skill:
        skill = self.get(name)
        if skill is None:
            raise KeyError(f"Skill '{name}' is not registered.")
        return skill

    def list_all(self) -> List[Skill]:
        return list(self._skills.values())

    def list_by_category(self, category: SkillCategory) -> List[Skill]:
        return [s for s in self._skills.values() if s.category == category]

    def search(self, query: str) -> List[Skill]:
        return [s for s in self._skills.values() if s.matches(query)]

    def names(self) -> List[str]:
        return list(self._skills.keys())

    def stats(self) -> Dict[str, Any]:
        by_category: Dict[str, int] = {}
        for s in self._skills.values():
            by_category[s.category.value] = by_category.get(s.category.value, 0) + 1
        return {
            "total": len(self._skills),
            "by_category": by_category,
            "consent_required": sum(1 for s in self._skills.values() if s.requires_consent),
            "async_skills": sum(1 for s in self._skills.values() if s.is_async),
        }

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills
