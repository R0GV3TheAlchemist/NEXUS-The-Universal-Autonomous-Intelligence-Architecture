"""
GAIA LLM Router — Offline-First AI Routing

Upgraded in Issue #113 to support dual-model sovereign stack:
  - Qwen3.5-9B  → default chat, vision, code (fast, GPT-5-nano quality)
  - GLM-5.1     → long-horizon agentic tasks (sustained 8-hour autonomous work)

Routing priority is controlled by GAIA_ROUTING_MODE env var:
  local-first  (default) — try Ollama, fall back to cloud
  cloud-first             — try cloud, fall back to Ollama
  local-only              — Ollama only; raise if unavailable
  cloud-only              — cloud only; never touch Ollama

Model selection is controlled by GAIA_ROUTING_MODE + task type:
  CHAT, VISION, CODE      → GAIA_CHAT_MODEL   (default: qwen3.5:9b)
  AGENTIC, LONG_HORIZON   → GAIA_AGENT_MODEL  (default: glm-5.1)
  estimated_duration_minutes > 30 → auto-upgrade to AGENT_MODEL

All public functions are async and return a LLMResult dataclass so callers
always know which provider answered and whether GAIA was offline.

Callers MUST consume stream() with `async for`, not `await` — it is an
async generator and awaiting it will raise TypeError at runtime.
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Optional

import httpx

log = logging.getLogger("gaia.llm_router")


# ── Routing mode ─────────────────────────────────────────────────────────────

class RoutingMode(str, Enum):
    LOCAL_FIRST  = "local-first"
    CLOUD_FIRST  = "cloud-first"
    LOCAL_ONLY   = "local-only"
    CLOUD_ONLY   = "cloud-only"


class TaskType(str, Enum):
    """
    Describes the nature of the task being sent to the LLM.
    This drives model selection within the sovereign local stack.

    CHAT         → Qwen3.5-9B  (conversational, fast)
    VISION       → Qwen3.5-9B  (native multimodal — replaces LLaVA)
    CODE         → Qwen3.5-9B  (instruction-following, strong code bench)
    AGENTIC      → GLM-5.1     (multi-step tool use, long-horizon planning)
    LONG_HORIZON → GLM-5.1     (tasks estimated > 30 min duration)
    """
    CHAT         = "chat"
    VISION       = "vision"
    CODE         = "code"
    AGENTIC      = "agentic"
    LONG_HORIZON = "long_horizon"


# Duration threshold (minutes) above which we auto-upgrade to the agent model
LONG_HORIZON_THRESHOLD_MINUTES = int(
    os.environ.get("GAIA_LONG_HORIZON_THRESHOLD", "30")
)


def _routing_mode() -> RoutingMode:
    raw = os.environ.get("GAIA_ROUTING_MODE", "local-first").strip().lower()
    try:
        return RoutingMode(raw)
    except ValueError:
        log.warning(f"[llm_router] Unknown GAIA_ROUTING_MODE '{raw}', defaulting to local-first")
        return RoutingMode.LOCAL_FIRST


# ── Provider config ───────────────────────────────────────────────────────────

OLLAMA_BASE    = os.environ.get("OLLAMA_BASE_URL",       "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT",    "60"))

# ── Dual-model sovereign stack (Issue #113) ───────────────────────────────────
# GAIA_MODEL is preserved for backward-compat; if set it overrides both below.
_LEGACY_MODEL  = os.environ.get("GAIA_MODEL", "")

CHAT_MODEL     = _LEGACY_MODEL or os.environ.get("GAIA_CHAT_MODEL",   "qwen3.5:9b")
AGENT_MODEL    = _LEGACY_MODEL or os.environ.get("GAIA_AGENT_MODEL",  "glm-5.1")
VISION_MODEL   = _LEGACY_MODEL or os.environ.get("GAIA_VISION_MODEL", "qwen3.5:9b")

# Cloud fallbacks
OPENAI_MODEL   = os.environ.get("GAIA_OPENAI_MODEL",     "gpt-4o-mini")
ANTH_MODEL     = os.environ.get("GAIA_ANTHROPIC_MODEL",  "claude-3-haiku-20240307")

# Token cap — prevents runaway API costs
MAX_TOKENS = int(os.environ.get("GAIA_MAX_TOKENS", "2048"))


def _select_model(
    task_type: TaskType = TaskType.CHAT,
    estimated_duration_minutes: Optional[float] = None,
) -> str:
    """
    Select the appropriate local model based on task type and estimated duration.

    Rules:
      1. If estimated_duration_minutes > LONG_HORIZON_THRESHOLD → GLM-5.1
      2. AGENTIC or LONG_HORIZON task type → GLM-5.1
      3. VISION task → Qwen3.5-9B (native multimodal)
      4. Everything else → Qwen3.5-9B
    """
    if estimated_duration_minutes is not None:
        if estimated_duration_minutes > LONG_HORIZON_THRESHOLD_MINUTES:
            log.info(
                f"[llm_router] estimated_duration={estimated_duration_minutes}min "
                f"> threshold={LONG_HORIZON_THRESHOLD_MINUTES}min → upgrading to AGENT_MODEL ({AGENT_MODEL})"
            )
            return AGENT_MODEL

    if task_type in (TaskType.AGENTIC, TaskType.LONG_HORIZON):
        return AGENT_MODEL

    if task_type == TaskType.VISION:
        return VISION_MODEL

    return CHAT_MODEL


# ── Result type ───────────────────────────────────────────────────────────────

@dataclass
class LLMResult:
    text:        str
    provider:    str                    # "ollama" | "openai" | "anthropic"
    model:       str
    latency_ms:  int
    offline:     bool                   # True when served entirely locally
    task_type:   TaskType = TaskType.CHAT
    metadata:    dict = field(default_factory=dict)


# ── Local provider (Ollama) ───────────────────────────────────────────────────

async def _call_ollama(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    images: Optional[list[str]] = None,
) -> LLMResult:
    """
    Call local Ollama. Raises RuntimeError on any failure so the
    router can decide whether to fall back to cloud.

    Args:
        images: Optional list of base64-encoded image strings for vision tasks.
                Passed to Ollama's multimodal endpoint (Qwen3.5-9B supports this natively).
    """
    selected_model = model or CHAT_MODEL
    payload: dict = {"model": selected_model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    if images:
        payload["images"] = images  # Qwen3.5-9B native vision support

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            r = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
    except httpx.ConnectError as exc:
        raise RuntimeError(f"Ollama not reachable at {OLLAMA_BASE}") from exc
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"Ollama timed out after {OLLAMA_TIMEOUT}s") from exc
    except Exception as exc:
        raise RuntimeError(f"Ollama error: {exc}") from exc

    text = data.get("response") or data.get("output") or ""
    if not text:
        raise RuntimeError("Ollama returned an empty response")

    latency = int((time.monotonic() - t0) * 1000)
    return LLMResult(
        text=text,
        provider="ollama",
        model=selected_model,
        latency_ms=latency,
        offline=True,
        metadata={"eval_count": data.get("eval_count"), "done": data.get("done")},
    )


async def _stream_ollama(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    images: Optional[list[str]] = None,
) -> AsyncIterator[str]:
    """Yield text tokens from Ollama streaming endpoint."""
    import json as _json

    selected_model = model or CHAT_MODEL
    payload: dict = {"model": selected_model, "prompt": prompt, "stream": True}
    if system:
        payload["system"] = system
    if images:
        payload["images"] = images

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            async with client.stream("POST", f"{OLLAMA_BASE}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = _json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except _json.JSONDecodeError:
                        continue
    except httpx.ConnectError as exc:
        raise RuntimeError(f"Ollama not reachable: {exc}") from exc


# ── Cloud providers ───────────────────────────────────────────────────────────

async def _call_openai(
    prompt: str,
    system: Optional[str] = None,
) -> LLMResult:
    try:
        import openai as _openai
    except ImportError as exc:
        raise RuntimeError("openai package not installed") from exc

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t0 = time.monotonic()
    client = _openai.AsyncOpenAI()
    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
    )
    latency = int((time.monotonic() - t0) * 1000)

    return LLMResult(
        text=resp.choices[0].message.content or "",
        provider="openai",
        model=resp.model,
        latency_ms=latency,
        offline=False,
        metadata={"usage": resp.usage.model_dump() if resp.usage else {}},
    )


async def _call_anthropic(
    prompt: str,
    system: Optional[str] = None,
) -> LLMResult:
    try:
        import anthropic as _anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic package not installed") from exc

    t0 = time.monotonic()
    client = _anthropic.AsyncAnthropic()

    create_kwargs: dict = dict(
        model=ANTH_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    if system:
        create_kwargs["system"] = system

    resp = await client.messages.create(**create_kwargs)
    latency = int((time.monotonic() - t0) * 1000)

    text = resp.content[0].text if resp.content else ""
    return LLMResult(
        text=text,
        provider="anthropic",
        model=resp.model,
        latency_ms=latency,
        offline=False,
        metadata={"stop_reason": resp.stop_reason},
    )


async def _call_cloud(
    prompt: str,
    system: Optional[str] = None,
) -> LLMResult:
    """Try OpenAI first, then Anthropic. Raise if neither is configured."""
    errors: list[str] = []

    if os.environ.get("OPENAI_API_KEY"):
        try:
            return await _call_openai(prompt, system)
        except Exception as exc:
            errors.append(f"openai: {exc}")
            log.warning(f"[llm_router] OpenAI failed: {exc}")

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return await _call_anthropic(prompt, system)
        except Exception as exc:
            errors.append(f"anthropic: {exc}")
            log.warning(f"[llm_router] Anthropic failed: {exc}")

    raise RuntimeError(
        "No cloud provider available. "
        + ("Errors: " + "; ".join(errors) if errors else "No API keys configured.")
    )


# ── Public interface ──────────────────────────────────────────────────────────

async def generate(
    prompt: str,
    system: Optional[str] = None,
    task_type: TaskType = TaskType.CHAT,
    estimated_duration_minutes: Optional[float] = None,
    images: Optional[list[str]] = None,
) -> LLMResult:
    """
    Offline-first LLM call. Returns a LLMResult with full provenance.

    Args:
        prompt: User prompt text.
        system: Optional system prompt.
        task_type: TaskType enum — drives model selection (Qwen3.5-9B vs GLM-5.1).
        estimated_duration_minutes: If provided and > LONG_HORIZON_THRESHOLD (30min),
                                    auto-upgrades to GLM-5.1 regardless of task_type.
        images: Base64-encoded images for VISION tasks (Qwen3.5-9B handles natively).

    Routing logic:
      local-first  → Ollama (model-selected) → cloud
      cloud-first  → cloud → Ollama
      local-only   → Ollama only (error if unavailable)
      cloud-only   → cloud only (never tries Ollama)
    """
    mode = _routing_mode()
    selected_model = _select_model(task_type, estimated_duration_minutes)

    log.info(f"[llm_router] generate | task={task_type.value} | model={selected_model} | mode={mode.value}")

    if mode == RoutingMode.LOCAL_ONLY:
        result = await _call_ollama(prompt, system, model=selected_model, images=images)
        result.task_type = task_type
        log.info(f"[llm_router] local-only → {result.model} ({result.latency_ms}ms)")
        return result

    if mode == RoutingMode.CLOUD_ONLY:
        result = await _call_cloud(prompt, system)
        result.task_type = task_type
        log.info(f"[llm_router] cloud-only → {result.provider}/{result.model} ({result.latency_ms}ms)")
        return result

    if mode == RoutingMode.LOCAL_FIRST:
        try:
            result = await _call_ollama(prompt, system, model=selected_model, images=images)
            result.task_type = task_type
            log.info(f"[llm_router] local-first → {result.model} ({result.latency_ms}ms) [offline]")
            return result
        except RuntimeError as local_err:
            log.info(f"[llm_router] local-first: local unavailable ({local_err}), falling back to cloud")
        result = await _call_cloud(prompt, system)
        result.task_type = task_type
        log.info(f"[llm_router] local-first fallback → {result.provider}/{result.model} ({result.latency_ms}ms)")
        return result

    if mode == RoutingMode.CLOUD_FIRST:
        try:
            result = await _call_cloud(prompt, system)
            result.task_type = task_type
            log.info(f"[llm_router] cloud-first → {result.provider}/{result.model} ({result.latency_ms}ms)")
            return result
        except RuntimeError as cloud_err:
            log.info(f"[llm_router] cloud-first: cloud unavailable ({cloud_err}), falling back to Ollama")
        result = await _call_ollama(prompt, system, model=selected_model, images=images)
        result.task_type = task_type
        log.info(f"[llm_router] cloud-first fallback → {result.model} ({result.latency_ms}ms) [offline]")
        return result

    raise RuntimeError(f"Unsupported routing mode: {mode}")


async def stream(
    prompt: str,
    system: Optional[str] = None,
    task_type: TaskType = TaskType.CHAT,
    estimated_duration_minutes: Optional[float] = None,
    images: Optional[list[str]] = None,
) -> AsyncIterator[str]:
    """
    Streaming token generator.

    IMPORTANT: consume with `async for token in stream(...)` — NOT `await stream(...)`.
    Awaiting an async generator raises TypeError at runtime.

    Args:
        task_type: TaskType enum — drives model selection.
        estimated_duration_minutes: Auto-upgrades to GLM-5.1 if > 30min.
        images: Base64-encoded images for VISION tasks.
    """
    mode = _routing_mode()
    selected_model = _select_model(task_type, estimated_duration_minutes)

    log.info(f"[llm_router] stream | task={task_type.value} | model={selected_model} | mode={mode.value}")

    if mode == RoutingMode.CLOUD_ONLY:
        result = await _call_cloud(prompt, system)
        log.info(f"[llm_router] stream cloud-only → {result.provider}/{result.model}")
        for word in result.text.split(" "):
            yield word + " "
        return

    if mode == RoutingMode.CLOUD_FIRST:
        try:
            result = await _call_cloud(prompt, system)
            log.info(f"[llm_router] stream cloud-first → {result.provider}/{result.model}")
            for word in result.text.split(" "):
                yield word + " "
            return
        except RuntimeError as cloud_err:
            log.info(f"[llm_router] stream cloud-first: cloud unavailable ({cloud_err}), falling back to Ollama")
        async for token in _stream_ollama(prompt, system, model=selected_model, images=images):
            yield token
        return

    try:
        async for token in _stream_ollama(prompt, system, model=selected_model, images=images):
            yield token
        return
    except RuntimeError as local_err:
        if mode == RoutingMode.LOCAL_ONLY:
            raise
        log.info(f"[llm_router] stream local-first: local unavailable ({local_err}), falling back to cloud")

    result = await _call_cloud(prompt, system)
    log.info(f"[llm_router] stream local-first fallback → {result.provider}/{result.model}")
    for word in result.text.split(" "):
        yield word + " "


async def routing_status() -> dict:
    """
    Return the current routing configuration and live provider availability.
    Used by /api/llm/routing-status endpoint.
    """
    mode = _routing_mode()

    # Probe Ollama for both models
    async def _probe_model(model_name: str) -> tuple[bool, Optional[str]]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{OLLAMA_BASE}/api/tags")
                r.raise_for_status()
                tags = r.json()
                models = [m["name"] for m in tags.get("models", [])]
                ok = any(m.startswith(model_name.split(":")[0]) for m in models)
                if not ok:
                    return False, f"Model '{model_name}' not found. Available: {models}"
                return True, None
        except Exception as exc:
            return False, str(exc)

    chat_ok, chat_err = await _probe_model(CHAT_MODEL)
    agent_ok, agent_err = await _probe_model(AGENT_MODEL)
    sovereign = (chat_ok or agent_ok) and mode in {RoutingMode.LOCAL_FIRST, RoutingMode.LOCAL_ONLY}

    return {
        "routing_mode": mode.value,
        "sovereign": sovereign,
        "local_models": {
            "chat_model":   {"name": CHAT_MODEL,   "available": chat_ok,  "error": chat_err,  "tasks": ["chat", "vision", "code"]},
            "agent_model":  {"name": AGENT_MODEL,  "available": agent_ok, "error": agent_err, "tasks": ["agentic", "long_horizon"]},
            "vision_model": {"name": VISION_MODEL, "available": chat_ok,  "error": chat_err,  "tasks": ["vision"]},
            "long_horizon_threshold_minutes": LONG_HORIZON_THRESHOLD_MINUTES,
        },
        "ollama": {"base_url": OLLAMA_BASE},
        "cloud": {
            "openai":          bool(os.environ.get("OPENAI_API_KEY")),
            "anthropic":       bool(os.environ.get("ANTHROPIC_API_KEY")),
            "openai_model":    OPENAI_MODEL,
            "anthropic_model": ANTH_MODEL,
            "max_tokens":      MAX_TOKENS,
        },
    }
