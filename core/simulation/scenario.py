"""
core/simulation/scenario.py

Scenario and ScenarioEngine — define, load, and execute simulation scenarios.

A Scenario is a declarative description of:
  - Which agents participate
  - What preconditions must hold
  - What the termination condition is
  - Optional deterministic seed
  - Metadata (id, name, tags, description)

ScenarioEngine manages scenario registration and lookup.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ScenarioStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    MAX_STEPS_REACHED = "max_steps_reached"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class Scenario:
    """
    Declarative simulation scenario definition.

    Attributes:
        scenario_id: Unique identifier (auto-generated if not provided)
        name:        Human-readable name
        description: Long-form description of the scenario
        agents:      List of agent definition dicts [{"id": str, "config": dict}]
        preconditions: Key/value pairs applied before the simulation starts
        termination_condition: Callable(states, step) -> bool. If None, runs to max_steps.
        seed:        Optional integer seed for deterministic RNG
        tags:        Optional list of string tags for filtering
        metadata:    Arbitrary metadata dict
    """

    name: str
    agents: List[Dict[str, Any]] = field(default_factory=list)
    preconditions: Dict[str, Any] = field(default_factory=dict)
    termination_condition: Optional[Callable[[Dict[str, Any], int], bool]] = None
    seed: Optional[int] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    scenario_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "agents": self.agents,
            "preconditions": self.preconditions,
            "seed": self.seed,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        return cls(
            scenario_id=data.get("scenario_id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description", ""),
            agents=data.get("agents", []),
            preconditions=data.get("preconditions", {}),
            seed=data.get("seed"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json_file(cls, path: Path | str) -> "Scenario":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))


@dataclass
class ScenarioResult:
    """
    The outcome of a completed simulation run.
    """

    scenario_id: str
    scenario_name: str
    status: ScenarioStatus = ScenarioStatus.PENDING
    duration_seconds: float = 0.0
    error: Optional[str] = None
    snapshots: List[Any] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == ScenarioStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "status": self.status.value,
            "passed": self.passed,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "metrics": self.metrics,
            "snapshot_count": len(self.snapshots),
        }


class ScenarioEngine:
    """
    Registry and executor for named simulation scenarios.

    Usage:
        engine = ScenarioEngine()
        engine.register(my_scenario)
        result = await engine.execute("my_scenario_name", runner=runner)
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Scenario] = {}

    def register(self, scenario: Scenario) -> None:
        """Register a scenario by name."""
        self._registry[scenario.name] = scenario

    def register_from_file(self, path: Path | str) -> Scenario:
        """Load a scenario from a JSON file and register it."""
        scenario = Scenario.from_json_file(path)
        self.register(scenario)
        return scenario

    def get(self, name: str) -> Optional[Scenario]:
        return self._registry.get(name)

    def list_scenarios(self) -> List[str]:
        return list(self._registry.keys())

    def filter_by_tag(self, tag: str) -> List[Scenario]:
        return [s for s in self._registry.values() if tag in s.tags]

    async def execute(
        self,
        name: str,
        runner: Any,  # SimulationRunner
    ) -> ScenarioResult:
        """Look up a scenario by name and run it through the provided runner."""
        scenario = self._registry.get(name)
        if scenario is None:
            raise KeyError(f"Scenario '{name}' not found in registry. "
                           f"Available: {self.list_scenarios()}")
        return await runner.run(scenario)
