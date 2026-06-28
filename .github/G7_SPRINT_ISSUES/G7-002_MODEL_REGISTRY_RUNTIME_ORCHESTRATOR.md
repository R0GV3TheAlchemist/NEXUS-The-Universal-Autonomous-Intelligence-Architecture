---
title: "[G-7] Model Registry & Runtime Orchestrator — Capability-Based Local Model Routing"
labels: ["enhancement", "ai-core", "sprint:G-7", "priority:high"]
---

## Overview

GAIA-OS currently couples its intelligence layer to specific model names and hardcoded endpoints. As GAIA grows — chat, code synthesis, long-context reasoning, vision, background summarization — this becomes brittle and wasteful. A small 3B parameter model is ideal for fast chat; a large code-specialized model is ideal for Dev Suite synthesis; a multimodal endpoint is needed for Vision Capture. Hardcoding prevents any of these from being used correctly.

The Model Registry and Runtime Orchestrator replaces model names with capability declarations. Each GAIA engine declares what capability it needs (`fast_chat`, `deep_reason`, `code_synthesis`, `vision`, `background`). The orchestrator resolves that to the best available local runtime at the moment of the request.

## Background & Motivation

Recent local AI desktop tooling (Ollama, LM Studio, vLLM-compatible servers) demonstrates that local inference is now a real capability plane, not a fallback. Multi-agent orchestration stacks commonly abstract model identity behind capability routing so the stack remains runtime-agnostic. GAIA-OS should adopt this pattern now, before model coupling becomes load-bearing across too many subsystems.

This also positions GAIA to:
- Add new local models without touching engine code.
- Fail over gracefully when a preferred runtime is unavailable.
- Benchmark and compare models without manual reconfiguration.
- Support sovereign, offline-first operation permanently.

## Architecture

```
core/
  models/
    __init__.py
    registry.py              # ModelRegistry — load, save, query by capability
    model_record.py          # Typed model metadata: id, endpoint, capabilities, benchmarks, health
    runtime_orchestrator.py  # resolve(capability, context) → ModelRecord + failover
    discovery.py             # Probe known local endpoints, populate registry
    benchmarker.py           # Measure latency and throughput for registered models
    health_monitor.py        # Background task: poll runtimes, update health state
    capability_map.py        # Canonical capability taxonomy (enum + descriptions)
```

### Capability taxonomy

```python
class ModelCapability(str, Enum):
    FAST_CHAT        = "fast_chat"        # Low-latency conversational
    DEEP_REASON      = "deep_reason"      # Extended reasoning, long context
    CODE_SYNTHESIS   = "code_synthesis"   # Code generation and review
    VISION           = "vision"           # Multimodal image+text
    BACKGROUND       = "background"       # Low-priority summarization, indexing
    TOOL_CALLING     = "tool_calling"     # Structured function call support
```

### ModelRecord schema

```python
@dataclass
class ModelRecord:
    model_id: str
    provider: str                        # "ollama" | "lmstudio" | "vllm" | "openai_compat"
    endpoint: str
    capabilities: list[ModelCapability]
    context_window: int
    supports_tools: bool
    benchmark: ModelBenchmark | None
    health: HealthState                  # HEALTHY | DEGRADED | UNAVAILABLE
    last_seen: datetime
```

### Persistence

The registry is persisted using the **Tauri Store plugin** on the app side (JSON-backed async key-value store) and as a Python-side JSON file in `$APPDATA/gaia/model_registry.json` for the core/sidecar context. The two views stay in sync via the Synergy Engine's state bus.

## Acceptance Criteria

- [ ] `core/models/registry.py` provides `register()`, `query(capability)`, `all()`, `remove()`, and `save()`/`load()` methods.
- [ ] `core/models/discovery.py` probes Ollama (`:11434`), LM Studio (`:1234`), and any user-configured endpoints on launch.
- [ ] `core/models/runtime_orchestrator.py` resolves a `ModelCapability` to a `ModelRecord` with a declared fallback chain.
- [ ] `core/models/health_monitor.py` polls registered models every 60 seconds and updates `HealthState`.
- [ ] Registry state persists across restarts.
- [ ] All existing GAIA engine model references are refactored to call `orchestrator.resolve(capability)` rather than naming a model.
- [ ] A new Ollama or LM Studio model is recognized within one discovery cycle (≤ 60 s) without code changes.
- [ ] When the preferred model for a capability is `UNAVAILABLE`, the orchestrator falls back to the next candidate and emits a `GAIAEvent.MODEL_FALLBACK` log entry.
- [ ] Unit and integration tests cover: discovery, resolution, failover, and health state transitions.

## Simulations / Tests to Define Success

- `tests/models/test_discovery_finds_ollama.py` — mock Ollama endpoint; confirms discovery registers models with correct capabilities.
- `tests/models/test_resolve_with_fallback.py` — mark primary model `UNAVAILABLE`; confirm fallback is selected.
- `tests/models/test_registry_persistence.py` — save registry, reload, confirm all records intact.
- `tests/models/test_capability_resolution_taxonomy.py` — each `ModelCapability` resolves to exactly one model in a seeded registry.

## Dependencies

- Tauri Store plugin (`@tauri-apps/plugin-store`) for app-side registry persistence
- Local runtimes: Ollama, LM Studio, vLLM (optional; discovery is graceful-fail)
- `core/logger.py` for `GAIAEvent.MODEL_FALLBACK`
- Synergy Engine (consumer of orchestrator outputs)

## Cross-References

- Sprint G-7: Sandbox Service (#G7-001), Synergy Orchestrator v2 (#G7-005)
- Sprint G-8: full routing policy engine expansion
- Tauri Store plugin docs: https://v2.tauri.app/plugin/store/

## Labels
`enhancement` `ai-core` `sprint:G-7` `priority:high`

## Priority
🔴 High — blocks Synergy Orchestrator v2 and all future multi-model GAIA capabilities.
