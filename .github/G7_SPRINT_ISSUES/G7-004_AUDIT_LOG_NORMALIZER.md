---
title: "[G-7] Audit Log Normalizer — Structured, Correlation-Linked Execution Audit Trail"
labels: ["enhancement", "observability", "sprint:G-7", "priority:high"]
---

## Overview

GAIA-OS emits logs through `core/logger.py` using `GAIAEvent` structured events and `correlation_id_ctx`. However, there is no single normalized schema for *execution audit records* — the specific, forensic-grade log entries that tie an action authorization (ActionGate decision) to an execution result (sandbox output) to an outcome (success/failure/error). As GAIA becomes more autonomous, the absence of a complete audit trail is both a safety gap and a debugging liability.

The Audit Log Normalizer defines and enforces a canonical `ExecutionAuditRecord` schema, ensures every sandboxed execution produces one, and provides a query interface for reviewing, filtering, and exporting audit history.

## Background & Motivation

The existing error boundary (`core/infra/error_boundary.py`) already demonstrates the value of structured, correlation-ID-linked logging — every error is returned as a machine-readable envelope with a traceable ID. The Audit Log Normalizer applies the same discipline to the execution lifecycle: authorization → launch → result → outcome.

This is also the foundation for future transparency features — a user-visible "What did GAIA do?" log, consent review screens, and automated rollback triggers.

## Architecture

```
core/
  audit/
    __init__.py
    audit_record.py     # ExecutionAuditRecord dataclass
    audit_writer.py     # Write records to append-only audit log
    audit_reader.py     # Query, filter, and export audit records
    audit_store.py      # Storage backend (SQLite via aiosqlite, or JSONL append file)
```

### ExecutionAuditRecord schema

```python
@dataclass
class ExecutionAuditRecord:
    # Identity
    audit_id: str                    # UUID
    correlation_id: str              # From correlation_id_ctx
    session_id: str                  # GAIA session identifier
    timestamp_utc: datetime

    # Authorization
    action_type: str                 # e.g. "dev_suite.run", "shell.exec", "tool.call"
    risk_tier: str                   # RiskTier name
    trust_tier: int                  # Sandbox tier (0/1/2)
    grant_rationale: str             # Human-readable reason from ExecutionGrant
    allowed_read_paths: list[str]
    allowed_write_paths: list[str]
    allowed_outbound_hosts: list[str]

    # Execution
    command_hash: str                # SHA-256 of the executed command (never raw command)
    cwd_hash: str                    # SHA-256 of working directory path
    sandbox_backend: str             # "landlock" | "seatbelt" | "stub"
    duration_ms: int

    # Outcome
    exit_code: int
    success: bool
    error_type: str | None           # Exception class name if failure
    stdout_lines: int                # Count only — never log raw stdout in audit records
    stderr_lines: int

    # Flags
    consent_required: bool           # True if CRITICAL tier was escalated with human approval
    consent_given: bool | None
```

### Storage

- Primary: append-only JSONL file at `$APPLOG/gaia/execution_audit.jsonl`
- Secondary (query): SQLite at `$APPLOCALDATA/gaia/audit.db` (populated async from JSONL)
- Both paths use the Tauri FS plugin's `$APPLOG` / `$APPLOCALDATA` base directories for cross-platform correct paths.

### Retention policy

- Default: 90-day rolling window.
- User-configurable via Settings Store.
- Records are never deleted within the retention window without explicit user action.

## Acceptance Criteria

- [ ] `ExecutionAuditRecord` is defined and all fields are populated for every sandboxed execution.
- [ ] Records are written to the JSONL append log atomically (no partial writes).
- [ ] SQLite view is populated asynchronously and queryable within 1 second of write.
- [ ] `audit_reader.py` exposes: `recent(n)`, `by_correlation_id(cid)`, `by_session(sid)`, `since(dt)`, `export_jsonl(path)`.
- [ ] Raw command strings are never stored — only SHA-256 hashes.
- [ ] Raw stdout/stderr content is never stored — only line counts.
- [ ] Retention enforcement runs on startup and prunes records older than the configured window.
- [ ] Unit tests cover: record creation, JSONL append, SQLite query, retention pruning, hash-only storage invariant.

## Simulations / Tests to Define Success

- `tests/audit/test_record_completeness.py` — every execution through the sandbox produces an audit record with all required fields populated.
- `tests/audit/test_no_raw_command_storage.py` — asserts no audit record contains a raw command string.
- `tests/audit/test_retention_pruning.py` — inserts records older than the retention window; confirms they are pruned on the next startup cycle.
- `tests/audit/test_query_by_correlation_id.py` — inserts 100 records; confirms query by correlation_id returns the correct single record.

## Dependencies

- `core/execution/launcher.py` (#G7-001)
- `core/action_gate.py` (#G7-003)
- `core/logger.py` (correlation_id_ctx)
- `aiosqlite` (new dependency)
- Tauri FS plugin (`$APPLOG`, `$APPLOCALDATA` base directories)

## Cross-References

- Sprint G-7: Sandbox Service (#G7-001), Action Gate Extensions (#G7-003)
- Canon: C30 (No Silent Failures), C01 (Sovereignty)
- Future: user-visible "Activity Log" panel in GAIA UI

## Labels
`enhancement` `observability` `sprint:G-7` `priority:high`

## Priority
🔴 High — forensic audit trail is required before any increase in autonomous execution.
