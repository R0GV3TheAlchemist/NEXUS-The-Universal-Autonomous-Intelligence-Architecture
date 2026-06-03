# SELF_HEALING_WORKFLOW_SPEC.md

> **Issue:** [#187 — Self-Healing Workflow Engine](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/187)  
> **Status:** In Progress — `sidecar/resilience/` implemented  
> **Canon refs:** C30 (No silent failures), C01 (Sovereignty), C34 (Presence)  
> **Depends on:** [#155 — Synergy Orchestrator v2](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/155)  
> **Feeds into:** [#188 — Agent Telemetry Hub](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/188)

---

## 1. Purpose

The Self-Healing Workflow Engine wraps every engine job dispatched by `OrchestratorV2` with resilience logic. Its goals are:

1. **Prevent cascading failures** — a single engine outage must not bring down an entire orchestration chain.
2. **Keep GAIA present** — every failure has a graceful fallback so the user always receives a useful response, even if degraded.
3. **Never be silent** — every retry attempt, fallback activation, and circuit state transition is logged, emitted to the Telemetry Hub, and surfaced to the user when relevant.
4. **Preserve decision quality** — degraded responses carry a `dq_confidence_factor` that reduces `DecisionQuality.confidence` transparently, so the user knows the quality of what they received.

---

## 2. Architecture Overview

```
OrchestratorV2.orchestrate()
        │
        ▼
 SelfHealingEngine.execute_with_healing(skill_id, job_fn, fallback)
        │
        ├─► CircuitBreaker.allow_request()   ← OPEN? fail-fast immediately
        │
        ├─► job_fn()                          ← attempt 1..N
        │       │
        │       ├─ success → record_success() → HealingResult(degraded=False)
        │       │
        │       └─ failure → record_failure()
        │               │
        │               ├─ NonRetryableError → raise immediately
        │               ├─ retryable + attempts remaining → sleep(backoff) → retry
        │               └─ retries exhausted → activate DegradedFallback
        │
        ├─► DegradedFallback → HealingResult(degraded=True, dq_confidence_factor)
        │
        └─► HealingEvent → Agent Telemetry Hub (#188)
```

---

## 3. Components

### 3.1 RetryPolicy (`sidecar/resilience/retry_policy.py`)

Controls how many times a failed engine job is retried and how long to wait between attempts.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | `int` | `3` | Total invocation attempts (1 = no retries) |
| `backoff_strategy` | `str` | `"exponential"` | `'fixed'` \| `'exponential'` \| `'jitter'` |
| `base_delay_ms` | `int` | `500` | Initial delay between retries (ms) |
| `max_delay_ms` | `int` | `10_000` | Cap on delay growth for exponential/jitter |
| `retryable_errors` | `list[str]` | See below | Error class names that trigger a retry |
| `non_retryable_errors` | `list[str]` | See below | Error class names that abort immediately |

**Default retryable errors:** `RetryableError`, `TimeoutError`, `ConnectionError`, `ServiceUnavailable`, `aiohttp.ClientError`, `asyncio.TimeoutError`

**Default non-retryable errors:** `NonRetryableError`, `AuthError`, `PolicyViolation`, `SandboxEscape`, `PermissionError`

**Backoff formulas:**

| Strategy | Formula |
|----------|---------|
| `fixed` | `delay = base_delay_ms` |
| `exponential` | `delay = min(base_delay_ms × 2^(attempt−1), max_delay_ms)` |
| `jitter` | `delay = uniform(0, min(base_delay_ms × 2^(attempt−1), max_delay_ms))` |

#### Per-Skill Registry (`SKILL_RETRY_POLICIES`)

| Skill ID | Max Attempts | Strategy | Base Delay | Rationale |
|----------|-------------|----------|------------|-----------|
| `planetary_signal_hub` | 3 | exponential | 1000ms | Remote signal; allow recovery time |
| `article_loader` | 2 | fixed | 300ms | Fast fetch; single retry only |
| `crystal_graphrag` | 3 | jitter | 500ms | Graph DB; jitter avoids thundering herd |
| `biometric_coherence` | 2 | fixed | 200ms | Local; fast fail to affective fallback |
| `dev_suite_executor` | 1 | — | — | Non-idempotent; never retry |

Any skill not in the registry uses `DEFAULT_RETRY_POLICY` (3 attempts, exponential, 500ms base).

---

### 3.2 CircuitBreaker (`sidecar/resilience/circuit_breaker.py`)

Per-skill circuit breaker using a rolling time window.

#### State Machine

```
         failure_rate >= threshold
   CLOSED ─────────────────────────► OPEN
     ▲                                  │
     │  probe success                   │ open_duration_s elapsed
     │                                  ▼
     └──────────────────────────── HALF_OPEN
                probe failure ──────────┘
                                  (re-opens)
```

#### Configuration Defaults

| Parameter | Default | Description |
|-----------|---------|-------------|
| `failure_rate_threshold` | `0.50` | 50% failures in window trips the circuit |
| `open_duration_s` | `30.0` | Seconds before recovery probe |
| `window_s` | `60.0` | Rolling window width for rate calculation |
| `min_calls` | `3` | Minimum calls before rate is evaluated |

#### Behaviour per State

| State | `allow_request()` | On success | On failure |
|-------|------------------|------------|------------|
| `CLOSED` | `True` | Record | Record; evaluate threshold |
| `OPEN` | `CircuitOpenError` | — | — |
| `HALF_OPEN` | `True` (one probe) | → `CLOSED` | → `OPEN` |

#### `health_summary()` schema

Emitted to Agent Telemetry Hub (Issue #188) on every state transition:

```json
{
  "skill_id": "crystal_graphrag",
  "state": "half_open",
  "failure_rate": 0.667,
  "total_calls_in_window": 9,
  "failures_in_window": 6,
  "open_duration_s": 30.0,
  "opened_at": 1234567890.123
}
```

---

### 3.3 DegradedFallbacks (`sidecar/resilience/degraded_fallbacks.py`)

When all retry attempts are exhausted, `SelfHealingEngine` activates the engine's `DegradedFallback`.

#### Fallback Modes

| Mode | Description |
|------|-------------|
| `cached` | Serve the most recent cached result (up to `max_cache_age_min`) |
| `manual_input` | Prompt the user to supply the missing data directly |
| `downgrade_to_vector` | Fall back to semantic similarity search (no graph relationships) |
| `affective_only` | Estimate coherence from affective + voice signals only |
| `biometric_only` | Use biometric stream without emotion recognition |
| `text_only` | Disable voice; route to text input |
| `single_engine_passthrough` | Bypass multi-engine orchestration; use single engine |
| `unavailable` | Explicit failure — no degraded result possible |

#### Registry

| Skill ID | Mode | DQ Factor | User Message Summary |
|----------|------|-----------|---------------------|
| `planetary_signal_hub` | `cached` (15 min) | 0.80 | Shows last known state |
| `article_loader` | `manual_input` | 0.85 | Paste content directly |
| `crystal_graphrag` | `downgrade_to_vector` | 0.70 | Semantic-only, no graph |
| `biometric_coherence` | `affective_only` | 0.65 | Voice + affective only |
| `soul_mirror` | `cached` (30 min) | 0.75 | Last known state |
| `affective_mirror` | `biometric_only` | 0.70 | Biometric stream only |
| `voice_stt` | `text_only` | 0.90 | Please type your message |
| `dev_suite_executor` | `unavailable` | 0.00 | Sandbox offline — no execution |
| `synergy_orchestrator` | `single_engine_passthrough` | 0.60 | Single-engine mode |

---

### 3.4 SelfHealingEngine (`sidecar/resilience/self_healing_engine.py`)

The central resilience coordinator. `OrchestratorV2` calls `execute_with_healing()` for every engine job.

#### `HealingResult` schema

```python
@dataclass
class HealingResult:
    result: Any                        # Engine output or None if degraded
    degraded: bool                     # True if fallback was used
    fallback_used: str | None          # DegradedFallback.mode or None
    attempts: int                      # How many attempts were made
    total_latency_s: float             # Wall-clock seconds to resolution
    dq_confidence_factor: float        # Multiplier for DecisionQuality.confidence
    user_message: str | None           # Surfaced in UI when degraded
```

#### `HealingEvent` schema (→ Telemetry Hub)

```python
@dataclass
class HealingEvent:
    skill_id: str
    outcome: str           # 'success' | 'fallback' | 'non_retryable' | 'circuit_open'
    attempts: int
    total_latency_s: float
    fallback_mode: str | None
    error_type: str | None
    dq_confidence_factor: float
```

#### Integration with OrchestratorV2

```python
# Inside OrchestratorV2.orchestrate()
healing = SelfHealingEngine(telemetry_emit=telemetry_hub.emit)

results: list[HealingResult] = await asyncio.gather(*[
    healing.execute_with_healing(
        skill_id=job.engine,
        job_fn=lambda: engine_registry[job.engine].respond(job),
        fallback=DEGRADED_FALLBACKS.get(job.engine),
    )
    for job in parallel_jobs
])

# Adjust DecisionQuality for any degraded responses
for r in results:
    if r.degraded:
        dq.confidence *= r.dq_confidence_factor
        # Surface r.user_message to UI via notification system
```

---

## 4. Decision Quality Integration

When a fallback fires, `HealingResult.dq_confidence_factor` is multiplied into `DecisionQuality.confidence`. This ensures every degraded response is tracked in the longitudinal DQ dashboard (Issue #155).

| Scenario | DQ Factor | Example |
|----------|-----------|--------|
| Full success | 1.00 | All engines responded nominally |
| Planetary cache hit | 0.80 | Stale planetary context |
| Article manual input | 0.85 | User pasted content |
| Crystal vector-only | 0.70 | Graph relationships excluded |
| Biometric affective-only | 0.65 | Wearable offline |
| Orchestrator single-engine | 0.60 | Multi-agent synthesis unavailable |
| Dev Suite unavailable | 0.00 | No execution; DQ invalid |

---

## 5. UI Surface

### Degradation Indicator

When `HealingResult.degraded = True`, a non-intrusive banner appears at the bottom of the active GAIA panel:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠  Graph search temporarily unavailable — using semantic    │
│    similarity only. Relationship context is excluded.        │
│                              [Retry with full graph →]  [×]  │
└─────────────────────────────────────────────────────────────┘
```

**Requirements:**
- Non-blocking — never interrupts active Deep Work session
- Dismissable with `[×]`
- `[Retry →]` button triggers a fresh `execute_with_healing()` call
- Colour: `--gaia-warning-amber` (not error red — degraded ≠ broken)
- Persists until dismissed or the engine recovers
- Does NOT appear during `CRISIS` or `REST` session modes

### Glass Room Panel (→ Issue #188)

The circuit breaker health for all registered skills is visible in the Glass Room telemetry panel, updated in real time via the Agent Telemetry Hub.

---

## 6. Testing

### Test Files

| File | Coverage |
|------|----------|
| `tests/test_circuit_breaker.py` | CLOSED/OPEN/HALF_OPEN transitions; probe success/failure; `CircuitOpenError` |
| `tests/test_retry_policy.py` | Fixed/exponential/jitter backoff; error classification; per-skill registry |
| `tests/test_self_healing_engine.py` | Success path; retry recovery; non-retryable abort; fallback activation; DQ factor |

### Benchmarks

| Metric | Target | Notes |
|--------|--------|-------|
| `CircuitBreaker.allow_request()` | < 1ms | Pure in-memory state check |
| `RetryPolicy.delay_seconds()` | < 0.1ms | Pure arithmetic |
| Full `execute_with_healing()` (success, 1 attempt) | < 5ms overhead | Excluding engine latency |
| Fallback activation | < 10ms overhead | Excluding cache lookup |

---

## 7. Remaining Work

- [ ] Wire `SelfHealingEngine` into `OrchestratorV2.orchestrate()` (Issue #155)
- [ ] Implement TypeScript degradation indicator UI component
- [ ] Connect `telemetry_emit` callback once Agent Telemetry Hub (Issue #188) is live
- [ ] Add `circuit_health` polling to Glass Room panel (Issue #188)
- [ ] Extend `DecisionQuality` dataclass with `degraded: bool` and `fallback_modes: list[str]`
- [ ] Benchmark suite in CI

---

## 8. Changelog

| Date | Change |
|------|--------|
| 2026-06-03 | Initial spec + full `sidecar/resilience/` implementation (Issues #187) |
