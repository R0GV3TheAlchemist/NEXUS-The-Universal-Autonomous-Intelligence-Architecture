---
title: "[G-7] Action Gate — Execution Grant Extension for Sandboxed Tool Authorization"
labels: ["enhancement", "security", "sprint:G-7", "priority:critical"]
---

## Overview

The existing `ActionGate` in `core/action_gate.py` produces allow/deny decisions and `RiskTier` classifications for GAIA actions. This is a strong foundation, but it is not sufficient for sandboxed execution. The Execution Sandbox Service (#G7-001) needs structured, typed `ExecutionGrant` objects — not bare booleans — to construct accurate sandbox profiles. ActionGate must be extended to emit those grants.

This issue also standardizes the risk tier taxonomy to map cleanly onto the three sandbox trust tiers introduced by the Sandbox Service, creating a unified authorization language across the entire action governance layer.

## Background & Motivation

Current ActionGate logic classifies risk and decides allow/deny, but the sandbox needs to know *what is allowed*, not just *whether it is allowed*. The extension here is additive: existing allow/deny behavior is preserved, and `ExecutionGrant` is emitted as an additional structured output alongside it.

This also makes ActionGate the canonical governance interface for all action-capable modules — a principle that will scale cleanly as GAIA adds more autonomous capabilities in G-8 and beyond.

## Scope of Changes

### New types in `core/action_gate.py`

```python
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ExecutionGrant:
    """
    Structured authorization emitted by ActionGate for sandbox-mediated execution.
    The Execution Sandbox Service consumes this to build the kernel-enforced policy.
    """
    tier: TrustTier                         # Maps to sandbox trust tier (0/1/2)
    allowed_read_paths: list[Path] = field(default_factory=list)
    allowed_write_paths: list[Path] = field(default_factory=list)
    allowed_outbound_hosts: list[str] = field(default_factory=list)  # empty = no network
    max_duration_seconds: int = 30
    correlation_id: str = ""
    rationale: str = ""                     # Human-readable justification for audit log


@dataclass
class ActionDecision:
    """
    Full ActionGate output — replaces bare bool return values.
    """
    allowed: bool
    risk_tier: RiskTier
    grant: Optional[ExecutionGrant] = None  # Present only when allowed=True and action is executable
    reason: str = ""
```

### Updated ActionGate methods

- `ActionGate.evaluate(action: Action) → ActionDecision` — replaces the current bool-returning evaluation.
- All call sites are updated to consume `ActionDecision` rather than bare bool.
- Existing tests are updated to match the new return type.

### RiskTier → TrustTier mapping

| RiskTier | TrustTier | Rationale |
|---|---|---|
| `LOW` | `READ_ONLY_INSPECT` (0) | Safe inspection only |
| `MEDIUM` | `WORKSPACE_MUTATE` (1) | Workspace-scoped writes allowed |
| `HIGH` | `NETWORK_BUILD` (2) | Network access with explicit allow-list |
| `CRITICAL` | Deny — no grant issued | Requires explicit human consent before re-evaluation |

## Acceptance Criteria

- [ ] `ExecutionGrant` and `ActionDecision` are defined in `core/action_gate.py`.
- [ ] `ActionGate.evaluate()` returns `ActionDecision` in all code paths.
- [ ] `ExecutionGrant` is emitted for every allowed executable action.
- [ ] `RiskTier.CRITICAL` actions never produce a grant without explicit human consent confirmation.
- [ ] All existing ActionGate call sites are updated and all existing tests pass.
- [ ] New unit tests cover: grant emission for LOW/MEDIUM/HIGH tiers, deny with no grant for CRITICAL, ActionDecision serialization for audit logging.
- [ ] The sandbox service (#G7-001) successfully consumes `ExecutionGrant` objects in integration tests.

## Simulations / Tests to Define Success

- `tests/action_gate/test_execution_grant_emission.py` — for each RiskTier, confirms the correct grant tier and fields are produced.
- `tests/action_gate/test_critical_tier_no_grant.py` — confirms CRITICAL actions produce `allowed=False, grant=None`.
- `tests/action_gate/test_action_decision_audit_serializable.py` — confirms `ActionDecision` serializes cleanly to JSON for audit logging.
- `tests/integration/test_sandbox_consumes_grant.py` — end-to-end: ActionGate evaluates → produces grant → sandbox launches with correct profile.

## Dependencies

- `core/action_gate.py` (existing)
- `core/execution/launcher.py` (#G7-001)
- `core/logger.py`

## Cross-References

- Sprint G-7: Execution Sandbox Service (#G7-001), Audit Log Normalizer (#G7-004)
- Canon: C01 (Sovereignty), C30 (No Silent Failures)
- `core/infra/error_boundary.py` (error envelope patterns apply here too)

## Labels
`enhancement` `security` `sprint:G-7` `priority:critical`

## Priority
🔴 Critical — the Sandbox Service cannot function without typed grants. Must land in the same milestone as #G7-001.
