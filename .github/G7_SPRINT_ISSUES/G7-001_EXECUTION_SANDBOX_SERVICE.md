---
title: "[G-7] Execution Sandbox Service — Kernel-Enforced Isolation for All GAIA Tool & Code Execution"
labels: ["enhancement", "security", "sprint:G-7", "priority:critical"]
---

## Overview

Every shell command, Dev Suite run, Python sidecar call, MCP server invocation, and future agentic tool execution in GAIA-OS currently runs in the ambient host process context. As GAIA's autonomy grows — code generation, refactoring, shell helpers, research agents — this becomes an unacceptable blast radius. A single compromised or misbehaving tool can reach the user's filesystem, network, or secrets with no kernel-level guardrail.

The Execution Sandbox Service creates a mandatory, default-deny execution layer. Every action that touches the host system must pass through this service and receive an explicit, scoped grant before it runs.

## Background & Motivation

Modern AI agent security research identifies exec policies, plugin channels, and shell quirks as the primary composition vectors for host-level compromise. Lightweight Linux tools such as `nono` (Landlock + Seatbelt) demonstrate that kernel-enforced sandboxing can be added without containers, root access, or significant runtime overhead (~5 ms startup cost). GAIA-OS should adopt the same default-deny posture for all action-capable execution paths before those paths become load-bearing.

This also aligns with:
- **C01 (Sovereignty)** — Users retain sovereignty over their host machine; GAIA must not silently acquire host access.
- **C30 (No Silent Failures)** — Every execution must be logged and attributable.
- The existing `ActionGate` / `RiskTier` model — execution grants become a first-class ActionGate output.

## Scope

All of the following must be mediated by the Execution Sandbox Service after this work lands:

- Dev Suite Run / Test / Format / Lint actions
- Shell command sidecar calls
- Python sidecar tool execution
- Any MCP server subprocess launch
- Future autonomous refactor or code-generation apply flows
- Background task runners

## Architecture

### Core components

```
core/
  execution/
    __init__.py
    launcher.py          # Single public interface: launch(spec) → ExecutionResult
    execution_spec.py    # Typed input: command, cwd, env, trust_tier, correlation_id
    execution_result.py  # Typed output: stdout, stderr, exit_code, sandbox_profile, audit_ref
  sandbox/
    __init__.py
    policy_compiler.py   # Converts ActionGate grants → sandbox profile (paths, hosts, syscalls)
    sandbox_adapter.py   # OS-specific backend: nono/Landlock on Linux, Seatbelt on macOS, stub on Win
    trust_tiers.py       # Three canonical tiers (see below)
    resource_broker.py   # Explicit allow-lists: read paths, write paths, outbound hosts, tmp scope
```

### Trust tiers

| Tier | Name | Filesystem | Network | Use case |
|---|---|---|---|---|
| 0 | `READ_ONLY_INSPECT` | Read declared paths only | Blocked | Linting, static analysis, file inspection |
| 1 | `WORKSPACE_MUTATE` | Read + write within active workspace | Blocked | Compile, test, format, generate files |
| 2 | `NETWORK_BUILD` | Read + write within workspace | Declared outbound hosts only | Package install, external API calls |

No execution may run without resolving to one of these tiers. Tier selection is determined by ActionGate before the call reaches the launcher.

### Action Gate extension

ActionGate's current allow/deny output must be extended to emit an `ExecutionGrant`:

```python
@dataclass
class ExecutionGrant:
    tier: TrustTier
    allowed_read_paths: list[Path]
    allowed_write_paths: list[Path]
    allowed_hosts: list[str]  # empty = no network
    max_duration_seconds: int
    correlation_id: str
```

## Acceptance Criteria

- [ ] `core/execution/launcher.py` is the single entry point for all host-side execution in GAIA. No code path bypasses it.
- [ ] `core/sandbox/sandbox_adapter.py` implements Landlock on Linux, Seatbelt on macOS, and a strict-logging stub on Windows.
- [ ] All three trust tiers are enforced at the kernel level on supported platforms.
- [ ] `ActionGate` emits `ExecutionGrant` objects instead of bare allow/deny.
- [ ] Every execution produces a structured audit event with: command hash, tier, granted paths, correlation ID, exit code, and duration.
- [ ] Dev Suite Run, Test, and Format actions all route through the sandbox. Verified by integration tests.
- [ ] A `pre-commit` guard (`python -m py_compile` + `sandbox_policy_check`) is added to CI.
- [ ] No existing tests regress.

## Simulations / Tests to Define Success

- `tests/sandbox/test_tier0_cannot_write.py` — confirms a Tier-0 process cannot write to a declared read-only path.
- `tests/sandbox/test_tier1_no_network.py` — confirms a Tier-1 process cannot open outbound sockets.
- `tests/sandbox/test_tier2_limited_outbound.py` — confirms a Tier-2 process can reach declared hosts but not undeclared ones.
- `tests/sandbox/test_audit_log_completeness.py` — confirms every execution produces a complete structured audit event.
- Passing condition: all four tests pass on Linux and macOS. Windows stub emits correct warnings.

## Dependencies

- `ActionGate` / `RiskTier` (already exists in `core/action_gate.py`)
- `core/logger.py` (GAIAEvent, correlation_id_ctx)
- OS: Linux kernel ≥ 5.13 (Landlock), macOS any (Seatbelt via sandbox-exec)
- External reference: [nono.sh](https://nono.sh) — Rust sandbox tool for AI agents using Landlock/Seatbelt

## Cross-References

- `core/action_gate.py`
- `core/infra/error_boundary.py`
- Sprint G-7: Model Registry (#G7-002), Action Gate Extensions (#G7-003), Audit Log Normalizer (#G7-004)
- Canon: C01 (Sovereignty), C30 (No Silent Failures)

## Labels
`enhancement` `security` `sprint:G-7` `priority:critical`

## Priority
🔴 Critical — must land before any increase in autonomous tool execution scope.
