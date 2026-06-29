"""
test_inference_router.py — Sovereignty routing tests for GAIAInferenceRouter

ADR-0011: Cloud LLM providers are optional augmentation.
GAIA must remain fully functional on local resources alone.
Cloud failure must NEVER propagate to the caller.

Test coverage:
  1. Local-only mode (GAIA_ALLOW_CLOUD unset/0): cloud backends are never selected
  2. Cloud failure → automatic local fallback (never propagates)
  3. Ollama is selected as primary when available and cloud is disabled
  4. allow_cloud=True enables cloud backends when keys are present
  5. Backend health recovery window
  6. cloud_fallback_triggered flag is set correctly
  7. get_stats() sovereignty_mode reflects GAIA_ALLOW_CLOUD state
"""

import os
import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _reset_backend_health():
    """Reset backend health state between tests."""
    from core.inference_router import _BACKEND_HEALTH, _BACKEND_FAILURE_TS, InferenceBackend
    for b in InferenceBackend:
        _BACKEND_HEALTH[b] = True
    _BACKEND_FAILURE_TS.clear()


# ------------------------------------------------------------------ #
#  Test 1: Local-only mode — cloud never selected                     #
# ------------------------------------------------------------------ #

def test_probe_backend_local_only_no_cloud_key(monkeypatch):
    """With GAIA_ALLOW_CLOUD=0 and cloud keys present, Ollama must be selected."""
    monkeypatch.setenv("GAIA_ALLOW_CLOUD", "0")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:27b")
    _reset_backend_health()

    from core.inference_router import _probe_backend_availability, InferenceBackend
    backend = _probe_backend_availability("test query")
    assert backend == InferenceBackend.OLLAMA, (
        f"ADR-0011 VIOLATED: expected OLLAMA, got {backend}. "
        "Cloud must not be selected when GAIA_ALLOW_CLOUD=0."
    )


def test_probe_backend_local_only_env_unset(monkeypatch):
    """With GAIA_ALLOW_CLOUD unset (default), Ollama must be selected."""
    monkeypatch.delenv("GAIA_ALLOW_CLOUD", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:27b")
    _reset_backend_health()

    from core.inference_router import _probe_backend_availability, InferenceBackend
    backend = _probe_backend_availability("what is the weather")
    assert backend == InferenceBackend.OLLAMA, (
        f"ADR-0011 VIOLATED: expected OLLAMA, got {backend}. "
        "Default must be local-only."
    )


# ------------------------------------------------------------------ #
#  Test 2: Cloud failure → local fallback (core sovereignty test)     #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_cloud_failure_routes_to_ollama(monkeypatch):
    """ADR-0011 core test: Anthropic 503 → automatic Ollama fallback, no exception raised."""
    monkeypatch.setenv("GAIA_ALLOW_CLOUD", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:27b")
    _reset_backend_health()

    import httpx

    async def mock_anthropic_503(*args, **kwargs):
        raise httpx.HTTPStatusError(
            "503 Service Unavailable",
            request=MagicMock(),
            response=MagicMock(status_code=503),
        )

    async def mock_ollama_ok(*args, **kwargs):
        return "[LOCAL OLLAMA RESPONSE]"

    from core import inference_router
    with patch.object(inference_router, "_call_anthropic", side_effect=mock_anthropic_503), \
         patch.object(inference_router, "_call_ollama", side_effect=mock_ollama_ok):

        router = inference_router.GAIAInferenceRouter()
        result = await router.generate("test query", allow_cloud=True)

    assert "[LOCAL OLLAMA RESPONSE]" in result, (
        f"ADR-0011 VIOLATED: cloud failure was not caught and resolved locally. Got: {result!r}"
    )


@pytest.mark.asyncio
async def test_anthropic_political_restriction_routes_to_ollama(monkeypatch):
    """Simulate June 2026 Anthropic restriction: 403 Forbidden → Ollama fallback."""
    monkeypatch.setenv("GAIA_ALLOW_CLOUD", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-restricted")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:27b")
    _reset_backend_health()

    import httpx
    from core import inference_router

    async def mock_anthropic_403(*args, **kwargs):
        raise httpx.HTTPStatusError(
            "403 Forbidden — access restricted by policy",
            request=MagicMock(),
            response=MagicMock(status_code=403),
        )

    async def mock_ollama_ok(*args, **kwargs):
        return "[SOVEREIGNTY PRESERVED — LOCAL RESPONSE]"

    with patch.object(inference_router, "_call_anthropic", side_effect=mock_anthropic_403), \
         patch.object(inference_router, "_call_ollama", side_effect=mock_ollama_ok):

        router = inference_router.GAIAInferenceRouter()
        result = await router.generate("sensitive query", allow_cloud=True)

    assert "SOVEREIGNTY PRESERVED" in result, (
        f"ADR-0011 VIOLATED: political restriction was not handled. Got: {result!r}"
    )


# ------------------------------------------------------------------ #
#  Test 3: Ollama is primary when available and cloud disabled         #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_ollama_is_primary_local(monkeypatch):
    """Ollama must be called directly when cloud is disabled and Ollama is available."""
    monkeypatch.setenv("GAIA_ALLOW_CLOUD", "0")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:27b")
    _reset_backend_health()

    from core import inference_router
    ollama_called = []

    async def mock_ollama(prompt, system, max_tokens, fallback=False):
        ollama_called.append(True)
        return "[OLLAMA PRIMARY RESPONSE]"

    with patch.object(inference_router, "_call_ollama", side_effect=mock_ollama):
        router = inference_router.GAIAInferenceRouter()
        result = await router.generate("local query")

    assert ollama_called, "ADR-0011 VIOLATED: Ollama was not called as primary backend."
    assert "OLLAMA PRIMARY RESPONSE" in result


# ------------------------------------------------------------------ #
#  Test 4: allow_cloud=True enables cloud when keys present            #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_allow_cloud_true_selects_cloud(monkeypatch):
    """When allow_cloud=True and keys present, cloud backend is selected."""
    monkeypatch.setenv("GAIA_ALLOW_CLOUD", "0")  # env says local
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:27b")
    _reset_backend_health()

    from core.inference_router import _probe_backend_availability, InferenceBackend
    # Explicit allow_cloud=True overrides env
    backend = _probe_backend_availability("test", allow_cloud=True)
    assert backend == InferenceBackend.OPENAI, (
        f"Expected OPENAI when allow_cloud=True and key present, got {backend}"
    )


# ------------------------------------------------------------------ #
#  Test 5: Backend health recovery window                              #
# ------------------------------------------------------------------ #

def test_backend_health_recovery(monkeypatch):
    """Failed backend recovers after _BACKEND_RECOVERY_WINDOW seconds."""
    from core import inference_router
    from core.inference_router import InferenceBackend, _BACKEND_RECOVERY_WINDOW
    _reset_backend_health()

    inference_router._mark_backend_failed(InferenceBackend.ANTHROPIC)
    assert not inference_router._is_healthy(InferenceBackend.ANTHROPIC), \
        "Backend should be unhealthy immediately after failure."

    # Simulate time past recovery window
    inference_router._BACKEND_FAILURE_TS[InferenceBackend.ANTHROPIC] = (
        time.monotonic() - _BACKEND_RECOVERY_WINDOW - 1.0
    )
    assert inference_router._is_healthy(InferenceBackend.ANTHROPIC), \
        "Backend should recover after recovery window."


# ------------------------------------------------------------------ #
#  Test 6: cloud_fallback_triggered flag                               #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_cloud_fallback_triggered_flag(monkeypatch):
    """InferenceResponse.cloud_fallback_triggered must be True when cloud fails."""
    monkeypatch.setenv("GAIA_ALLOW_CLOUD", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:27b")
    _reset_backend_health()

    from core import inference_router
    from core.inference_router import InferenceRequest, InferenceResponse

    async def mock_synthesizer_cloud_fail(*args, **kwargs):
        provider = kwargs.get("provider", args[2] if len(args) > 2 else "")
        if provider == "anthropic":
            raise RuntimeError("Anthropic restricted")
        yield "[LOCAL FALLBACK]"

    response_meta = InferenceResponse()
    request = InferenceRequest(query="test", allow_cloud=True)

    with patch("core.synthesizer.stream_synthesis", side_effect=mock_synthesizer_cloud_fail):
        chunks = []
        async for chunk in inference_router.GAIAInferenceRouter()._stream_full(request, response_meta):
            chunks.append(chunk)

    assert response_meta.cloud_fallback_triggered, (
        "ADR-0011 VIOLATED: cloud_fallback_triggered must be True when cloud fails."
    )


# ------------------------------------------------------------------ #
#  Test 7: get_stats() sovereignty_mode                                #
# ------------------------------------------------------------------ #

def test_get_stats_sovereignty_mode_local(monkeypatch):
    monkeypatch.setenv("GAIA_ALLOW_CLOUD", "0")
    from core.inference_router import GAIAInferenceRouter
    router = GAIAInferenceRouter()
    stats = router.get_stats()
    assert stats["sovereignty_mode"] == "local_only"
    assert stats["cloud_allowed"] is False


def test_get_stats_sovereignty_mode_cloud(monkeypatch):
    monkeypatch.setenv("GAIA_ALLOW_CLOUD", "1")
    from core.inference_router import GAIAInferenceRouter
    router = GAIAInferenceRouter()
    stats = router.get_stats()
    assert stats["sovereignty_mode"] == "cloud_augmented"
    assert stats["cloud_allowed"] is True
