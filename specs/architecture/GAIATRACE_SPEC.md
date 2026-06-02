# GAIATRACE_SPEC — Structured Inference Tracing & Audit

**Sprint:** G-7  
**Issue:** [#171](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/171)  
**Canon Refs:** C01 (Sovereignty), C30 (No silent failures)  
**Status:** Implemented — `core/trace.py`

---

## Purpose

GAIATrace is GAIA's flight recorder. Every significant inference step — LLM calls, SynergyEngine computations, ActionGate decisions, TaskGraph node executions, memory reads/writes — is wrapped in a `GAIATrace` context manager that writes a structured JSON Line to `core/audit/`. This makes behavioral regressions reproducible and debuggable without grepping freeform logs.

---

## Module: `core/trace.py`

### `TraceEventType` (str, Enum)

First-class event types. Using `(str, Enum)` enables:
- mypy exhaustive matching
- JSON-serializable without extra conversion
- Comparison with plain strings in query filters

| Value | When emitted |
|---|---|
| `synergy_compute` | SynergyEngine.compute() entry/exit |
| `llm_inference` | Every LLM call site |
| `memory_recall` | MemoryRouter.search() |
| `memory_write` | MemoryRouter.write() / promote() |
| `action_gate_decision` | ActionGate._evaluate() |
| `task_node_exec` | TaskGraph._run_node() |
| `canon_load` | CanonGraph._build() / CanonLoader load |
| `stage_session` | Stage Engine ceremony start/end |
| `tool_call` | GAIAStateAdapter.to_synergy_params() and other tool boundaries |

### `TraceRecord` (dataclass)

| Field | Type | Notes |
|---|---|---|
| `trace_id` | `str` | UUID4 — unique per trace |
| `event` | `str` | `TraceEventType.value` |
| `gaian_id` | `str \| None` | Identifies the Gaian context |
| `correlation_id` | `str` | From `correlation_id_ctx`; links traces across a single request |
| `canon_refs` | `list[str]` | e.g. `["C01", "C32"]` |
| `started_at` | `str` | ISO-8601 UTC |
| `ended_at` | `str \| None` | ISO-8601 UTC; `None` if flush before exit |
| `latency_ms` | `float \| None` | Wall-clock duration |
| `inputs` | `dict` | Caller-supplied input summary |
| `outputs` | `dict` | Populated via `trace.record_output(...)` |
| `error` | `str \| None` | `"ExceptionType: message"` if an exception was raised |
| `meta` | `dict` | Extensible: model_id, temperature, node_version, etc. |

### `GAIATrace` (sync context manager)

```python
with GAIATrace(
    event=TraceEventType.SYNERGY_COMPUTE,
    gaian_id=gaian.id,
    canon_refs=["C32"],
    inputs={"dominant_hz": 528.0},
) as trace:
    reading, state = engine.compute(**params)
    trace.record_output({"synergy_factor": reading.synergy_factor})
```

**Guarantees:**
- Never suppresses exceptions (`__exit__` returns `False`).
- Records exception in `TraceRecord.error` before flushing.
- Flush failure is logged but never raises — tracing infra must not crash GAIA.

### `AsyncGAIATrace` (async context manager)

Drop-in replacement for `async with` blocks. Delegates flush to the synchronous `__exit__` — the flush is a file append and does not require awaiting.

```python
async with AsyncGAIATrace(
    event=TraceEventType.LLM_INFERENCE,
    gaian_id=gaian.id,
) as trace:
    response = await llm.complete(prompt)
    trace.record_output({"response_tokens": len(response.tokens)})
```

---

## Trace File Format

Files are written to `core/audit/traces_YYYYMMDD.jsonl` — one JSON object per line, daily rotation.

```jsonl
{"trace_id": "550e8400-e29b-41d4-a716-446655440000", "event": "synergy_compute", "gaian_id": "luna", "correlation_id": "req-abc123", "canon_refs": ["C32"], "started_at": "2026-06-02T14:00:00+00:00", "ended_at": "2026-06-02T14:00:00.043000+00:00", "latency_ms": 43.2, "inputs": {"dominant_hz": 528.0}, "outputs": {"synergy_factor": 0.87}, "error": null, "meta": {}}
```

**`.gitignore` rule:** `core/audit/*.jsonl` is gitignored at `core/audit/.gitignore`. The directory itself is tracked so it always exists on clone. Schema files (`.md`, `.json`, `.yaml`) remain tracked.

---

## Integration Points

### SynergyEngine (`core/synergy_engine.py`)
```python
with GAIATrace(
    event=TraceEventType.SYNERGY_COMPUTE,
    gaian_id=gaian_id,
    canon_refs=["C32"],
    inputs={"dominant_hz": dominant_hz, "love_arc_stage": love_arc_stage},
) as trace:
    reading, new_state = self._compute_internal(**params)
    trace.record_output({"synergy_factor": reading.synergy_factor})
```

### ActionGate (`core/action_gate.py`)
```python
with GAIATrace(
    event=TraceEventType.ACTION_GATE_DECISION,
    gaian_id=gaian_id,
    canon_refs=["C01", "C30"],
    inputs={"action": action_type, "risk_tier": risk_tier.value},
) as trace:
    decision = self._evaluate(action_type, context)
    trace.record_output({"allowed": decision.allowed, "reason": decision.reason})
```

### TaskGraph (`core/task_graph.py`) — Issue #170
```python
async def _run_node(self, node: EngineNode) -> None:
    async with AsyncGAIATrace(
        event=TraceEventType.TASK_NODE_EXEC,
        inputs={"engine_id": node.engine_id, "inputs": list(node.inputs)},
        canon_refs=node.canon_refs,
    ) as trace:
        result = await asyncio.wait_for(node.handler(...), timeout=node.timeout_ms / 1000)
        self._context.update(result)
        trace.record_output({"outputs": list(result.keys())})
```

### CanonGraph (`core/canon_graph.py`) — Issue #169
```python
with GAIATrace(
    event=TraceEventType.CANON_LOAD,
    canon_refs=["C01"],
    inputs={"canon_dir": str(canon_dir), "node_count": len(nodes)},
) as trace:
    self._build(canon_dir)
    trace.record_output({"nodes_loaded": len(self._nodes)})
```

---

## CLI Query Utility

```bash
# Filter traces for gaian 'luna' today, only failures
python -m core.trace query --gaian luna --event synergy_compute --error-only

# Show full trace record by correlation ID
python -m core.trace show --correlation-id req-abc123

# Aggregate stats for the last 24 hours
python -m core.trace stats --event llm_inference --since 24
```

---

## Test Coverage Requirements

- [ ] `test_trace_jsonl_output` — verify file is created, single record, valid JSON
- [ ] `test_trace_error_recording` — raise inside `with GAIATrace(...)`, verify `error` field is set and exception propagates
- [ ] `test_trace_latency_nonzero` — verify `latency_ms > 0`
- [ ] `test_async_trace` — verify `AsyncGAIATrace` writes the same record structure via `async with`
- [ ] `test_trace_event_type_enum` — verify `TraceEventType.SYNERGY_COMPUTE.value == "synergy_compute"` and JSON round-trip
- [ ] `test_cli_query` — invoke `python -m core.trace query` against a fixture JSONL, verify correct filtering
- [ ] `test_cli_stats` — verify counts, error rate, latency aggregates

---

## Related Issues

- **#170** `task_graph.py` — every `EngineNode` emits `TASK_NODE_EXEC`
- **#169** `canon_graph.py` — `CanonGraph._build()` emits `CANON_LOAD`
- **#172** `GAIAStateAdapter` — `to_synergy_params()` emits `TOOL_CALL`
- **#173** `MemoryHierarchy` — router emits `MEMORY_RECALL` / `MEMORY_WRITE`
