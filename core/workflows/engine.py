"""Workflow Engine — executes a Workflow plan step by step.

The engine resolves each step's inputs from the declared sources (static
value, top-level workflow inputs, or a prior step's output), delegates
execution to the SkillExecutor, records the result, and either continues
or halts based on the step's halt_on_failure policy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional

from core.skills.executor import SkillExecutor, SkillResult
from core.workflows.plan import InputSource, Workflow, WorkflowStep


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"


@dataclass
class StepRun:
    step_id: str
    skill_name: str
    resolved_params: Dict[str, Any]
    result: SkillResult

    @property
    def ok(self) -> bool:
        return self.result.ok


@dataclass
class WorkflowRun:
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    step_runs: List[StepRun] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == WorkflowStatus.COMPLETED

    def output_of(self, step_id: str) -> Any:
        for sr in self.step_runs:
            if sr.step_id == step_id:
                return sr.result.output
        return None

    def summary(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "steps_total": len(self.step_runs),
            "steps_ok": sum(1 for sr in self.step_runs if sr.ok),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
        }


class WorkflowEngine:
    """Executes a Workflow plan using a SkillExecutor.

    Input resolution order per step:
      1. STATIC  — use the literal value from the plan.
      2. WORKFLOW — look up workflow_key in the top-level inputs.
      3. STEP     — take the output of a prior step (output_key selects
                    a key if the output is a dict, otherwise uses the
                    output directly).
    """

    def __init__(self, executor: SkillExecutor) -> None:
        self.executor = executor

    def run(
        self,
        workflow: Workflow,
        inputs: Mapping[str, Any] | None = None,
    ) -> WorkflowRun:
        inputs = dict(inputs or {})
        run = WorkflowRun(
            workflow_id=workflow.workflow_id,
            workflow_name=workflow.name,
            status=WorkflowStatus.RUNNING,
        )

        step_outputs: Dict[str, Any] = {}

        for step in workflow.steps:
            params = self._resolve_inputs(step, inputs, step_outputs)
            skill_result = self.executor.run(step.skill_name, params)
            step_run = StepRun(
                step_id=step.step_id,
                skill_name=step.skill_name,
                resolved_params=params,
                result=skill_result,
            )
            run.step_runs.append(step_run)
            step_outputs[step.step_id] = skill_result.output

            if not skill_result.ok and step.halt_on_failure:
                run.status = WorkflowStatus.HALTED
                run.error = f"Step '{step.step_id}' failed: {skill_result.error}"
                run.finished_at = datetime.now(timezone.utc).isoformat()
                return run

        run.status = WorkflowStatus.COMPLETED
        run.finished_at = datetime.now(timezone.utc).isoformat()
        return run

    @staticmethod
    def _resolve_inputs(
        step: WorkflowStep,
        workflow_inputs: Dict[str, Any],
        step_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {}
        for inp in step.inputs:
            if inp.source == InputSource.STATIC:
                resolved[inp.param_name] = inp.static_value
            elif inp.source == InputSource.WORKFLOW:
                key = inp.workflow_key or inp.param_name
                resolved[inp.param_name] = workflow_inputs.get(key)
            elif inp.source == InputSource.STEP:
                prior_output = step_outputs.get(inp.step_ref or "")
                if isinstance(prior_output, dict) and inp.output_key:
                    resolved[inp.param_name] = prior_output.get(inp.output_key)
                else:
                    resolved[inp.param_name] = prior_output
        return resolved
