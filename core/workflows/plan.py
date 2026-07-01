"""Workflow plan model — describes a multi-step task as data.

Workflows are declarative: a Workflow is just a named list of steps,
each of which maps input keys to resolved values. This separation lets
plans be serialised, stored, inspected, and replanned without coupling
them to execution logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class InputSource(str, Enum):
    """Where a step input value comes from."""
    STATIC = "static"       # fixed value provided at plan time
    WORKFLOW = "workflow"   # from the top-level workflow inputs
    STEP = "step"           # from a previous step's output


@dataclass
class StepInput:
    """Declares how a single input parameter for a step is resolved.

    Examples:
        StepInput("query", InputSource.WORKFLOW, workflow_key="user_query")
        StepInput("text", InputSource.STEP, step_ref="fetch_page", output_key="content")
        StepInput("limit", InputSource.STATIC, static_value=5)
    """
    param_name: str
    source: InputSource = InputSource.STATIC
    static_value: Any = None
    workflow_key: Optional[str] = None
    step_ref: Optional[str] = None
    output_key: Optional[str] = None


@dataclass
class WorkflowStep:
    """A single step in a workflow plan.

    Attributes:
        step_id: Unique identifier within the workflow (used as output ref).
        skill_name: The registered skill to invoke.
        inputs: How each input parameter is resolved.
        halt_on_failure: If True, a failed step stops the entire workflow.
        description: Optional human-readable note for debugging.
    """
    step_id: str
    skill_name: str
    inputs: List[StepInput] = field(default_factory=list)
    halt_on_failure: bool = True
    description: str = ""


@dataclass
class Workflow:
    """An ordered multi-step task plan.

    Attributes:
        workflow_id: Unique identifier.
        name: Human-readable name.
        steps: Ordered list of WorkflowSteps.
        description: Purpose of the workflow.
        tags: Free-form labels.
    """
    workflow_id: str
    name: str
    steps: List[WorkflowStep] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def step_ids(self) -> List[str]:
        return [step.step_id for step in self.steps]

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
