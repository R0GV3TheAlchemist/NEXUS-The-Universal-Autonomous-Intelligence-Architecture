# api/routes/numerology.py
# Numerology API — Vibrational Identity Engine
# Canon Ref: C160 — Numerology: Vibrational Identity Engine
#
# Endpoints:
#   POST   /numerology/chart              — compute or retrieve a full chart
#   GET    /numerology/chart/{chart_id}   — fetch a persisted chart by ID
#   GET    /numerology/user/{user_id}     — list charts for a user
#   DELETE /numerology/profile/{id}       — soft-delete a profile (C139)
#
# Mount in main.py:
#   from api.routes.numerology import router as numerology_router
#   app.include_router(numerology_router, prefix="/api/v1")

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from gaia.db.session import get_db
from gaia.numerology.models import (
    NumerologyChart,
    NumerologyChartListResponse,
    NumerologyInput,
)
from gaia.numerology.service import NumerologyService

router = APIRouter(prefix="/numerology", tags=["numerology"])


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_numerology_service(db: AsyncSession = Depends(get_db)) -> NumerologyService:
    """Inject a NumerologyService bound to the current request's DB session."""
    return NumerologyService(db)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _orm_chart_to_schema(orm_chart, engine) -> NumerologyChart:
    """Convert a NumerologyChart ORM row into the Pydantic response schema.

    Reads from raw_chart JSONB where possible (fast path); falls back to
    individual NumerologyNumber rows if JSONB is absent.
    personal_year_cycle is read directly from raw_chart JSONB.
    """
    raw = orm_chart.raw_chart or {}

    def _number_detail(position: str) -> dict:
        if position in raw:
            return raw[position]
        nr = orm_chart.get_number(position)
        if nr is None:
            return {"number_type": position, "raw_value": 0, "reduced_value": 0,
                    "is_master_number": False, "reduction_path": []}
        return {
            "number_type": nr.number_type,
            "raw_value": nr.raw_value,
            "reduced_value": nr.reduced_value,
            "is_master_number": nr.is_master_number,
            "reduction_path": nr.reduction_path,
            "archetype": None,
            "theme": None,
        }

    master_numbers = [
        v for v in (
            orm_chart.life_path if orm_chart.life_path_is_master else None,
            orm_chart.expression if orm_chart.expression_is_master else None,
            orm_chart.soul_urge if orm_chart.soul_urge_is_master else None,
        )
        if v is not None
    ]

    return NumerologyChart(
        chart_id=orm_chart.id,
        profile_id=orm_chart.profile_id,
        full_name=orm_chart.profile.full_name if orm_chart.profile else raw.get("full_name", ""),
        birth_date=orm_chart.profile.birth_date if orm_chart.profile else date.fromisoformat(raw.get("birth_date", "1900-01-01")),
        system=orm_chart.profile.system if orm_chart.profile else raw.get("system", "pythagorean"),
        life_path=_number_detail("life_path"),
        expression=_number_detail("expression"),
        soul_urge=_number_detail("soul_urge"),
        personality=_number_detail("personality"),
        birthday=_number_detail("birthday"),
        personal_year=_number_detail("personal_year"),
        computed_for_year=orm_chart.computed_for_year,
        # personal_year_cycle is stored as a list in raw_chart JSONB.
        # Default to [] so older charts (pre-improvement) don't break.
        personal_year_cycle=raw.get("personal_year_cycle", []),
        challenges=[_number_detail(c["number_type"]) for c in raw.get("challenges", [])],
        master_numbers_present=master_numbers,
    )


def _ephemeral_chart(computed) -> NumerologyChart:
    """Build a NumerologyChart response from a ChartResult without persisting."""
    from gaia.numerology.engine import ARCHETYPES

    def _nd(nr) -> dict:
        arc = ARCHETYPES.get(nr.reduced_value, (None, None))
        return {
            "number_type": nr.number_type,
            "raw_value": nr.raw_value,
            "reduced_value": nr.reduced_value,
            "is_master_number": nr.is_master_number,
            "reduction_path": nr.reduction_path,
            "archetype": arc[0],
            "theme": arc[1],
        }

    def _pye(entry) -> dict:
        """Convert a PersonalYearEntry dataclass to the Pydantic-compatible dict."""
        return {
            "year": entry.year,
            "reduced_value": entry.reduced_value,
            "is_master_number": entry.is_master_number,
            "archetype": entry.archetype,
            "theme": entry.theme,
        }

    master_numbers = [
        nr.reduced_value
        for nr in (
            computed.life_path,
            computed.expression,
            computed.soul_urge,
        )
        if nr.is_master_number
    ]

    return NumerologyChart(
        chart_id=None,
        profile_id=None,
        full_name=computed.full_name,
        birth_date=computed.birth_date,
        system=computed.system,
        life_path=_nd(computed.life_path),
        expression=_nd(computed.expression),
        soul_urge=_nd(computed.soul_urge),
        personality=_nd(computed.personality),
        birthday=_nd(computed.birthday),
        personal_year=_nd(computed.personal_year),
        computed_for_year=date.today().year,
        personal_year_cycle=[_pye(e) for e in computed.personal_year_cycle],
        challenges=[_nd(c) for c in computed.challenges],
        master_numbers_present=master_numbers,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/chart",
    response_model=NumerologyChart,
    status_code=status.HTTP_200_OK,
    summary="Compute or retrieve a full Pythagorean numerology chart",
    description=(
        "Accepts a birth name and date. Returns the five core numbers "
        "(Life Path, Expression, Soul Urge, Personality, Birthday), "
        "Personal Year, Personal Year Cycle, Challenge Numbers, and archetype "
        "labels for each. When user_id is provided the chart is persisted; "
        "otherwise it is ephemeral. Canon: C160."
    ),
)
async def generate_chart(
    inp: NumerologyInput,
    svc: NumerologyService = Depends(get_numerology_service),
) -> NumerologyChart:
    try:
        if inp.user_id is not None:
            # Persistent path — save to DB, passing cycle_years through.
            orm_chart = await svc.get_or_create_chart(
                full_name=inp.full_name,
                birth_date=inp.birth_date,
                user_id=inp.user_id,
                system=inp.system,
                force_recompute=inp.force_recompute,
                cycle_years=inp.cycle_years,
            )
            return _orm_chart_to_schema(orm_chart, None)
        else:
            # Ephemeral path — compute only, no DB write.
            from gaia.numerology.engine import NumerologyEngine
            engine = NumerologyEngine()
            computed = engine.compute(
                full_name=inp.full_name,
                birth_date=inp.birth_date,
                system=inp.system,
                cycle_years=inp.cycle_years,
            )
            return _ephemeral_chart(computed)
    except NotImplementedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
    "/chart/{chart_id}",
    response_model=NumerologyChart,
    summary="Fetch a persisted chart by ID",
)
async def get_chart(
    chart_id: UUID,
    svc: NumerologyService = Depends(get_numerology_service),
) -> NumerologyChart:
    orm_chart = await svc.get_chart_by_id(chart_id)
    if orm_chart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chart {chart_id} not found.")
    return _orm_chart_to_schema(orm_chart, None)


@router.get(
    "/user/{user_id}",
    response_model=NumerologyChartListResponse,
    summary="List numerology charts for a user",
)
async def get_user_charts(
    user_id: UUID,
    limit: int = Query(default=10, ge=1, le=50),
    svc: NumerologyService = Depends(get_numerology_service),
) -> NumerologyChartListResponse:
    orm_charts = await svc.get_charts_for_user(user_id=user_id, limit=limit)
    schemas = [_orm_chart_to_schema(c, None) for c in orm_charts]
    return NumerologyChartListResponse(
        charts=schemas,
        total=len(schemas),
        user_id=user_id,
    )


@router.delete(
    "/profile/{profile_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a numerology profile (C139 — Right to Be Forgotten)",
    description=(
        "Marks the profile and all associated charts as deleted. "
        "Pass ?hard=true only under an explicit Right to Be Forgotten request "
        "as per canon C139 — this permanently removes the row."
    ),
)
async def delete_profile(
    profile_id: UUID,
    hard: bool = Query(default=False, description="Hard-delete (permanent erasure). C139 use only."),
    svc: NumerologyService = Depends(get_numerology_service),
) -> JSONResponse:
    deleted = await svc.delete_profile(profile_id=profile_id, hard=hard)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Profile {profile_id} not found.")
    return JSONResponse({
        "ok": True,
        "profile_id": str(profile_id),
        "deletion_type": "hard" if hard else "soft",
    })
