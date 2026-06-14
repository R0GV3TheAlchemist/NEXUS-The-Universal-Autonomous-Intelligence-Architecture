from fastapi import APIRouter, HTTPException
from gaia.numerology.models import NumerologyInput, NumerologyChart
from gaia.numerology.service import NumerologyService

router = APIRouter(prefix="/numerology", tags=["numerology"])
_service = NumerologyService()


@router.post(
    "/chart",
    response_model=NumerologyChart,
    summary="Generate a full Pythagorean numerology chart",
)
async def generate_chart(inp: NumerologyInput) -> NumerologyChart:
    try:
        return _service.generate_chart(inp)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
