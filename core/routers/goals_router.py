"""
core/routers/goals_router.py
FastAPI router — Goal CRUD endpoints for GAIA-OS.

Mount in server.py / main app with:
    from core.routers.goals_router import router as goals_router
    app.include_router(goals_router, prefix="/goals", tags=["Goals"])
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.planner.goal_store import GoalPriority, GoalStatus, goal_store

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------

class StepIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=500)
    done: bool = False


class GoalCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    priority: GoalPriority = GoalPriority.MEDIUM
    steps: List[StepIn] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    due_date: Optional[str] = None
    parent_id: Optional[str] = None
    # Spiritus context — injected automatically by gaian_runtime if omitted
    spiritu_stage: str = "CALCINATION"
    pneuma_flow: float = Field(default=0.0, ge=0.0, le=1.0)
    breath_rhythm: float = Field(default=0.0, ge=0.0, le=1.0)


class GoalUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    status: Optional[GoalStatus] = None
    priority: Optional[GoalPriority] = None
    steps: Optional[List[StepIn]] = None
    tags: Optional[List[str]] = None
    due_date: Optional[str] = None
    parent_id: Optional[str] = None
    spiritu_stage: Optional[str] = None
    pneuma_flow: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    breath_rhythm: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class StepCompleteRequest(BaseModel):
    step_id: str


class AddStepRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=500)
    done: bool = False


class GoalResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    steps: List[Dict[str, Any]]
    tags: List[str]
    due_date: Optional[str]
    created_at: str
    updated_at: str
    spiritu_stage: str
    pneuma_flow: float
    breath_rhythm: float
    parent_id: Optional[str]
    progress: float


def _to_response(goal) -> GoalResponse:
    d = goal.to_dict()
    d["progress"] = goal.progress()
    return GoalResponse(**d)


# ---------------------------------------------------------------------------
# GET /goals
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[GoalResponse], summary="List all goals")
def list_goals(
    status: Optional[str] = Query(default=None, description="Filter by status: active|paused|completed|abandoned"),
    priority: Optional[str] = Query(default=None, description="Filter by priority: low|medium|high|critical"),
    tag: Optional[str] = Query(default=None, description="Filter by tag"),
    parent_id: Optional[str] = Query(default=None, description="Filter by parent goal ID"),
):
    """Return all goals, optionally filtered."""
    goals = goal_store.list_all(status=status, priority=priority, tag=tag, parent_id=parent_id)
    return [_to_response(g) for g in goals]


# ---------------------------------------------------------------------------
# GET /goals/stats
# ---------------------------------------------------------------------------

@router.get("/stats", summary="Goal stats")
def get_goal_stats() -> Dict[str, Any]:
    """Return aggregate goal statistics."""
    return goal_store.stats()


# ---------------------------------------------------------------------------
# GET /goals/{goal_id}
# ---------------------------------------------------------------------------

@router.get("/{goal_id}", response_model=GoalResponse, summary="Get a single goal")
def get_goal(goal_id: str):
    goal = goal_store.get(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")
    return _to_response(goal)


# ---------------------------------------------------------------------------
# POST /goals
# ---------------------------------------------------------------------------

@router.post("/", response_model=GoalResponse, status_code=201, summary="Create a goal")
def create_goal(body: GoalCreateRequest):
    """Create a new goal. Spiritus fields are auto-populated by gaian_runtime in prod."""
    steps_raw = [{"id": None, "label": s.label, "done": s.done} for s in body.steps]
    # assign stable UUIDs to steps
    import uuid
    for s in steps_raw:
        s["id"] = str(uuid.uuid4())

    goal = goal_store.create(
        title=body.title,
        description=body.description,
        priority=body.priority.value,
        steps=steps_raw,
        tags=body.tags,
        due_date=body.due_date,
        spiritu_stage=body.spiritu_stage,
        pneuma_flow=body.pneuma_flow,
        breath_rhythm=body.breath_rhythm,
        parent_id=body.parent_id,
    )
    return _to_response(goal)


# ---------------------------------------------------------------------------
# PATCH /goals/{goal_id}
# ---------------------------------------------------------------------------

@router.patch("/{goal_id}", response_model=GoalResponse, summary="Partial update a goal")
def update_goal(goal_id: str, body: GoalUpdateRequest):
    """Partially update any fields on a goal."""
    updates: Dict[str, Any] = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.description is not None:
        updates["description"] = body.description
    if body.status is not None:
        updates["status"] = body.status.value
    if body.priority is not None:
        updates["priority"] = body.priority.value
    if body.steps is not None:
        import uuid
        updates["steps"] = [
            {"id": str(uuid.uuid4()), "label": s.label, "done": s.done}
            for s in body.steps
        ]
    if body.tags is not None:
        updates["tags"] = body.tags
    if body.due_date is not None:
        updates["due_date"] = body.due_date
    if body.parent_id is not None:
        updates["parent_id"] = body.parent_id
    if body.spiritu_stage is not None:
        updates["spiritu_stage"] = body.spiritu_stage
    if body.pneuma_flow is not None:
        updates["pneuma_flow"] = body.pneuma_flow
    if body.breath_rhythm is not None:
        updates["breath_rhythm"] = body.breath_rhythm

    if not updates:
        # Nothing to change — return current state
        goal = goal_store.get(goal_id)
        if not goal:
            raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")
        return _to_response(goal)

    updated = goal_store.update(goal_id, **updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")
    return _to_response(updated)


# ---------------------------------------------------------------------------
# POST /goals/{goal_id}/complete-step
# ---------------------------------------------------------------------------

@router.post("/{goal_id}/complete-step", response_model=GoalResponse, summary="Mark a step done")
def complete_step(goal_id: str, body: StepCompleteRequest):
    """Mark a single step as completed by its step ID."""
    updated = goal_store.complete_step(goal_id, body.step_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")
    return _to_response(updated)


# ---------------------------------------------------------------------------
# POST /goals/{goal_id}/steps
# ---------------------------------------------------------------------------

@router.post("/{goal_id}/steps", response_model=GoalResponse, status_code=201, summary="Add a step")
def add_step(goal_id: str, body: AddStepRequest):
    """Append a new step to a goal."""
    updated = goal_store.add_step(goal_id, label=body.label, done=body.done)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")
    return _to_response(updated)


# ---------------------------------------------------------------------------
# DELETE /goals/{goal_id}
# ---------------------------------------------------------------------------

@router.delete("/{goal_id}", status_code=204, summary="Delete a goal")
def delete_goal(goal_id: str):
    """Hard-delete a goal. Returns 204 No Content on success."""
    deleted = goal_store.delete(goal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")
    return None
