# Agent Telemetry Hub — Specification

**Issue:** #188  
**Status:** Implementation Complete  
**Canon:** C05 (Transparency) · C30 (No Silent Failures) · C01 (Sovereignty)  
**Sprint:** 2 · Tier 1 — Orchestration Core  

---

## Overview

The Agent Telemetry Hub is GAIA’s observability layer. Every agentic decision, skill invocation, degradation event, and conflict resolution is persisted to an append-only SQLite store, broadcast to Glass Room real-time subscribers, and — for YELLOW/RED events — indexed in the Crystal Knowledge Graph.

Without this layer, GAIA cannot answer: *Why did I get that response? Was anything degraded? How efficient is my orchestration over time?*

---

## Architecture

### TelemetryEvent Schema

```
src-python/telemetry/telemetry_event.py
```

Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | UUID | Globally unique event identifier |
| `source` | TelemetrySource | Which GAIA engine emitted this event |
| `event_type` | str | `success` / `retry` / `fallback_used` / `circuit_open` / `conflict_resolved` / ... |
| `risk_tier` | RiskTier | GREEN / YELLOW / RED |
| `trust_tier` | TrustTier | TRUSTED / SANDBOXED / UNTRUSTED |
| `degraded` | bool | Was a fallback used? |
| `conflict_detected` | bool | Was a conflict resolved? |
| `dq_score` | float | DecisionQuality score for this event |
| `latency_ms` | float | Wall-clock latency |
| `biometric_context` | str | Coherence label at event time |
| `planetary_context` | str | Schumann/Kp label at event time |
| `canon_refs` | list[str] | Which canons were triggered |

### TelemetryCollector

```
src-python/telemetry/telemetry_collector.py
```

- Append-only SQLite store at `~/.gaia/telemetry/events.db`
- WAL journal mode for concurrent reads
- Indexes on `timestamp`, `session_id`, `source`, `risk_tier`
- Auto-promotes risk tier: degraded → YELLOW, `SAFETY_ETHICAL_OVERRIDE` conflict → RED
- Crystal indexing for all YELLOW/RED events
- Glass Room real-time subscriber registry
- `export_session(session_id)` → JSON export (Canon C01)
- `delete_session(session_id)` → erasure (Canon C01 — right to erasure)

### Orchestration Efficiency Service

```
src-python/telemetry/orchestration_efficiency.py
```

**OE Formula:**

```
OE = (successful_tasks × avg_dq_score) / (avg_total_latency_s × avg_engine_count)
```

Higher OE = high quality delivered fast with fewer engines (minimal waste).

Four standard rolling windows: 1h / 24h / 7d / 30d.

Bottleneck detection: identifies the intent class with highest average latency.

---

## Event Sources

| Source | Events emitted |
|--------|----------------|
| `synergy_orchestrator` | `orchestration_complete`, `orchestration_failed` |
| `self_healing_engine` | `success`, `retry`, `exhausted`, `fallback_used`, `circuit_open`, `non_retryable_error` |
| `sandbox` | `skill_executed`, `sandbox_escape_attempt`, `skill_blocked` |
| `skill_trust` | `trust_verified`, `trust_denied`, `attestation_expired` |
| `action_gate` | `action_approved`, `action_blocked`, `risk_threshold_exceeded` |
| `planetary_hub` | `schumann_spike`, `kp_storm`, `feed_degraded` |
| `biometric_engine` | `coherence_shift`, `hrv_alert`, `hardware_offline` |
| `conflict_resolver` | `conflict_detected`, `conflict_resolved` (Issue #190) |

---

## Glass Room UI

The Glass Room panel renders three views:

1. **Live Stream** — real-time event feed; risk tier color-coded (GREEN/YELLOW/RED)
2. **Session Trace** — timeline of all events for the selected session; expandable
3. **OE Dashboard** — four OE windows (1h/24h/7d/30d) with trend sparklines and bottleneck hint
4. **Skill Health** — circuit breaker state for all registered skills

---

## Canon Compliance

| Canon | Requirement | Implementation |
|-------|-------------|----------------|
| C05 | Transparency | Every event persisted; Glass Room always accessible |
| C30 | No silent failures | `emit()` never raises; all degradation events are YELLOW+ |
| C01 | Sovereignty | `export_session()` + `delete_session()` always available |
| C50 | Action Gate | RED events surfaced immediately; may block downstream actions |
