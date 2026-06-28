# G-7 Sprint: Secure Foundations — Roadmap

**Sprint goal:** Establish the safety, observability, and orchestration foundation that makes every future increase in GAIA's autonomy safe, traceable, and reversible.

**Canon alignment:** C01 (Sovereignty), C30 (No Silent Failures)

---

## Issues in this sprint

| # | Title | Priority | Blocks |
|---|---|---|---|
| G7-001 | [Execution Sandbox Service](./G7-001_EXECUTION_SANDBOX_SERVICE.md) | 🔴 Critical | G7-003, all future tool execution |
| G7-002 | [Model Registry & Runtime Orchestrator](./G7-002_MODEL_REGISTRY_RUNTIME_ORCHESTRATOR.md) | 🔴 High | G7-005, all future multi-model work |
| G7-003 | [Action Gate — Execution Grant Extension](./G7-003_ACTION_GATE_EXECUTION_GRANTS.md) | 🔴 Critical | G7-001 (mutual dependency) |
| G7-004 | [Audit Log Normalizer](./G7-004_AUDIT_LOG_NORMALIZER.md) | 🔴 High | All future transparency features |
| G7-005 | [Synergy Orchestrator v2](./G7-005_SYNERGY_ORCHESTRATOR_V2.md) | 🔴 High | All G-8 autonomy expansion |
| G7-006 | [Workspace & Filesystem Service](./G7-006_WORKSPACE_FILESYSTEM_SERVICE.md) | 🟡 Medium | G7-007, G-10 Research Desk |
| G7-007 | [Live Dev Suite Watcher](./G7-007_LIVE_DEV_SUITE_WATCHER.md) | 🟡 Medium | G-11 Vision Capture |

---

## Build order

```
Track A — Safety (parallel)
  G7-001 (Sandbox) ←→ G7-003 (Action Gate Grants)  [mutual dependency, build together]
  G7-004 (Audit Log)                               [depends on G7-001 + G7-003]

Track B — Intelligence (parallel with Track A)
  G7-002 (Model Registry)
  G7-005 (Synergy Orchestrator v2)                 [depends on G7-002]

Track C — Platform (after Track A foundation is stable)
  G7-006 (Workspace Service)
  G7-007 (Dev Suite Watcher)                       [depends on G7-006]
```

---

## Definition of Done for G-7

- [ ] 100% of GAIA code execution paths route through the Execution Sandbox Service.
- [ ] ActionGate emits `ExecutionGrant` objects for all allowed actions.
- [ ] Every execution produces a complete `ExecutionAuditRecord`.
- [ ] Model Registry is populated from local runtime discovery on launch.
- [ ] Synergy pipeline has all five stages implemented and all engines registered.
- [ ] Workspace Service is the sole FS abstraction in the Tauri frontend.
- [ ] Dev Suite auto-reloads and triggers tests on file changes.
- [ ] All existing tests pass. No regressions.
- [ ] CI runs `python -m py_compile` on all Python files before test execution.

---

## What G-7 enables

| Future sprint | What G-7 gives it |
|---|---|
| G-8: Multi-model routing expansion | Model Registry + Synergy v2 routing substrate |
| G-9: Research Desk | Workspace Service + filesystem watch infrastructure |
| G-10: Vision Capture | Bug Capture bundle foundation |
| G-11: Mobile Shell | Workspace Service cross-platform path system |
| All future autonomy | Sandbox + Audit trail + ActionGate grants |
