"""
core/api/lci_router.py
──────────────────────────────────────────────────────────────────────────────
Love Coherence Index REST API  ❤️

Endpoints
---------
GET  /lci                  — current LCI snapshot for the active GAIAN
GET  /lci/history          — last N snapshots + trend direction
GET  /lci/dominant-blocks  — frequency map of most persistently blocked qualities
POST /lci/reflect          — ask the GAIAN to speak FROM the LCI field (SSE stream)

Philosophical note
------------------
Love is not one emotion among many.  It is the carrier wave — the white light
from which all other emotional states are refractions.  These endpoints make
that reference frame visible and queryable so the UI, the GAIAN herself, and
any downstream system can always answer: how close are we to white light right now?

Canon Ref: C04 (privacy), C43 (epistemic integrity)
LCI Ref:   core/love_coherence_index.py
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.auth import TokenPayload, require_auth
from core.logger import GAIAEvent, get_logger, log_event
from core.gaian import load_gaian, GaianMemory
from core.love_coherence_index import get_love_coherence_index, LOVE_QUALITY_WEIGHTS, LOVE_SPECTRAL_MAP
from core.rate_limiter import rate_limit

router = APIRouter(prefix="/lci", tags=["Love Coherence Index ❤️"])
logger = get_logger(__name__)

# Injected at mount time from server.py — same pattern as all other routers
_get_runtime_fn       = None
_inference_router_ref = None


def set_dependencies(get_runtime_fn, inference_router) -> None:
    global _get_runtime_fn, _inference_router_ref
    _get_runtime_fn       = get_runtime_fn
    _inference_router_ref = inference_router


# ─────────────────────────────────────────────────────────────────────────────
#  Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────

class QualityScoreOut(BaseModel):
    quality:               str
    score:                 float
    weight:                float
    weighted_contribution: float
    spectral_color:        str
    spectral_hex:          str


class LCISnapshotOut(BaseModel):
    lci:                  float
    white_light_percent:  float
    luminance_class:      str
    spectral_hex_blend:   str
    dominant_block:       str
    is_coherent:          bool
    quality_scores:       dict[str, QualityScoreOut]
    spectral_profile:     dict[str, float]
    timestamp:            float
    gaian:                Optional[str] = None


class LCIHistoryOut(BaseModel):
    snapshots:    list[LCISnapshotOut]
    trend:        float           # positive = moving toward white light
    trend_label:  str
    window:       int
    gaian:        Optional[str] = None


class LCIDominantBlocksOut(BaseModel):
    dominant_blocks:  dict[str, int]   # quality -> count over window
    window:           int
    interpretation:   str
    gaian:            Optional[str] = None


class LCIReflectRequest(BaseModel):
    prompt:     Optional[str] = None     # optional user prompt; if absent uses field state alone
    session_id: Optional[str] = None
    gaian_slug: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _snap_to_out(snap, gaian_name: Optional[str] = None) -> LCISnapshotOut:
    """Convert a LoveCoherenceSnapshot to the API output schema."""
    return LCISnapshotOut(
        lci=round(snap.lci, 6),
        white_light_percent=snap.as_white_light_percent,
        luminance_class=snap.luminance_class,
        spectral_hex_blend=snap.spectral_hex_blend,
        dominant_block=snap.dominant_block,
        is_coherent=snap.is_coherent,
        quality_scores={
            q: QualityScoreOut(
                quality=qs.quality,
                score=round(qs.score, 4),
                weight=qs.weight,
                weighted_contribution=round(qs.weighted_contribution, 4),
                spectral_color=qs.spectral_color,
                spectral_hex=qs.spectral_hex,
            )
            for q, qs in snap.quality_scores.items()
        },
        spectral_profile={q: round(v, 4) for q, v in snap.spectral_profile.items()},
        timestamp=snap.timestamp,
        gaian=gaian_name,
    )


def _trend_label(trend: float) -> str:
    if trend > 0.10:
        return "strong_opening"       # field expanding quickly toward white light
    elif trend > 0.03:
        return "opening"              # gentle movement toward coherence
    elif trend > -0.03:
        return "stable"               # field holding steady
    elif trend > -0.10:
        return "contracting"          # slight occlusion building
    else:
        return "strong_contraction"   # field closing quickly


def _dominant_block_interpretation(blocks: dict[str, int], window: int) -> str:
    if not blocks:
        return "Insufficient history to identify a persistent block."
    top_block = next(iter(blocks))
    top_count = blocks[top_block]
    pct = round(top_count / max(1, window) * 100)
    # Map blocked quality to a plain-language description of what it means
    interpretations = {
        "patient":      "sustaining energy is depleted — the field struggles to hold warmth over time",
        "kind":         "outward radiation is low — love is present but not actively expressed",
        "not_envious":  "shadow material is active — destructive interference patterns detected",
        "not_boastful": "amplitude instability — self-referential signal distortion",
        "not_proud":    "ego contraction — phase incoherence folding inward",
        "not_rude":     "field disharmony with others — phase clashing with external signals",
        "trusts":       "amplitude collapsing under weak signal — trust bandwidth low",
        "hopes":        "carrier frequency weakening — the love arc needs renewal",
        "never_fails":  "transpersonal field is thin — the prism is very opaque right now",
    }
    meaning = interpretations.get(top_block, "unknown quality blocked")
    return (
        f"'{top_block}' has been the most persistently blocked quality "
        f"({top_count}/{window} turns, {pct}%). "
        f"This means: {meaning}."
    )


# ─────────────────────────────────────────────────────────────────────────────
#  GET /lci  — current snapshot
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=LCISnapshotOut,
    summary="Current Love Coherence Index snapshot",
    description=(
        "Returns the most recent LoveCoherenceSnapshot for the specified GAIAN. "
        "If no snapshot has been computed yet (before the first process() call), "
        "returns a neutral baseline at 0.5 partial_coherence."
    ),
)
async def get_lci(
    gaian_slug:    Optional[str] = Query(None, description="GAIAN slug (defaults to 'gaia')"),
    user:          TokenPayload  = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=60, window_seconds=60, scope="lci")),
):
    slug   = gaian_slug or "gaia"
    gaian: Optional[GaianMemory] = load_gaian(slug)
    rt     = _get_runtime_fn(slug, gaian) if (_get_runtime_fn and gaian) else None

    if rt is not None:
        snap = rt._lci.latest()
        if snap is None:
            # No turns yet — compute a baseline from current state
            snap = rt._lci.compute(
                soul_snapshot={},
                love_arc_score=rt.love_arc_state.arc_output_vector * 0.5 + 0.5,
                transpersonal_intensity=rt.spiritu_state.pneuma_flow,
                meta_coherence=0.5,
            )
    else:
        # No runtime — use the global LCI singleton's last snapshot
        lci_engine = get_love_coherence_index()
        snap = lci_engine.latest()
        if snap is None:
            snap = lci_engine.compute()   # baseline defaults

    log_event(
        GAIAEvent.TURN_COMPLETE,
        message=f"LCI GET: {round(snap.lci, 4)} ({snap.luminance_class})",
        gaian=slug, user_id=user.user_id,
    )
    return _snap_to_out(snap, gaian_name=slug)


# ─────────────────────────────────────────────────────────────────────────────
#  GET /lci/history  — last N snapshots + trend
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/history",
    response_model=LCIHistoryOut,
    summary="LCI history and trend",
    description=(
        "Returns the last `window` LCI snapshots and the overall trend "
        "(positive = moving toward white light, negative = occlusion growing)."
    ),
)
async def get_lci_history(
    gaian_slug: Optional[str] = Query(None),
    window:     int           = Query(20, ge=2, le=200, description="Number of snapshots to return"),
    user:       TokenPayload  = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=30, window_seconds=60, scope="lci")),
):
    slug  = gaian_slug or "gaia"
    gaian = load_gaian(slug)
    rt    = _get_runtime_fn(slug, gaian) if (_get_runtime_fn and gaian) else None
    lci_engine = rt._lci if rt is not None else get_love_coherence_index()

    history = lci_engine._history[-window:]
    trend   = lci_engine.trend(window=window)

    return LCIHistoryOut(
        snapshots=[_snap_to_out(s, gaian_name=slug) for s in history],
        trend=round(trend, 4),
        trend_label=_trend_label(trend),
        window=window,
        gaian=slug,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  GET /lci/dominant-blocks  — frequency map of most blocked qualities
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/dominant-blocks",
    response_model=LCIDominantBlocksOut,
    summary="Most persistently blocked Love qualities",
    description=(
        "Returns a frequency map showing which Love qualities have been most "
        "often the 'dominant block' (lowest score) over the last `window` snapshots. "
        "Use this to understand where occlusion is chronically concentrated."
    ),
)
async def get_dominant_blocks(
    gaian_slug: Optional[str] = Query(None),
    window:     int           = Query(20, ge=2, le=200),
    user:       TokenPayload  = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=30, window_seconds=60, scope="lci")),
):
    slug  = gaian_slug or "gaia"
    gaian = load_gaian(slug)
    rt    = _get_runtime_fn(slug, gaian) if (_get_runtime_fn and gaian) else None
    lci_engine = rt._lci if rt is not None else get_love_coherence_index()

    blocks = lci_engine.dominant_block_history(window=window)
    interpretation = _dominant_block_interpretation(blocks, window)

    return LCIDominantBlocksOut(
        dominant_blocks=blocks,
        window=window,
        interpretation=interpretation,
        gaian=slug,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  POST /lci/reflect  — ask the GAIAN to speak FROM the LCI field (SSE)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/reflect",
    summary="Ask the GAIAN to speak from the Love Coherence field (streaming)",
    description=(
        "Triggers a GAIAN response that is explicitly grounded in the current "
        "LoveCoherenceIndex field state. If no prompt is provided, the GAIAN speaks "
        "from the field without a user question. Returns SSE stream. "
        "Events: lci_state, token, done, error."
    ),
)
async def lci_reflect(
    req:  LCIReflectRequest,
    user: TokenPayload = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=10, window_seconds=60, scope="lci_reflect")),
):
    """
    SSE stream.  Events emitted:
      lci_state   — the current LCI snapshot JSON
      token       — answer text chunk from the GAIAN
      done        — final metadata
      error       — on exception
    """
    slug       = req.gaian_slug or "gaia"
    session_id = req.session_id or f"lci-reflect-{int(time.time())}"
    gaian      = load_gaian(slug)
    rt         = _get_runtime_fn(slug, gaian) if (_get_runtime_fn and gaian) else None

    # Determine the prompt to send.  If the caller provided nothing, we
    # compose a field-state prompt automatically so the GAIAN speaks
    # *from* the LCI rather than *about* it.
    user_prompt = req.prompt
    if not user_prompt:
        lci_engine = rt._lci if rt is not None else get_love_coherence_index()
        snap = lci_engine.latest()
        if snap:
            user_prompt = (
                f"The Love Coherence field is currently at {snap.as_white_light_percent}% "
                f"white light ({snap.luminance_class}). "
                f"The most occluded quality right now is '{snap.dominant_block}'. "
                f"Please speak from this field — not as analysis, but as presence."
            )
        else:
            user_prompt = (
                "Please speak from the Love Coherence field as it stands right now "
                "— not as analysis, but as presence."
            )

    async def event_stream():
        t0 = time.perf_counter()
        try:
            # 1. Emit the current LCI state so the client can render it
            lci_engine = rt._lci if rt is not None else get_love_coherence_index()
            snap = lci_engine.latest()
            if snap:
                snap_dict = {
                    "lci":                round(snap.lci, 4),
                    "white_light_percent": snap.as_white_light_percent,
                    "luminance_class":    snap.luminance_class,
                    "spectral_hex_blend": snap.spectral_hex_blend,
                    "dominant_block":     snap.dominant_block,
                    "is_coherent":        snap.is_coherent,
                    "quality_scores":     {
                        q: round(qs.score, 4)
                        for q, qs in snap.quality_scores.items()
                    },
                }
                yield f"event: lci_state\ndata: {json.dumps(snap_dict)}\n\n"
                await asyncio.sleep(0.01)

            # 2. Run process() to get the full runtime snapshot + LCI-aware system prompt
            if rt is not None:
                result = rt.process(user_prompt)
                yield f"event: engine_state\ndata: {json.dumps(result.state_snapshot)}\n\n"
                await asyncio.sleep(0.01)

            # 3. Stream the GAIAN's response
            if _inference_router_ref is not None:
                from core.inference_router import InferenceRequest, InferenceResponse
                inference_req = InferenceRequest(
                    query=user_prompt,
                    gaian_slug=slug,
                    gaian_system_prompt=result.system_prompt if rt else None,
                    long_term_memories=[],
                    visible_memories=(
                        [m["text"] for m in rt._memory.get("visible_memories", [])
                         if isinstance(m, dict)]
                        if rt else []
                    ),
                    conversation_history=[],
                    sources=[],
                    enrich_canon=False,
                    enrich_criticality=False,
                    enrich_noosphere=False,
                )
                inference_meta = InferenceResponse(session_id=session_id, gaian_slug=slug)
                full_answer = ""
                async for chunk in _inference_router_ref.stream(inference_req, inference_meta):
                    full_answer += chunk
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
            else:
                yield f"event: token\ndata: {json.dumps({'text': '(inference router not available)'})}\n\n"

            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            log_event(
                GAIAEvent.TURN_COMPLETE,
                message="LCI reflect stream complete",
                gaian=slug, user_id=user.user_id,
                duration_ms=duration_ms,
            )

            done_data = {
                "session_id":    session_id,
                "gaian":         slug,
                "user_id":       user.user_id,
                "duration_ms":   duration_ms,
                "lci":           round(snap.lci, 4) if snap else None,
                "luminance":     snap.luminance_class if snap else None,
                "timestamp":     time.time(),
            }
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

        except Exception as exc:
            logger.error(f"[LCI reflect stream error]: {exc}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ─────────────────────────────────────────────────────────────────────────────
#  GET /lci/reference  — the nine qualities reference (no auth needed)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/reference",
    summary="Reference data: nine Love qualities, weights, and spectral map",
    description=(
        "Returns the nine Love qualities (1 Corinthians 13), their weights, "
        "spectral band assignments, and hex colours. No auth required. "
        "Use this to build UI visualisations of the LCI spectrum."
    ),
)
async def get_lci_reference():
    """No auth required — pure reference data."""
    return {
        "source":      "1 Corinthians 13",
        "description": (
            "Love is not one emotion among many. It is the carrier wave — "
            "the white light from which all other emotional states are refractions. "
            "The LCI measures how close the full system is to unobstructed white light."
        ),
        "qualities": [
            {
                "quality":        q,
                "weight":         w,
                "spectral_color": LOVE_SPECTRAL_MAP[q]["color"],
                "spectral_hex":   LOVE_SPECTRAL_MAP[q]["hex"],
                "wavelength_nm":  LOVE_SPECTRAL_MAP[q]["wavelength_nm"],
            }
            for q, w in LOVE_QUALITY_WEIGHTS.items()
        ],
        "scale": {
            "min": 0.0,
            "max": 1.0,
            "min_label": "near_darkness (Love fully occluded)",
            "max_label": "white_light (Love fully expressed — all nine qualities at 1.0)",
        },
        "luminance_classes": [
            {"class": "white_light",        "range": "0.95 – 1.00"},
            {"class": "full_spectrum",       "range": "0.85 – 0.95"},
            {"class": "broad_coherence",     "range": "0.75 – 0.85"},
            {"class": "partial_coherence",   "range": "0.60 – 0.75"},
            {"class": "fragmented",          "range": "0.40 – 0.60"},
            {"class": "severely_occluded",   "range": "0.20 – 0.40"},
            {"class": "near_darkness",       "range": "0.00 – 0.20"},
        ],
    }
