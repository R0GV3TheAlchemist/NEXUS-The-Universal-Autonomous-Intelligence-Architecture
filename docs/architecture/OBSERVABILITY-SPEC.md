# Observability & Audit Layer — Architecture Spec
> Canon ref: C01, SOVEREIGNTY.md
> Issue: #231

## Overview
The Observability & Audit Layer is GAIA's internal nervous system for transparency. Every agent action, tool call, memory access, policy decision, and loop iteration produces a structured, searchable, Gaian-owned record. This layer makes GAIA debuggable, trustworthy, and continuously improvable.

## Core Principle
> "Transparency is not surveillance — it is sovereignty over your own system."

## Signal Types

| Signal Type | Granularity | Retention | Owner |
|-------------|-------------|-----------|-------|
| Action logs | Per tool call | 90 days | Gaian |
| Loop traces | Per agentic loop run | 30 days | Gaian |
| Memory access logs | Per recall/write | 90 days | Gaian |
| Policy decisions | Per approval/denial | 365 days | Gaian (immutable) |
| Performance telemetry | Per session | 30 days | Gaian |
| Error events | Per exception | 365 days | Gaian |

## Architecture

```
[Every GAIA Action]
        │
        ▼
[Log Interceptor Middleware]
        │
        ├──► [Structured Action Log] ──► [Log Store (local SQLite)]
        │
        ├──► [Trace Span] ──► [Trace Collector] ──► [Trace Store]
        │
        ├──► [Telemetry Event] ──► [Metrics Aggregator]
        │
        └──► [Audit Event (if policy-gated)] ──► [Immutable Audit Store]
                                                         │
                                              [Tamper-evident hash chain]
```

## Log Entry Schema

```json
{
  "id": "uuid",
  "timestamp": "ISO8601",
  "session_id": "string",
  "agent_id": "string",
  "action_type": "tool_call | memory_read | memory_write | loop_start | loop_end | policy_gate",
  "tool": "string | null",
  "input_summary": "string",
  "output_summary": "string",
  "duration_ms": 0,
  "trust_tier": 0,
  "policy_decision": "approved | denied | auto | null",
  "error": "string | null",
  "trace_id": "uuid"
}
```

## Trace Schema

```json
{
  "trace_id": "uuid",
  "goal": "string",
  "started_at": "ISO8601",
  "completed_at": "ISO8601",
  "iterations": 0,
  "outcome": "success | failure | halted | pending",
  "spans": [ { "span_id": "uuid", "action": "string", "duration_ms": 0 } ]
}
```

## Audit Chain
Every policy-gated or sensitive action writes to an **append-only audit log** where each entry includes a SHA-256 hash of the previous entry — creating a tamper-evident chain that Gaian can verify at any time.

## Implementation Plan

### Phase 1 — Structured Logging
- [ ] Log interceptor middleware wrapping all tool calls.
- [ ] Structured log entry schema implemented.
- [ ] Local SQLite log store with indexed queries.
- [ ] Log viewer in the GAIA UI (filterable by type, session, tool).

### Phase 2 — Tracing
- [ ] Trace collector linking multi-step loop spans.
- [ ] Trace viewer showing full execution path per goal.
- [ ] Performance metrics per tool and per loop cycle.

### Phase 3 — Audit Chain
- [ ] Immutable audit store for policy decisions.
- [ ] SHA-256 hash chain for tamper evidence.
- [ ] Export audit log to JSON on demand.
- [ ] Retention policy controls in Gaian settings.

## Files to Create
- `src/observability/logger.ts` — structured log writer.
- `src/observability/tracer.ts` — trace span collection.
- `src/observability/audit.ts` — immutable audit chain.
- `src/observability/telemetry.ts` — performance metrics aggregator.
- `src/observability/store.ts` — SQLite log and trace storage.
- `tests/observability/logger.test.ts` — unit tests.

## Privacy Rules
- No raw personal data in telemetry unless Gaian explicitly opts in.
- All logs are stored locally by default.
- Gaian can export, delete, or purge any log category on demand.
- Cloud telemetry (if ever added) requires explicit per-session consent.

## Dependencies
- Feeds: State Bench Harness (#214), Trust & Permission Policy Engine (#229).
- Depended on by: Agentic Loop (#228), RAG Layer (#218), every future feature.
