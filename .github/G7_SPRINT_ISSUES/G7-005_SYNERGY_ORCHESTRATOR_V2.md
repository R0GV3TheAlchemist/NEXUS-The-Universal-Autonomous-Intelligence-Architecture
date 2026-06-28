---
title: "[G-7] Synergy Orchestrator v2 — Intent Parser, Engine Router & Multi-Stage Execution Planner"
labels: ["enhancement", "ai-core", "sprint:G-7", "priority:high"]
---

## Overview

The Synergy Engine (`core/synergy_engine.py`) is GAIA's coordination core, but it currently functions as a flat coordinator: it holds state and dispatches, but it does not have a structured pipeline for intent classification, engine selection, tool filtering, or synthesis scoring. As GAIA grows, this causes prompt bloat, inconsistent tool exposure, and brittle coupling between the UI layer and the intelligence layer.

Synergy Orchestrator v2 restructures the engine into a five-stage pipeline: **Interpret → Select → Authorize → Execute → Synthesize**. Each stage has a defined contract, and each GAIA engine registers itself as a typed capability rather than being hardcoded into routing logic.

## Background & Motivation

Enterprise orchestration research shows that intent parsing + semantic tool filtering is the primary lever for improving multi-agent quality and consistency. Sending every tool to every prompt is both expensive and unsafe — it exposes capabilities to the model that are not relevant to the task. A structured selection stage reduces prompt size, improves determinism, and makes capability governance tractable.

This refactor also enables the Model Registry (#G7-002) to be consumed properly: instead of engines selecting their own model, the orchestrator resolves the right model for each stage's requirements.

## Architecture

### Five-stage pipeline

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  INTERPRET   │──▶│   SELECT     │──▶│  AUTHORIZE   │──▶│   EXECUTE    │──▶│ SYNTHESIZE   │
│              │   │              │   │              │   │              │   │              │
│ Classify     │   │ Choose       │   │ ActionGate   │   │ Run engines  │   │ Merge,       │
│ intent into  │   │ engines +    │   │ evaluates    │   │ with scoped  │   │ score, emit  │
│ typed task   │   │ filter tools │   │ all grants   │   │ tools/models │   │ response     │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

### New files

```
core/
  synergy/
    __init__.py
    pipeline.py            # OrchestratorPipeline — top-level five-stage runner
    intent_parser.py       # classify(request) → TaskSpec
    engine_selector.py     # select(TaskSpec) → list[EngineDescriptor]
    tool_filter.py         # filter(TaskSpec, all_tools) → list[Tool]
    plan_executor.py       # execute(plan, grants) → list[EngineResult]
    synthesizer.py         # synthesize(results) → SynthesisOutput
    task_spec.py           # TaskSpec dataclass
    engine_registry.py     # EngineRegistry — register/discover GAIA engines by capability
    engine_descriptor.py   # EngineDescriptor dataclass
    synthesis_output.py    # SynthesisOutput dataclass with confidence + risk scores
```

### TaskSpec

```python
@dataclass
class TaskSpec:
    intent_class: IntentClass      # CONVERSATIONAL | OPERATIONAL | DEVELOPMENTAL |
                                   # RESEARCH | REFLECTIVE | MIXED
    goal: str                      # Normalized goal statement
    required_capabilities: list[ModelCapability]
    context_depth: Literal["short", "medium", "long"]
    risk_surface: RiskTier
    correlation_id: str
```

### EngineDescriptor

```python
@dataclass
class EngineDescriptor:
    engine_id: str
    display_name: str
    intent_classes: list[IntentClass]    # Which intents this engine handles
    required_capabilities: list[ModelCapability]
    tools: list[str]                     # Tool IDs this engine may use
    priority: int                        # Lower = selected first when multiple engines match
```

### Engine registry

Engines self-register on import:
```python
engine_registry.register(EngineDescriptor(
    engine_id="soul_mirror",
    display_name="Soul Mirror",
    intent_classes=[IntentClass.REFLECTIVE, IntentClass.CONVERSATIONAL],
    required_capabilities=[ModelCapability.DEEP_REASON],
    tools=["memory.read", "archetype.query"],
    priority=10,
))
```

This means adding a new engine never requires changes to routing logic — only a registration call.

## Decision Quality Metric

The Synthesizer scores each multi-engine response on:
- **Consistency** — do engine outputs agree on key claims?
- **Completeness** — are all required task components addressed?
- **Risk alignment** — does the response match the authorized risk tier?

A `DecisionQualityScore` (0.0–1.0) is attached to every `SynthesisOutput` and logged in the audit trail.

## Acceptance Criteria

- [ ] `core/synergy/pipeline.py` implements all five stages with typed contracts between them.
- [ ] All existing GAIA engines are registered in `engine_registry.py` with correct descriptors.
- [ ] A new engine can be added by calling `engine_registry.register()` — no changes to pipeline code required.
- [ ] The tool filter ensures no tool is exposed to a model unless it is in the selected engine's declared tool list.
- [ ] `SynthesisOutput` includes a `DecisionQualityScore` for every response.
- [ ] The existing `SynergyEngine` public interface (`process_request`, `get_state`) is preserved during migration so callers are not broken.
- [ ] Integration tests cover all five intent classes producing correctly routed plans.
- [ ] Performance: median pipeline overhead (excluding model inference) ≤ 50 ms.

## Simulations / Tests to Define Success

- `tests/synergy/test_intent_classification_coverage.py` — 20 sample requests; confirms each resolves to the correct `IntentClass`.
- `tests/synergy/test_engine_selection_isolation.py` — confirms a DEVELOPMENTAL task does not activate Soul Mirror.
- `tests/synergy/test_tool_filter_no_bleed.py` — confirms no tool outside the selected engine's declared list appears in any model prompt.
- `tests/synergy/test_new_engine_registration.py` — registers a mock engine; confirms it is selected for matching intents without pipeline changes.
- `tests/synergy/test_decision_quality_score_range.py` — all synthesis outputs produce a DQ score in [0.0, 1.0].

## Migration Plan

1. Create `core/synergy/` alongside existing `core/synergy_engine.py`.
2. Implement pipeline stages with new types.
3. Register all existing engines in the new registry.
4. Redirect `SynergyEngine.process_request()` to call the new pipeline internally.
5. Run full test suite. Fix regressions.
6. Deprecate direct engine dispatch outside the pipeline.
7. Remove old dispatch code in G-8 once all callers are migrated.

## Dependencies

- `core/models/runtime_orchestrator.py` (#G7-002)
- `core/action_gate.py` (#G7-003)
- `core/audit/audit_writer.py` (#G7-004)
- All existing GAIA engines (Soul Mirror, Stage Engine, Schumann, Crystal services, etc.)

## Cross-References

- Sprint G-7: Model Registry (#G7-002), Action Gate Extensions (#G7-003)
- Sprint G-8: full tool-calling expansion, multi-engine parallel execution
- Canon: C01 (Sovereignty), C30 (No Silent Failures)

## Labels
`enhancement` `ai-core` `sprint:G-7` `priority:high`

## Priority
🔴 High — the clean orchestration substrate for all G-8+ autonomy work.
