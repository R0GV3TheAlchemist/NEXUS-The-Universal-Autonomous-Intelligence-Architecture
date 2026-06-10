# Self-Healing Workflow Engine — Specification

**Issue:** #187  
**Status:** Implemented (`src-python/resilience/`)  
**Canon:** C30 · C01 · C34  
**Last Updated:** 2026-06-10

---

## 1. Purpose

GAIA-OS orchestrates multi-engine, multi-step agentic workflows through the Synergy
Orchestrator. As workflow complexity grows — chaining Research Desk, Crystal GraphRAG,
Planetary Hub, Biometric Engine, and Dev Suite — a transient failure in any single engine
can silently cascade and abort an entire session.

This violates **Canon C30** (No silent failures) and erodes the Gaian's trust in GAIA as
an agentic partner.

The Self-Healing Workflow Engine is a dedicated resilience layer that sits between the
Synergy Orchestrator and every downstream skill. It provides:

- **Automatic retry** with configurable backoff strategy
- **Circuit breaking** to isolate persistently failing skills without crashing the workflow
- **Graceful degradation** via per-engine fallback strategies when all retries are exhausted
- **DQ confidence adjustment** so DecisionQuality scores honestly reflect degraded responses
- **Full telemetry emission** so every healing event is visible in the Agent Telemetry Hub

---

## 2. Module Structure

```
src-python/resilience/
  __init__.py               — Public surface: SelfHealingEngine, HealingResult, DEGRADED_FALLBACKS
  circuit_breaker.py        — CircuitBreaker 4-state machine
  retry_policy.py           — RetryPolicy with exponential/jitter backoff
  degraded_fallbacks.py     — Per-engine DegradedFallback registry
  self_healing_engine.py    — Orchestration loop binding all three components

specs/resilience/
  SELF_HEALING_WORKFLOW_SPEC.md  — This document

src-python/tests/
  test_resilience.py        — pytest suite covering all acceptance criteria
```

---

## 3. Component: RetryPolicy

**File:** `src-python/resilience/retry_policy.py`

### 3.1 Data Model

```python
@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_strategy: str = "exponential"   # "fixed" | "exponential" | "jitter"
    base_delay_ms: int = 500
    max_delay_ms: int = 10_000
    retryable_errors: list[str]             # e.g. TimeoutError, ConnectionError
    non_retryable_errors: list[str]         # e.g. AuthError, PolicyViolation, SandboxEscape
```

### 3.2 Backoff Calculation

| Strategy | Formula |
|---|---|
| `fixed` | `base_delay_ms` on every retry |
| `exponential` | `min(base_delay_ms × 2^(attempt-1), max_delay_ms)` |
| `jitter` | Exponential ± uniform(0, base_delay_ms) |

### 3.3 Per-Skill Policy Registry

`get_retry_policy(skill_id)` returns the registered policy for a skill, falling back to
the default `RetryPolicy()` if none is registered. Policies are registered at startup
via configuration — no code changes needed to add a new skill policy.

### 3.4 Error Classification

`RetryPolicy.is_retryable(error)` checks the error's class name (and MRO) against
`retryable_errors` and `non_retryable_errors`. Non-retryable errors bypass all retry
logic and propagate immediately as `NonRetryableError`.

---

## 4. Component: CircuitBreaker

**File:** `src-python/resilience/circuit_breaker.py`

### 4.1 States

```
CLOSED   → failure_rate ≥ threshold → OPEN
OPEN     → recovery probe due        → HALF_OPEN
HALF_OPEN → success                  → CLOSED
HALF_OPEN → failure                  → OPEN
OPEN     → force_close()             → COOLING
COOLING  → tick() × cooling_ticks   → CLOSED
```

| State | Behaviour |
|---|---|
| `CLOSED` | All calls pass through normally. Failure rate is tracked. |
| `OPEN` | All calls fail fast with `CircuitOpenError`. Downstream is protected. |
| `HALF_OPEN` | One probe call is allowed. Success → CLOSED; failure → OPEN again. |
| `COOLING` | Manual reset path. Countdown via `tick()` before returning to CLOSED. |

### 4.2 Configuration Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `failure_rate_threshold` | `0.5` | 50% failures in window → OPEN |
| `window_seconds` | `60` | Rolling window for failure rate calculation |
| `open_duration_seconds` | `30` | Wait before probing recovery (OPEN → HALF_OPEN) |
| `min_calls_in_window` | `4` | Minimum calls required before rate is evaluated |
| `cooling_ticks` | `5` | `tick()` calls needed to leave COOLING |

### 4.3 Health Snapshot

`CircuitBreaker.health` returns a dict suitable for direct emission to the Telemetry Hub:

```python
{
    "skill_id": str,
    "state": "CLOSED" | "OPEN" | "HALF_OPEN" | "COOLING",
    "failure_rate": float,         # 0.0–1.0 over rolling window
    "total_calls_in_window": int,
    "failures_in_window": int,
    "opened_at": float | None,     # monotonic timestamp
    "cooling_counter": int,
}
```

### 4.4 Thread / Async Safety

The `CircuitBreaker` is designed for use within a single async event loop. If cross-thread
access is required in a future deployment, wrap mutation paths with `asyncio.Lock`.

---

## 5. Component: DegradedFallbacks

**File:** `src-python/resilience/degraded_fallbacks.py`

### 5.1 FallbackMode Enum

| Mode | Behaviour |
|---|---|
| `CACHED` | Return last known cached value up to `max_cache_age_min` minutes old |
| `MANUAL_INPUT` | Surface a prompt asking the Gaian to provide input manually |
| `DOWNGRADE` | Switch to a simpler/cheaper capability (e.g. vector search instead of GraphRAG) |
| `AFFECTIVE_ONLY` | Use affective inference as a proxy when biometric data is unavailable |
| `SKIP` | Omit this engine from the response; reduce DQ confidence accordingly |
| `STATIC_RESPONSE` | Return a safe static payload (used when execution environments are offline) |

### 5.2 DegradedFallback Data Model

```python
@dataclass
class DegradedFallback:
    mode: FallbackMode
    user_message: str               # Always shown in UI. Never empty.
    max_cache_age_min: int | None   # CACHED mode only
    static_payload: Any | None      # STATIC_RESPONSE mode only
    dq_confidence_multiplier: float # Applied to DQ score (0.0–1.0)
    allow_retry: bool = True        # Show [Retry →] action in UI
```

### 5.3 Registered Fallbacks

| Skill ID | Mode | DQ Multiplier | User Message Summary |
|---|---|---|---|
| `planetary_signal_hub` | `CACHED` | 0.85 | Showing last known state (≤ 15 min) |
| `article_loader` | `MANUAL_INPUT` | 0.90 | Paste content directly |
| `crystal_graphrag` | `DOWNGRADE` | 0.70 | Semantic similarity only; no graph context |
| `biometric_coherence` | `AFFECTIVE_ONLY` | 0.80 | Coherence estimated from voice + affect |
| `soul_mirror` | `SKIP` | 0.75 | Responding analytically; attunement reduced |
| `dev_suite_executor` | `STATIC_RESPONSE` | 0.00 | Code preserved; execution unavailable |
| `dream_weaver` | `SKIP` | 0.90 | Entry queued locally; will sync on recovery |

### 5.4 Adding a New Fallback

Add an entry to `DEGRADED_FALLBACKS` in `degraded_fallbacks.py`. No changes to
`SelfHealingEngine` are required — the engine looks up the registry by `skill_id` at
runtime.

---

## 6. Component: SelfHealingEngine

**File:** `src-python/resilience/self_healing_engine.py`

### 6.1 Execution Flow

```
call execute_with_healing(skill_id, fn, *args)
  │
  ├─ get_retry_policy(skill_id)         → RetryPolicy
  ├─ get_breaker(skill_id)              → CircuitBreaker
  ├─ DEGRADED_FALLBACKS.get(skill_id)   → DegradedFallback | None
  │
  └─ for attempt in 1..max_attempts:
       │
       ├─ breaker.call(fn, *args)
       │    ├─ OPEN + probe not due → raise CircuitOpenError → break to fallback
       │    ├─ success → return HealingResult(degraded=False)
       │    └─ failure → is_retryable?
       │         ├─ yes + attempts left → sleep(backoff) → retry
       │         ├─ yes + exhausted → break to fallback
       │         └─ no → raise NonRetryableError immediately
       │
  └─ fallback available?
       ├─ yes → _apply_fallback() → return HealingResult(degraded=True, dq_multiplier)
       └─ no  → raise WorkflowFailure
```

### 6.2 HealingResult

```python
@dataclass
class HealingResult:
    result: Any                           # Payload from the skill or fallback
    degraded: bool                        # Was a fallback used?
    fallback_used: str | None             # FallbackMode value if degraded
    attempts: int                         # How many attempts were made
    total_duration_ms: float              # Wall-clock time including retries
    dq_confidence_multiplier: float       # Downstream DQ should multiply by this
    user_message: str | None              # Degradation message for UI surface layer
    skill_id: str
```

### 6.3 DQ Integration Contract

When a `HealingResult` with `degraded=True` is returned, the Synergy Orchestrator **must**
apply `dq_confidence_multiplier` to the affected engine's contribution to `DecisionQuality`:

```python
if result.degraded:
    dq.confidence *= result.dq_confidence_multiplier
    dq.degradation_reason = result.fallback_used
```

This is a **binding contract**. A degraded result that does not adjust DQ silently
misrepresents GAIA's confidence — a violation of Canon C30.

### 6.4 Telemetry Events

Every state transition emits a structured event to the Agent Telemetry Hub (Issue #188):

| `event_type` | Trigger |
|---|---|
| `success` | Skill responded successfully |
| `retry` | Retryable error; another attempt scheduled |
| `exhausted` | Final retry attempt failed |
| `non_retryable_error` | Error bypassed retry loop |
| `circuit_open` | CircuitOpenError raised; skipping to fallback |
| `fallback_used` | DegradedFallback applied |

Telemetry emission is **fire-and-forget** — a telemetry failure must never interrupt
the healing engine itself.

### 6.5 Health API

```python
engine.get_all_health()          # → list[dict]  — health of every registered breaker
engine.get_skill_health(skill_id) # → dict        — health of a single breaker
```

These are used by the Agent Telemetry Hub dashboard to surface circuit breaker state.

---

## 7. User-Facing Degradation UI Contract

Every `HealingResult` with `degraded=True` carries a `user_message`. The Synergy
Orchestrator / response layer **must** surface this to the Gaian. It must never be
silently swallowed.

### 7.1 Degradation Banner Format

```
┌─ GAIA Response ─────────────────────────────────┐
│  [Response content here…]                        │
│                                                   │
│  ⚠ [user_message from HealingResult]             │
│  [Retry →]  (shown when allow_retry=True)         │
└───────────────────────────────────────────────────┘
```

### 7.2 Rules

- Banner appears **inline** within the response, not as a modal or blocking dialog
- Banner is **dismissable** with a single tap/click
- **[Retry →]** triggers a fresh `execute_with_healing()` call for the affected skill
- Banner never appears on non-degraded results (`degraded=False`)
- Degradation banners are **logged as Crystal memory nodes** for session history

---

## 8. Orchestrator Integration Pattern

The Synergy Orchestrator wraps every parallel job with `execute_with_healing()`:

```python
# In OrchestratorV2.orchestrate():
results = await asyncio.gather(*[
    self.healing_engine.execute_with_healing(
        skill_id=job.engine,
        fn=job.callable,
        *job.args,
        **job.kwargs,
    )
    for job in parallel_jobs
])

for r in results:
    if r.degraded:
        dq.confidence *= r.dq_confidence_multiplier
        dq.degradation_reason = r.fallback_used
        response.degradation_notices.append(r.user_message)
```

The `SelfHealingEngine` instance is **shared across the orchestrator's lifetime** —
not instantiated per-request — so circuit breaker state persists correctly across calls.

---

## 9. Acceptance Criteria Checklist

| Criterion | Status |
|---|---|
| `RetryPolicy` model and per-skill policy registry | ✅ Implemented |
| `CircuitBreaker` with CLOSED/OPEN/HALF_OPEN/COOLING state machine | ✅ Implemented |
| `SelfHealingEngine` wrapping all Synergy Orchestrator job execution | ✅ Implemented |
| `DEGRADED_FALLBACKS` for all current GAIA engines (7 registered) | ✅ Implemented |
| DQ confidence adjustment when fallbacks are used | ✅ Implemented (contract defined §6.3) |
| User-facing degradation banner (never silent) | ⬜ UI layer pending (contract defined §7) |
| All healing events wired to Agent Telemetry Hub | ✅ Implemented (`_emit()`) |
| Health-check probing for HALF_OPEN recovery | ✅ Implemented (`_probe_recovery_due()`) |
| Synergy Orchestrator integration | ⬜ Pending (pattern defined §8) |
| `specs/resilience/SELF_HEALING_WORKFLOW_SPEC.md` | ✅ This document |
| `pytest` — circuit breaker transitions, retry backoff, fallback, DQ | ✅ `test_resilience.py` |

---

## 10. Canon References

| Canon | Principle | Application |
|---|---|---|
| **C30** | No silent failures | Every degradation surfaces `user_message` to the Gaian. Fallbacks are never invisible. |
| **C01** | Sovereignty | Gaian always has `[Retry →]` option. The healing engine suggests, never commands. |
| **C34** | Presence | GAIA remains functional and present in degraded conditions. It does not disappear when a skill fails. |

---

## 11. Related Issues

| Issue | Relationship |
|---|---|
| #155 — Synergy Orchestrator v2 | Healing engine integrates here (§8) |
| #188 — Agent Telemetry Hub | Receives all healing events via `_emit()` |
| #190 — OE Metric + Conflict Resolution | OE scores are affected by fallback events; `degraded_fraction` field |
| #162 — Crystal Knowledge Graph | Degradation notices logged as memory nodes |
| #153 — Biometric Engine | `biometric_coherence` fallback registered |
| #152 — Planetary Hub | `planetary_signal_hub` fallback registered |
| #157 — Research Desk | `article_loader` fallback registered |
