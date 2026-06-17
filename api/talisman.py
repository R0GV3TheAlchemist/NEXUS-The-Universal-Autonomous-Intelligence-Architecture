"""
api/talisman.py

FastAPI router for Talisman Object v1.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gaia.core.talisman_store import (
    activate_talisman,
    create_talisman,
    deactivate_talisman,
    get_talisman,
    list_talismans,
    seed_default_talismans,
)

router = APIRouter(prefix="/gaia/talismans", tags=["Talismans"])
seed_default_talismans()


class TalismanCreateRequest(BaseModel):
    name: str
    purpose: str
    created_by: str = "Kyle Steen"
    coherence_delta: float = 0.05
    energy_delta: float = 0.02
    stress_delta: float = -0.05
    entropy_delta: float = -0.02
    notes: str = ""


@router.get("")
async def api_list_talismans():
    return [t.to_json() for t in list_talismans()]


@router.post("")
async def api_create_talisman(req: TalismanCreateRequest):
    talisman = create_talisman(
        name=req.name,
        purpose=req.purpose,
        created_by=req.created_by,
        coherence_delta=req.coherence_delta,
        energy_delta=req.energy_delta,
        stress_delta=req.stress_delta,
        entropy_delta=req.entropy_delta,
        notes=req.notes,
    )
    return talisman.to_json()


@router.post("/{talisman_id}/activate")
async def api_activate_talisman(talisman_id: str):
    talisman = get_talisman(talisman_id)
    if not talisman:
        raise HTTPException(status_code=404, detail="Talisman not found")
    talisman, decision = activate_talisman(talisman_id)
    return {
        "talisman": talisman.to_json(),
        "decision": {
            "new_state": decision.next_state.to_runtime_json(),
            "interventions": decision.interventions,
            "rationale": decision.rationale,
        },
    }


@router.post("/{talisman_id}/deactivate")
async def api_deactivate_talisman(talisman_id: str):
    talisman = get_talisman(talisman_id)
    if not talisman:
        raise HTTPException(status_code=404, detail="Talisman not found")
    return deactivate_talisman(talisman_id).to_json()
