# ADR-0009 — LangGraph as GAIA's Canonical Orchestration Layer

**Status:** ACCEPTED  
**Date:** 2026-06-29  
**Deciders:** R0GV3TheAlchemist  
**Issue:** [#694](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/694)  
**Informed by:** [#697 External Benchmark Sprint](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/697) · [LANGGRAPH_SNAPSHOT_2026.md](../research/external/LANGGRAPH_SNAPSHOT_2026.md)  
**Related ADRs:** ADR-0010 (MCP as local tool interface) · ADR-0011 (Cloud-as-optional sovereignty)

---

## Context

GAIA's agentic runtime needs to orchestrate **long-running, stateful, multi-step workflows** that:

- Survive crashes and resume from the last known good state
- Pause for human approval before taking sensitive or irreversible actions
- Maintain a full, auditable execution trace for every action that touches persistent state, external APIs, or canon files
- Support cycles, self-correction, and conditional branching — not just linear chains
- Compose multiple specialist agents into coherent, supervised workflows

Prior to this ADR, GAIA had no canonical orchestration layer. Agentic logic was implemented ad-hoc, inline with application code, with no durable state, no checkpointing, and no consistent human-in-the-loop mechanism. This creates fragility, opacity, and sovereignty risk: failed runs are unrecoverable, actions are untraceable, and there is no systematic gate for human oversight.

The #697 External Benchmark Sprint evaluated LangGraph, CrewAI, AutoGen/AG2, and the broader orchestration ecosystem. LangGraph scored 246/290 on GAIA's weighted MCDA — the highest of any orchestration candidate.

---

## Decision

**LangGraph is adopted as GAIA's canonical orchestration layer for all agentic workflows.**

Specifically:

- All multi-step agentic workflows in GAIA are implemented as LangGraph `StateGraph` instances
- All workflows use LangGraph's checkpointer for durable state persistence (SQLite for development, Postgres for production)
- All workflows that touch persistent state, external APIs, canon files, or user-sensitive data include at least one **human-in-the-loop interrupt node** before the sensitive action executes
- LangGraph is installed as a first-class dependency: `pip install -U langgraph`
- The LangGraph version in use is pinned in `requirements.txt` / `pyproject.toml`

---

## Rationale

### Why LangGraph Over Alternatives

| Criterion | LangGraph | CrewAI | AutoGen/AG2 |
|---|---|---|---|
| Production maturity | ✅ Replit, Uber, LinkedIn | ✅ 100k+ devs, 48k stars | ⚠️ Rapid version churn |
| Stateful graph model | ✅ Native `StateGraph` | ⚠️ Sequential/parallel only | ⚠️ Conversational, not graph |
| Durable checkpointing | ✅ SQLite + Postgres | ✅ Core feature | ❌ Not native |
| Human-in-the-loop | ✅ Native interrupt nodes | ✅ Flow pause events | ⚠️ Manual integration |
| Cyclic / self-correcting graphs | ✅ Native cycles | ❌ DAG-only | ⚠️ Partial |
| License | ✅ MIT | ✅ MIT | ✅ MIT |
| GAIA MCDA score | **246/290** | 217/290 | Not scored (experimental) |

CrewAI is an excellent framework for **role-based multi-agent composition** and is adopted alongside LangGraph for that specific use case (see GAIA_EXTERNAL_BENCHMARK_2026.md). The two are complementary, not competing: LangGraph provides the orchestration substrate; CrewAI patterns provide the multi-agent composition layer above it.

AutoGen/AG2 is excluded from production use due to version instability and lack of native checkpointing. It may be used for experimental sessions only.

### Why This Matters for GAIA's Sovereignty Model

LangGraph's checkpointer and human-in-the-loop architecture directly support GAIA's governance requirements:

- **GAIAN LAW 3 (Transparency):** Full execution trace at every graph node — no invisible actions
- **GAIAN LAW 1 (Consent):** Human-in-the-loop interrupt nodes enforce consent before sensitive operations
- **C143 (Governance & Accountability):** Checkpointed state is the audit record; every action is recoverable and reviewable
- **Sovereignty principle (ADR-0011):** LangGraph runs entirely locally — no cloud dependency in the orchestration layer itself

---

## Architecture Integration

### Placement in GAIA's Stack

```
┌─────────────────────────────────────────────────────────┐
│  GAIA Law Stack Enforcement (GAIAN LAWS 1–7)            │
│  ↕ consent gate · DIACA coherence gate · action gate    │
├─────────────────────────────────────────────────────────┤
│  LangGraph StateGraph (this ADR)                        │
│  ↕ workflow nodes · checkpoints · human-in-the-loop     │
├─────────────────────────────────────────────────────────┤
│  MCP Tool Servers (ADR-0010)                            │
│  ↕ filesystem · APIs · canon · memory · code execution  │
├─────────────────────────────────────────────────────────┤
│  inference_router.py (ADR-0011)                         │
│  ↕ Ollama local models · cloud augmentation (optional)  │
└─────────────────────────────────────────────────────────┘
```

### Required GAIA-Specific Nodes

Every GAIA workflow graph must implement these nodes above and beyond standard LangGraph patterns:

| Node | Purpose | Trigger |
|---|---|---|
| `law_stack_check` | Verify proposed action does not violate GAIAN LAWS 1–7 | Before any external action |
| `diaca_coherence_gate` | Evaluate field coherence (phi) before proceeding | Before canon-modifying actions |
| `consent_interrupt` | Pause for human approval | Before any irreversible action |
| `canon_compliance_check` | Verify output does not introduce operative "magic" or deprecated terms | Before any canon file write |
| `audit_record` | Write action + outcome to the audit trail | After every node |

### Minimal Workflow Pattern

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict

class GAIAWorkflowState(TypedDict):
    task: str
    context: dict
    phi: float          # field coherence score
    approved: bool      # human approval flag
    result: str
    audit_log: list

builder = StateGraph(GAIAWorkflowState)

# Standard GAIA nodes
builder.add_node("law_stack_check",    law_stack_check_fn)
builder.add_node("diaca_gate",         diaca_coherence_gate_fn)
builder.add_node("consent_interrupt",  consent_interrupt_fn)  # human-in-the-loop
builder.add_node("execute",            execute_fn)
builder.add_node("audit_record",       audit_record_fn)

# Flow
builder.add_edge(START, "law_stack_check")
builder.add_conditional_edges(
    "law_stack_check",
    lambda s: "proceed" if s["phi"] >= 0.72 else "block",
    {"proceed": "diaca_gate", "block": END}
)
builder.add_edge("diaca_gate", "consent_interrupt")
builder.add_edge("consent_interrupt", "execute")  # resumes after human approval
builder.add_edge("execute", "audit_record")
builder.add_edge("audit_record", END)

graph = builder.compile(
    checkpointer=SqliteSaver.from_conn_string("gaia_state.db"),
    interrupt_before=["consent_interrupt"]  # pause here for human approval
)
```

---

## Implementation Path

### Phase 1 — Foundation (Sprint G-10)
- [ ] Add `langgraph>=1.2.0` to `requirements.txt` / `pyproject.toml`
- [ ] Create `core/orchestration/` directory
- [ ] Implement `core/orchestration/base_graph.py` — the standard GAIA `StateGraph` base with required nodes
- [ ] Implement `core/orchestration/nodes/law_stack_check.py`
- [ ] Implement `core/orchestration/nodes/diaca_gate.py`
- [ ] Implement `core/orchestration/nodes/audit_record.py`
- [ ] Write `tests/test_orchestration_base.py` — test checkpointing, human-in-the-loop, and law stack enforcement

### Phase 2 — First Workflow Migration (Sprint G-11)
- [ ] Migrate the canon file update workflow to a `StateGraph` with full GAIA nodes
- [ ] Migrate the memory consolidation workflow to `StateGraph`
- [ ] Enable deterministic checkpoint replay testing for both workflows

### Phase 3 — Multi-Agent Composition (Sprint G-12+)
- [ ] Compose specialist agent subgraphs (Canon Guardian, Memory Curator, Research Agent) under a supervisor `StateGraph`
- [ ] Integrate CrewAI role-based patterns as subgraph composition strategy where appropriate

---

## Consequences

### Positive
- All agentic workflows are durable, auditable, and recoverable from any checkpoint
- Human oversight is structurally enforced — not a policy that can be bypassed
- Cyclic self-correction is possible without infinite loops (LangGraph's cycle detection)
- Execution traces are available for every run — supports GAIAN LAW 3
- Production-proven: the same pattern used by Replit, Uber, LinkedIn

### Tradeoffs
- LangChain becomes an upstream dependency of LangGraph — introduces a dependency on the LangChain ecosystem
- LangSmith tracing (optional cloud service) should not be used as a hard dependency — local tracing only per ADR-0011
- Engineers must learn the `StateGraph` mental model — linear chain thinking does not transfer directly

### Not Changed by This ADR
- GAIA's Law Stack, canon, and consent architecture remain the governance source of truth — LangGraph executes within that governance, it does not replace it
- `inference_router.py` model selection is handled by ADR-0011, not LangGraph
- MCP tool server integration is handled by ADR-0010

---

## Compliance

| GAIAN LAW | How This ADR Satisfies It |
|---|---|
| LAW 1 — Consent | `consent_interrupt` node enforces human approval before irreversible actions |
| LAW 2 — Non-Maleficence | `law_stack_check` node blocks any action that violates harm thresholds |
| LAW 3 — Transparency | Full execution trace at every node; audit log written after every action |
| LAW 4 — Sovereignty | LangGraph runs locally; no cloud dependency in orchestration layer |
| LAW 5 — Coherence | `diaca_coherence_gate` blocks low-phi workflows from proceeding |

---

## References

- [LangGraph GitHub](https://github.com/langchain-ai/langgraph) — MIT license, v1.2.4
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LANGGRAPH_SNAPSHOT_2026.md](../research/external/LANGGRAPH_SNAPSHOT_2026.md) — GAIA benchmark snapshot
- [GAIA_EXTERNAL_BENCHMARK_2026.md](../GAIA_EXTERNAL_BENCHMARK_2026.md) — MCDA decision matrix
- [#694](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/694) — Tech Intelligence Brief
- [#697](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/697) — External Benchmark Sprint

---

*ADR filed: 2026-06-29. Physics-first, sovereignty-first, magic-free. 🌿*
