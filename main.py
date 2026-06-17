"""
GAIA Backend — FastAPI Entry Point
Runs on http://localhost:8008

Boot contract:
  - ALWAYS starts, even if optional subsystems are missing
  - Core Twin API (/twin/*) is always available
  - Optional routers log a warning and are skipped if their module is missing
  - Health endpoint reports per-subsystem readiness
"""

import sys
import os
import signal
import asyncio
import logging
import time
import httpx
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Path setup ────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    ROOT = sys._MEIPASS  # type: ignore[attr-defined]
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, ROOT)

_SRC_PYTHON = os.path.join(ROOT, "src-python")
if _SRC_PYTHON not in sys.path:
    sys.path.insert(0, _SRC_PYTHON)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger("gaia")

_START_TIME = time.time()
_SUBSYSTEM_STATUS: dict[str, bool] = {}  # populated during lifespan


# ── Safe import helper ────────────────────────────────────────────────────────

def _try_import(module_path: str, attr: str | None = None):
    """
    Import a module (and optionally an attribute from it) without crashing.
    Returns the module/attr on success, None on failure.
    Logs a WARNING so the operator knows what's missing.
    """
    try:
        import importlib
        mod = importlib.import_module(module_path)
        if attr:
            return getattr(mod, attr, None)
        return mod
    except Exception as exc:
        log.warning(f"[GAIA] Optional import skipped — {module_path}: {exc}")
        return None


# ── Core router imports (always required — crash if missing) ──────────────────

from api.twin import router as twin_router          # /twin/* — core product
from api.auth import router as auth_router          # /auth/*

# ── Optional router imports (safe — skipped if module missing) ────────────────

_zodiac_router         = _try_import("api.routers.zodiac", "router")
_llm_router            = _try_import("api.routers.llm", "router")
_gaian_router          = _try_import("api.routers.gaian", "router")
_memory_router         = _try_import("api.routers.memory", "router")
_alignment_router      = _try_import("api.routers.alignment", "router")
_pair_prog_router      = _try_import("api.routers.pair_programmer", "router")
_observability_router  = _try_import("api.routers.observability", "router")
_notifications_router  = _try_import("api.notifications", "router")
_atlas_router          = _try_import("api.atlas", "router")
_crypto_router         = _try_import("api.crypto", "router")
_safety_router         = _try_import("core.safety.router", "router")
_numerology_router     = _try_import("api.routes.numerology", "router")
_emrys_router          = _try_import("emrys_engine.router", "emrys_router")
_init_emrys            = _try_import("emrys_engine.router", "init_emrys_engine")

# ── Queue 4 — GAIAState + Talisman routers (optional, same safety pattern) ───
_gaia_state_router     = _try_import("api.gaia_state", "router")
_talisman_router       = _try_import("api.talisman", "router")


# ── Graceful shutdown ─────────────────────────────────────────────────────────

_shutdown_event = asyncio.Event()


def _signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name
    log.info(f"[GAIA] Received {sig_name} — initiating graceful shutdown…")
    _shutdown_event.set()


for _sig in (signal.SIGTERM, signal.SIGINT):
    try:
        signal.signal(_sig, _signal_handler)
    except (OSError, ValueError):
        pass


async def _flush_state() -> None:
    log.info("[GAIA] Flushing engine state…")
    state_dir = os.path.join(ROOT, "data")
    os.makedirs(state_dir, exist_ok=True)
    tombstone_path = os.path.join(state_dir, "last_shutdown.txt")
    try:
        import datetime
        with open(tombstone_path, "w") as f:
            f.write(datetime.datetime.utcnow().isoformat() + "Z\n")
        log.info(f"[GAIA] Tombstone written → {tombstone_path}")
    except Exception as e:
        log.warning(f"[GAIA] Could not write tombstone: {e}")
    log.info("[GAIA] Shutdown complete.")


# ── Ollama health probe ───────────────────────────────────────────────────────

OLLAMA_BASE        = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL       = os.environ.get("GAIA_MODEL", "llama3")
OLLAMA_TIMEOUT     = 10


async def _check_ollama() -> dict:
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            r = await client.get(f"{OLLAMA_BASE}/api/tags")
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            model_ready = any(m.startswith(OLLAMA_MODEL) for m in models)
            if not model_ready:
                return {"ready": False, "model": None,
                        "error": f"Model '{OLLAMA_MODEL}' not found. Available: {models}"}
            probe = await client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": "ping", "stream": False},
            )
            probe.raise_for_status()
            return {"ready": True, "model": OLLAMA_MODEL, "error": None}
    except httpx.ConnectError:
        return {"ready": False, "model": None, "error": "Ollama not reachable"}
    except httpx.TimeoutException:
        return {"ready": False, "model": None, "error": f"Ollama probe timed out after {OLLAMA_TIMEOUT}s"}
    except Exception as e:
        return {"ready": False, "model": None, "error": str(e)}


# ── FastAPI lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    log.info("[GAIA] ✨ Backend starting — port 8008")

    # Encryption
    try:
        from api.crypto import get_symmetric_key
        get_symmetric_key()
        _SUBSYSTEM_STATUS["encryption"] = True
        log.info("[GAIA] ✓ Encryption layer ready")
    except Exception as e:
        _SUBSYSTEM_STATUS["encryption"] = False
        log.warning(f"[GAIA] Encryption init skipped: {e}")

    # Runtime orchestrator
    try:
        from core.runtime import init_orchestrator
        init_orchestrator()
        _SUBSYSTEM_STATUS["orchestrator"] = True
        log.info("[GAIA] ✓ Runtime orchestrator ready")
    except Exception as e:
        _SUBSYSTEM_STATUS["orchestrator"] = False
        log.warning(f"[GAIA] Runtime orchestrator skipped: {e}")

    # Emrys L2 vibronic bridge
    try:
        if _init_emrys:
            _init_emrys()
            _SUBSYSTEM_STATUS["emrys"] = True
            log.info("[GAIA] ✓ Emrys L2 vibronic bridge ready")
        else:
            _SUBSYSTEM_STATUS["emrys"] = False
    except Exception as e:
        _SUBSYSTEM_STATUS["emrys"] = False
        log.warning(f"[GAIA] Emrys engine skipped: {e}")

    # Twin Memory Engine — warm-up
    try:
        from core.twin_memory_engine import TwinMemoryEngine
        _SUBSYSTEM_STATUS["twin_memory"] = True
        log.info("[GAIA] ✓ TwinMemoryEngine ready")
    except Exception as e:
        _SUBSYSTEM_STATUS["twin_memory"] = False
        log.warning(f"[GAIA] TwinMemoryEngine skipped: {e}")

    # Love Override Handler
    try:
        from core.love_override import get_override_handler
        get_override_handler()
        _SUBSYSTEM_STATUS["love_override"] = True
        log.info("[GAIA] ✓ Love Override Handler ready")
    except Exception as e:
        _SUBSYSTEM_STATUS["love_override"] = False
        log.warning(f"[GAIA] Love Override Handler skipped: {e}")

    # Inference Router
    try:
        from core.inference_router import get_router
        get_router()
        _SUBSYSTEM_STATUS["inference_router"] = True
        log.info("[GAIA] ✓ InferenceRouter ready")
    except Exception as e:
        _SUBSYSTEM_STATUS["inference_router"] = False
        log.warning(f"[GAIA] InferenceRouter skipped: {e}")

    # Zodiac Engine
    try:
        from core.zodiac_engine import get_zodiac_engine
        get_zodiac_engine()
        _SUBSYSTEM_STATUS["zodiac"] = True
        log.info("[GAIA] ✓ ZodiacEngine ready")
    except Exception as e:
        _SUBSYSTEM_STATUS["zodiac"] = False
        log.warning(f"[GAIA] ZodiacEngine skipped: {e}")

    # GAIAState + Talisman subsystems
    try:
        from gaia.core.state_store import get_state
        get_state()  # warm-up: initialises singleton
        _SUBSYSTEM_STATUS["gaia_state"] = True
        log.info("[GAIA] ✓ GAIAState ready")
    except Exception as e:
        _SUBSYSTEM_STATUS["gaia_state"] = False
        log.warning(f"[GAIA] GAIAState init skipped: {e}")

    try:
        from gaia.core.talisman_store import seed_default_talismans
        seed_default_talismans()
        _SUBSYSTEM_STATUS["talismans"] = True
        log.info("[GAIA] ✓ Talisman store seeded")
    except Exception as e:
        _SUBSYSTEM_STATUS["talismans"] = False
        log.warning(f"[GAIA] Talisman store skipped: {e}")

    routing_mode = os.environ.get("GAIA_ROUTING_MODE", "local-first")
    log.info(f"[GAIA] LLM routing mode: {routing_mode}")
    log.info("[GAIA] ✨ GAIA is alive. Twin API ready at /twin/*")

    yield

    await _flush_state()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GAIA Backend",
    description="Sovereign AI Companion — Python Core",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:1420",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Router registration (always-on) ───────────────────────────────────────────

app.include_router(auth_router)          # /auth/*
app.include_router(twin_router)          # /twin/* — core product


# ── Router registration (optional — only if import succeeded) ─────────────────

def _mount(router, prefix: str = "", tags: list | None = None, label: str = "") -> None:
    if router is None:
        log.debug(f"[GAIA] Skipping optional router: {label or prefix}")
        return
    kw: dict = {}
    if prefix:
        kw["prefix"] = prefix
    if tags:
        kw["tags"] = tags
    app.include_router(router, **kw)


_mount(_zodiac_router,         prefix="/api/zodiac",   tags=["Zodiac"],          label="zodiac")
_mount(_llm_router,            prefix="/api",                                     label="llm")
_mount(_gaian_router,          prefix="/api",                                     label="gaian")
_mount(_memory_router,         prefix="/api/memory",   tags=["Memory"],          label="memory")
_mount(_alignment_router,      prefix="/alignment",    tags=["Alignment"],       label="alignment")
_mount(_pair_prog_router,      prefix="/api",          tags=["Pair Programmer"], label="pair_programmer")
_mount(_observability_router,                                                     label="observability")
_mount(_notifications_router,                                                     label="notifications")
_mount(_atlas_router,                                                             label="atlas")
_mount(_crypto_router,                                                            label="crypto")
_mount(_safety_router,                                                            label="safety")
_mount(_numerology_router,     prefix="/api/v1",       tags=["Numerology"],      label="numerology")
_mount(_emrys_router,          prefix="/api/emrys",    tags=["Emrys"],           label="emrys")

# ── Queue 4 — GAIAState + Talisman (prefix already set on routers) ────────────
# api.gaia_state  → prefix /gaia/state  (set in router definition)
# api.talisman    → prefix /gaia/talismans (set in router definition)
_mount(_gaia_state_router,                             tags=["GAIAState"],       label="gaia_state")
_mount(_talisman_router,                               tags=["Talismans"],       label="talisman")


# ── Core endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    uptime = round(time.time() - _START_TIME, 1)
    ollama = await _check_ollama()

    core_ready = _SUBSYSTEM_STATUS.get("twin_memory", True)

    payload = {
        "status": "ok" if core_ready else "degraded",
        "service": "gaia-backend",
        "version": "0.1.0",
        "uptime": uptime,
        "routing_mode": os.environ.get("GAIA_ROUTING_MODE", "local-first"),
        "subsystems": _SUBSYSTEM_STATUS,
        "ollama": {
            "ready": ollama["ready"],
            "model": ollama["model"],
            "error": ollama["error"],
        },
        "llm_backends": {
            "openai":     bool(os.environ.get("OPENAI_API_KEY")),
            "anthropic":  bool(os.environ.get("ANTHROPIC_API_KEY")),
            "perplexity": bool(os.environ.get("PERPLEXITY_API_KEY")),
            "ollama":     ollama["ready"],
        },
    }

    status_code = 200 if core_ready else 503
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/api/state")
async def get_state():
    return {
        "soul_mirror": {"archetype": "seeker", "individuation_stage": 1},
        "shadow": {"flags": []},
        "attachment": {"style": "secure"},
        "coherence": 72,
        "solfeggio": {"frequency": 528, "chakra": "heart"},
        "subsystems": _SUBSYSTEM_STATUS,
    }


# ── Launch ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("GAIA_PORT", 8008))
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
        reload=False,
    )
