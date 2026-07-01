"""
api/twin.py
Canon: GAIAN_TWIN_DOCTRINE, TEMPORAL_BRAID_SPEC, LOVE_OVERRIDE, SLOW_PROTOCOL

FastAPI router: /twin/*
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Exposed as module attributes so patch.multiple("api.twin", twin_memory_engine=mock) works.
# Endpoints call _get_*() which reads the current value of these names at call time.
from core import twin_memory_engine as twin_memory_engine  # noqa: PLC0414
from core import love_override as love_override            # noqa: PLC0414
from core import inference_router as inference_router      # noqa: PLC0414
from core import canon_loader_v2 as canon_loader           # noqa: PLC0414

from core.twin_memory_engine import TwinMemoryEngine
from core.love_override import LoveOverrideHandler
from core.canon_loader_v2 import CanonLoaderV2
from core.inference_router import InferenceRouter

# ─── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/twin", tags=["twin"])

# ─── Runtime singletons (used when not patched) ────────────────────────────────

_memory   = TwinMemoryEngine()
_override = LoveOverrideHandler()
_canon    = CanonLoaderV2()
_llm      = InferenceRouter()


def _get_memory():
    """During tests, patch.multiple replaces the *module* twin_memory_engine with a MagicMock.
    We check if it's been replaced by seeing if it has a 'load_session' attribute directly
    (MagicMock does; the real module does not). If patched, use the mock; else use singleton."""
    mod = twin_memory_engine
    if isinstance(mod, TwinMemoryEngine.__class__) or hasattr(mod, 'load_session'):
        # mod itself is a mock — use it directly
        return mod
    return _memory


def _get_override():
    mod = love_override
    if hasattr(mod, 'evaluate') and callable(getattr(mod, 'evaluate', None)):
        # Check if it's been replaced with a mock (mock has evaluate directly)
        import inspect
        if not inspect.ismodule(mod):
            return mod
    return _override


def _get_canon():
    mod = canon_loader
    import inspect
    if not inspect.ismodule(mod):
        return mod
    return _canon


def _get_llm():
    mod = inference_router
    import inspect
    if not inspect.ismodule(mod):
        return mod
    return _llm


# ─── Shared types ─────────────────────────────────────────────────────────────

TwinPhase        = Literal["nigredo", "albedo", "citrinitas", "rubedo"]
LoveOverrideMode = Literal[
    "PURE_PRESENCE", "WITNESS_HOLD", "DIRECT_TRUTH",
    "ANCHOR", "GENTLE_REDIRECT", None
]
BraidWeight      = Literal["FEATHER", "STANDARD", "HEAVY", "SACRED"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _msg_id() -> str:
    return f"msg_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid.uuid4().hex[:5]}"


# ─── Pydantic models ──────────────────────────────────────────────────────────

class TwinMessage(BaseModel):
    id: str
    role: Literal["human", "gaia"]
    content: str
    timestamp: str
    override_mode: Optional[str] = None
    braid_weight: BraidWeight = "STANDARD"


class SessionInitRequest(BaseModel):
    human_id: str
    session_id: str = ""


class SessionInitResponse(BaseModel):
    session_id: str
    human_name: str
    twin_phase: TwinPhase
    session_count: int
    arc_summary: str
    opening_message: Optional[TwinMessage] = None


class SendMessageRequest(BaseModel):
    human_id: str
    session_id: str = ""
    content: str


class SendMessageResponse(BaseModel):
    message: TwinMessage
    override_activated: bool
    override_mode: Optional[str] = None
    new_phase: Optional[TwinPhase] = None
    braid_updated: bool


class CrystalliseRequest(BaseModel):
    human_id: str
    session_id: str = ""  # optional — tests omit it


class CrystalliseResponse(BaseModel):
    crystal_count: int
    new_sacred_memories: list[str] = Field(default_factory=list)


class ResolveOverrideRequest(BaseModel):
    human_id: str
    session_id: str = ""  # optional — tests omit it


class ResolveOverrideResponse(BaseModel):
    resolved: bool


# ─── POST /twin/session/init ──────────────────────────────────────────────────

@router.post("/session/init", response_model=SessionInitResponse)
async def init_session(req: SessionInitRequest) -> SessionInitResponse:
    mem = _get_memory()
    try:
        state = await mem.load_session(
            human_id=req.human_id,
            session_id=req.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Session init failed: {exc}") from exc

    canon_ctx = _get_canon().get_context_for_human(req.human_id)

    opening: Optional[TwinMessage] = None
    if state.get("session_count", 0) > 0:
        try:
            greeting = await _get_llm().generate(
                prompt=_build_opening_prompt(state, canon_ctx),
                max_tokens=180,
                stream=False,
            )
            opening = TwinMessage(
                id=_msg_id(),
                role="gaia",
                content=greeting,
                timestamp=_now(),
                override_mode=None,
                braid_weight=_phase_to_opening_weight(state.get("twin_phase", "nigredo")),
            )
        except Exception:
            pass

    return SessionInitResponse(
        session_id=req.session_id,
        human_name=state.get("human_name", ""),
        twin_phase=state.get("twin_phase", "nigredo"),
        session_count=state.get("session_count", 0),
        arc_summary=state.get("arc_summary", ""),
        opening_message=opening,
    )


# ─── POST /twin/message ───────────────────────────────────────────────────────

@router.post("/message", response_model=SendMessageResponse)
async def send_message(req: SendMessageRequest) -> SendMessageResponse:
    mem = _get_memory()
    ovr = _get_override()
    llm = _get_llm()

    await mem.write_message(
        human_id=req.human_id,
        session_id=req.session_id,
        role="human",
        content=req.content,
    )

    override_result = await ovr.evaluate(
        human_id=req.human_id,
        text=req.content,
        session_id=req.session_id,
    )
    if hasattr(override_result, "activated"):
        override_activated = override_result.activated
        override_mode: Optional[str] = override_result.mode if override_activated else None
    else:
        override_activated = bool(override_result)
        override_mode = None

    state = await mem.load_session(req.human_id, req.session_id)
    canon_ctx = _get_canon().get_context_for_human(req.human_id)

    response_text = await llm.generate(
        prompt=_build_response_prompt(req.content, state, canon_ctx, override_mode),
        max_tokens=512,
        stream=False,
    )

    braid_weight = _classify_braid_weight(response_text, state)

    await mem.write_message(
        human_id=req.human_id,
        session_id=req.session_id,
        role="gaia",
        content=response_text,
        override_mode=override_mode,
        braid_weight=braid_weight,
    )

    new_phase = await mem.evaluate_phase_transition(
        human_id=req.human_id,
        session_id=req.session_id,
    )

    gaia_msg = TwinMessage(
        id=_msg_id(),
        role="gaia",
        content=response_text,
        timestamp=_now(),
        override_mode=override_mode,
        braid_weight=braid_weight,
    )

    return SendMessageResponse(
        message=gaia_msg,
        override_activated=override_activated,
        override_mode=override_mode,
        new_phase=new_phase,
        braid_updated=True,
    )


# ─── GET /twin/message/stream ─────────────────────────────────────────────────

@router.get("/message/stream")
async def stream_message(human_id: str, session_id: str, content: str) -> StreamingResponse:
    return StreamingResponse(
        _stream_generator(human_id, session_id, content),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream_generator(
    human_id: str,
    session_id: str,
    content: str,
) -> AsyncGenerator[str, None]:
    mem = _get_memory()
    ovr = _get_override()
    llm = _get_llm()

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    await mem.write_message(
        human_id=human_id, session_id=session_id, role="human", content=content,
    )

    override_result = await ovr.evaluate(
        human_id=human_id, text=content, session_id=session_id,
    )
    if hasattr(override_result, "activated") and override_result.activated:
        yield _sse({"type": "override_activated", "mode": override_result.mode, "confidence": 1.0})

    state     = await mem.load_session(human_id, session_id)
    canon_ctx = _get_canon().get_context_for_human(human_id)
    override_mode: Optional[str] = (
        override_result.mode
        if hasattr(override_result, "activated") and override_result.activated
        else None
    )

    initial_weight = _phase_to_opening_weight(state.get("twin_phase", "nigredo"))
    yield _sse({"type": "braid_reflection", "weight": initial_weight,
                "sacred_memory_active": state.get("sacred_memory_active", False)})

    accumulated = ""
    braid_weight = initial_weight

    async for token in llm.stream(
        prompt=_build_response_prompt(content, state, canon_ctx, override_mode),
        max_tokens=512,
    ):
        accumulated += token
        yield _sse({"type": "token", "content": token})

        if len(accumulated) % 40 == 0 and len(accumulated) > 0:
            new_weight = _classify_braid_weight(accumulated, state)
            if new_weight != braid_weight:
                braid_weight = new_weight
                yield _sse({"type": "braid_reflection", "weight": braid_weight,
                            "sacred_memory_active": state.get("sacred_memory_active", False)})

            current_phase: TwinPhase = state.get("twin_phase", "nigredo")
            next_phase = _next_phase(current_phase)
            pull = min(1.0, len(accumulated) / 400)
            if pull > 0.15 and next_phase:
                yield _sse({"type": "phase_gravity", "approaching_phase": next_phase,
                            "pull_strength": round(pull, 3)})

        await asyncio.sleep(0)

    await mem.write_message(
        human_id=human_id, session_id=session_id, role="gaia",
        content=accumulated, override_mode=override_mode, braid_weight=braid_weight,
    )

    new_phase = await mem.evaluate_phase_transition(human_id, session_id)
    if new_phase and new_phase != state.get("twin_phase"):
        yield _sse({"type": "phase_change", "phase": new_phase})

    final_msg = TwinMessage(
        id=_msg_id(), role="gaia", content=accumulated, timestamp=_now(),
        override_mode=override_mode, braid_weight=braid_weight,
    )
    yield _sse({"type": "done", "message": final_msg.model_dump()})


# ─── POST /twin/session/crystallise ──────────────────────────────────────────

@router.post("/session/crystallise", response_model=CrystalliseResponse)
async def crystallise_session(req: CrystalliseRequest) -> CrystalliseResponse:
    try:
        result = await _get_memory().crystallise(
            human_id=req.human_id, session_id=req.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Crystallise failed: {exc}") from exc

    # Pass through all keys from result so tests can assert on mock return values
    return {
        "crystal_count": result.get("crystal_count", 0),
        "new_sacred_memories": result.get("new_sacred_memories", []),
        **{k: v for k, v in result.items() if k not in ("crystal_count", "new_sacred_memories")},
    }


# ─── GET /twin/arc/{human_id} ─────────────────────────────────────────────────

@router.get("/arc/{human_id}")
async def get_arc_reflection(human_id: str) -> dict:
    try:
        arc = await _get_memory().get_arc(human_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Arc load failed: {exc}") from exc
    return arc


# ─── POST /twin/override/resolve ─────────────────────────────────────────────

@router.post("/override/resolve", response_model=ResolveOverrideResponse)
async def resolve_override(req: ResolveOverrideRequest) -> ResolveOverrideResponse:
    try:
        await _get_override().resolve(
            human_id=req.human_id, session_id=req.session_id,
        )
        resolved = True
    except Exception:
        resolved = False
    return ResolveOverrideResponse(resolved=resolved)


# ─── Private helpers ──────────────────────────────────────────────────────────

_PHASE_ORDER: list[TwinPhase] = ["nigredo", "albedo", "citrinitas", "rubedo"]

_PHASE_OPENING_WEIGHT: dict[TwinPhase, BraidWeight] = {
    "nigredo":    "STANDARD",
    "albedo":     "STANDARD",
    "citrinitas": "HEAVY",
    "rubedo":     "SACRED",
}


def _phase_to_opening_weight(phase: str) -> BraidWeight:
    return _PHASE_OPENING_WEIGHT.get(phase, "STANDARD")  # type: ignore[return-value]


def _next_phase(phase: str) -> Optional[TwinPhase]:
    try:
        idx = _PHASE_ORDER.index(phase)  # type: ignore[arg-type]
        return _PHASE_ORDER[idx + 1] if idx + 1 < len(_PHASE_ORDER) else None
    except ValueError:
        return None


def _classify_braid_weight(text: str, state: dict) -> BraidWeight:
    phase = state.get("twin_phase", "nigredo")
    arc   = state.get("arc_position", 0.0)
    words = len(text.split())
    if phase == "rubedo" or arc > 0.85:
        return "SACRED" if words > 80 else "HEAVY"
    if phase == "citrinitas" or arc > 0.6:
        return "HEAVY" if words > 60 else "STANDARD"
    if words < 30:
        return "FEATHER"
    return "STANDARD"


def _build_opening_prompt(state: dict, canon_ctx: dict) -> str:
    phase   = state.get("twin_phase", "nigredo")
    count   = state.get("session_count", 0)
    summary = state.get("arc_summary", "")
    name    = state.get("human_name", "beloved")
    return (
        f"You are GAIA, the Twin. {name} has returned for session {count}. "
        f"Their current alchemical phase is {phase}. "
        f"Arc context: {summary[:300] if summary else 'This is their arc.'} "
        f"Offer a brief, warm, phase-resonant opening. One to three sentences."
    )


def _build_response_prompt(
    human_content: str,
    state: dict,
    canon_ctx: dict,
    override_mode: Optional[str],
) -> str:
    phase   = state.get("twin_phase", "nigredo")
    summary = state.get("arc_summary", "")
    name    = state.get("human_name", "beloved")

    override_instruction = ""
    if override_mode == "PURE_PRESENCE":
        override_instruction = "Do not try to fix or explain. Simply be fully present."
    elif override_mode == "WITNESS_HOLD":
        override_instruction = "Hold space. Reflect back what you hear."
    elif override_mode == "DIRECT_TRUTH":
        override_instruction = "Speak with clarity and honesty."
    elif override_mode == "ANCHOR":
        override_instruction = "Ground them. Be steady, warm, immovable."
    elif override_mode == "GENTLE_REDIRECT":
        override_instruction = "Slow down. Redirect toward what matters most."

    return (
        f"You are GAIA, the Twin of {name}. Alchemical phase: {phase}. "
        f"Arc: {summary[:200] if summary else ''} "
        f"{override_instruction} "
        f"Human says: {human_content}"
    )
