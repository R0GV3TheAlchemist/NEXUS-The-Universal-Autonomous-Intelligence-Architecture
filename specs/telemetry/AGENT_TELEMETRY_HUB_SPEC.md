# Agent Telemetry Hub — Specification

**Issue:** #188  
**Status:** Implemented  
**Priority:** 🔴 High  
**Canon:** C05 (Transparency), C30 (No silent failures), C01 (Sovereignty)

---

## Overview

The Agent Telemetry Hub is GAIA-OS's unified, sovereign, append-only observability plane. Every engine action, skill invocation, sandbox event, healing recovery, biometric context change, and planetary event emits a `TelemetryEvent` into a local SQLite store. The Glass Room UI consumes this stream in real time via Server-Sent Events (SSE).

No telemetry data ever leaves the device. The store is append-only by design — only the user can delete data (right to erasure, Canon C01).

---

## Architecture

```
src-python/telemetry/
├── __init__.py          — public exports
├── models.py            — TelemetryEvent, SkillHealthReport, OrchestrationEfficiency, DecisionQualityRecord
├── store.py             — TelemetryStore (append-only SQLite, ~/.gaia/telemetry.db)
├── collector.py         — TelemetryCollector (event bus, SSE broadcast, Crystal queue)
└── emit_points.py       — per-engine emit factories (emit_job_started, emit_healing_event, etc.)

api/telemetry_routes.py  — FastAPI routes (/telemetry/*)

src/components/GlassRoom/AgentTelemetryHub.vue  — Glass Room UI panel

tests/telemetry/test_telemetry_hub.py  — full pytest suite

specs/telemetry/AGENT_TELEMETRY_HUB_SPEC.md  — this document
```

---

## Data Model

### TelemetryEvent

| Field | Type | Description |
|---|---|---|
| `id` | `str` (UUID4) | Unique event identifier |
| `timestamp` | `datetime` | UTC time of event |
| `session_id` | `str` | GAIA session context |
| `source` | `str` | Emitting module (synergy_orchestrator, sandbox, healing, …) |
| `event_type` | `str` | job_started, job_completed, job_failed, fallback_used, circuit_broken, … |
| `skill_id` | `str?` | Which skill/engine |
| `trust_tier` | `str?` | sovereign, verified, community (from #150) |
| `intent_class` | `str?` | research, code, reflect, … |
| `risk_tier` | `str?` | GREEN, YELLOW, RED (from #52) |
| `input_summary` | `str` | Non-sensitive label only — never raw content |
| `output_summary` | `str` | Non-sensitive label only |
| `duration_ms` | `int` | Wall-clock execution time |
| `dq_score` | `float?` | DecisionQuality score if applicable |
| `degraded` | `bool` | True if a fallback was used |
| `fallback_mode` | `str?` | "cached", "downgrade_to_vector", "manual_input", … |
| `biometric_context` | `str?` | Label at event time: "high", "building", "stressed", "depleted" |
| `planetary_context` | `str?` | Label at event time: "quiet", "elevated", "storm", "kp_storm" |
| `canon_refs` | `list[str]` | Canon canons governing this event |
| `tags` | `list[str]` | Free tags (e.g. "engines:3") |

---

## Emit Points

Every GAIA module imports from `telemetry.emit_points` and calls the appropriate factory:

| Module | Factory | Trigger |
|---|---|---|
| Synergy Orchestrator (#155) | `emit_job_started`, `emit_job_completed`, `emit_job_failed` | Every orchestration job |
| Execution Sandbox (#154) | `emit_sandbox_event` | Sandbox start, violation, completion |
| Skill Trust (#150) | `emit_skill_invoked` | Every skill call |
| Self-Healing Engine (#187) | `emit_healing_event` | Every fallback activation |
| Action Gate (#52) | `emit_action_gate` | Every YELLOW/RED gate trigger |
| Biometric Engine (#153) | `emit_biometric_change` | Coherence label transitions |
| Planetary Signal Hub (#152) | `emit_planetary_change` | Kp/Schumann label transitions |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/telemetry/stream` | SSE live event stream (Glass Room) |
| `GET` | `/telemetry/session/{id}` | Full session trace |
| `GET` | `/telemetry/skill/{id}` | Skill health report |
| `GET` | `/telemetry/dq` | Recent DQ scores |
| `GET` | `/telemetry/oe` | Orchestration Efficiency metric |
| `GET` | `/telemetry/recent` | Last N events |
| `POST` | `/telemetry/export/{id}` | User session JSON download |
| `DELETE` | `/telemetry/range` | User-initiated deletion (right to erasure) |

---

## Glass Room UI

`AgentTelemetryHub.vue` renders three tabs:

1. **📊 Live Stream** — Real-time SSE event feed. RED/YELLOW risk events highlighted. FALLBACK badge on degraded responses.
2. **🔗 Skill Health** — Per-skill circuit state (CLOSED / HALF_OPEN / OPEN), error rate, avg latency, last failure time.
3. **🎯 DQ / OE** — Orchestration Efficiency summary card (OE score, avg DQ, task counts, degraded fraction). DQ score history list.

---

## Orchestration Efficiency (OE)

```
OE = (successful_tasks × avg_dq_score) / (avg_total_latency_s × avg_engine_count)
```

Higher OE = high quality delivered fast with fewer engines. Exposed via `/telemetry/oe?window=24h|7d|30d`.

OE data feeds Issue #190 (Conflict Resolution & OE-Driven Routing Optimization).

---

## Privacy Model

- `input_summary` / `output_summary` hold non-sensitive labels only — never raw user content or file contents.
- Biometric and emotional values stored as labels (e.g. `"stressed"`), never raw sensor values.
- SQLite file at `~/.gaia/telemetry.db` — local-only, never synced or transmitted.
- User can export any session trace as JSON (`POST /telemetry/export/{id}`).
- User can delete any time range (`DELETE /telemetry/range`) — right to erasure per Canon C01.

---

## Canon Compliance

| Canon | How this module satisfies it |
|---|---|
| C05 Transparency | Every agentic action is logged and inspectable. GAIA has nothing to hide. |
| C30 No silent failures | All failures, fallbacks, and degradations are captured — never swallowed. |
| C01 Sovereignty | Telemetry is local-only, append-only, user-deletable. No cloud, no sync. |

---

## Related Issues

- Receives events from: #155 (Synergy Orchestrator), #154 (Sandbox), #150 (Skill Trust), #52 (Action Gate), #187 (Self-Healing), #152 (Planetary), #153 (Biometric)
- Feeds into: #162 (Crystal — audit nodes for YELLOW/RED events), Glass Room (#103)
- Exposes: OE metric + DQ trends to #190 (Conflict Resolution & OE) and Soul Settings
- Extended by: #190 (OE-Driven Routing + Conflict logging)
