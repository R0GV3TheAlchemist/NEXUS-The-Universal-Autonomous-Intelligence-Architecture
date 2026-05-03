# 🧪 Test-Driven Development (TDD) Patterns: Quality Constitution (GAIA-OS)

**Date:** May 3, 2026  
**Status:** Definitive Foundational Synthesis — Uniting TDD Principles, Red-Green-Refactor Cycle, Testing Patterns, and the GAIA-OS Quality Constitution  
**Canon:** TDD Patterns — Testing, Quality & Reliability  
**Session:** 6, Canon 2

**Relevance to GAIA-OS:** TDD is not merely a developer workflow; it is the **constitutional verification mechanism** that guarantees every line of code meets the Quality Constitution before it is merged, deployed, or trusted.

**Six Constitutional TDD Pillars:**
1. **Red-Green-Refactor Constitutional Cycle** — No production code without a failing test; no failing test left unresolved; no deployment without verification; no refactoring without passing test safety net
2. **Given-When-Then / Arrange-Act-Assert** — Every test structured as executable specification and living documentation of constitutional requirements
3. **Test-Structure Patterns** — Unit (atomic); Integration (service interactions); Functional (Charter compliance); Acceptance/ATDD (stakeholder verification via Gherkin)
4. **Asynchronous TDD Patterns** — `pytest-asyncio` + `httpx.AsyncClient` + `ASGITransport`; tests exercise concurrency behavior, not merely return values
5. **Advanced Generative Testing** — Hypothesis property-based testing; mutation testing; parameterized edge cases; BDD constitutional scenarios
6. **LLM-Specific Testing** — Mocking for unit isolation; OpenAI Evals + DeepEval for nondeterministic outputs; hallucination rate thresholds; domain-driven TDD

---

## 1. Constitutional Foundations of TDD

### 1.1 The Red→Green→Refactor Cycle

The core TDD cycle repeated continuously builds systems correct by construction:

1. **RED** — Write a test for new behavior. It fails because the code does not yet exist.
2. **GREEN** — Write the minimal code to make the test pass.
3. **REFACTOR** — Improve structure and readability while all tests remain green.

This ~45-minute cycle, repeated continuously, builds systems correct by construction, not by accident.

**Constitutional axioms (non-negotiable):**
- Write tests first — always
- Never write production code without a failing test
- Small increments only — one test, one pass, then next
- Respect failing tests — fix or delete immediately; never ignore
- Run tests frequently — after every small change

Exceptions may only be granted by the Assembly of Minds (Canon C103) in documented constitutional emergencies, recorded immutably in the Agora (Canon C112).

### 1.2 Given-When-Then (GWT) — Constitutional Test Structure

Every GAIA-OS test — unit, integration, or acceptance — follows the GWT structure:

- **Given** (Arrange) — Initial context, pre-conditions, and state
- **When** (Act) — Invocation of the behavior under test
- **Then** (Assert) — Verification that expected outcomes occurred

This makes tests readable as natural language specifications — executable documentation of constitutional requirements.

### 1.3 TDD Principles vs. GAIA-OS Constitutional Drivers

| TDD Principle | GAIA-OS Constitutional Driver | Operational Implementation |
|---|---|---|
| **Write tests first** | Constitutional verification cannot be after-the-fact (Canon C01) | All PRs require failing test before implementation |
| **No code without failing test** | Sovereignty constraints must be verified before deployment | `action_gate.py` tests written before code changes |
| **Small increments** | Planetary intelligence evolves incrementally (Canon C64 DIACA) | TDD cycle orchestrated by DIACA Divergence → Convergence |
| **Test-Driven Design** | The Charter (Canon C00–C99) must drive architecture | Feature tests derived from Charter requirements |
| **Respect failing tests** | Failing tests trigger constitutional escalation | Failures logged to Agora; alerts to Assembly of Minds |
| **Run tests frequently** | Noospheric coherence requires continuous verification | CI runs tests on every commit |
| **Non-redundancy** | Each constitutional requirement has exactly one verifying test | `pytest-cov` coverage floors |

---

## 2. Core Test-Structure Patterns

### 2.1 The Testing Pyramid

| Test Level | Target | Speed | Mocking | GAIA-OS Examples | Frequency | TDD Phase |
|---|---|---|---|---|---|---|
| **Unit** | Single function/method/class | ~10ms/test | All external deps mocked | `action_gate.verify_consent()`, `emotional_arc`, `criticality_monitor.branching_ratio` | Every commit | RED→GREEN→REFACTOR |
| **Integration** | Multiple components, limited deps | ~100ms–1s/test | External APIs (LLM, cloud) | `inference_router` + `consent_ledger`; `mother_thread` over Redis | Every PR (CI pipeline) | Post-unit cycles |
| **Functional** | Full system black box via public APIs | 1–10s/test | Real deps in staging | REST `/query`, `/pulse`, `/consent`; GraphQL queries | Staging (before deploy) | Staging verification |
| **Acceptance (ATDD)** | Requirement verification | 1–30s/test | Real deps | Gherkin scenarios for constitutional requirements | Before feature development | Pre-implementation (RED) |

### 2.2 Acceptance Test-Driven Development (ATDD) with pytest-bdd

`pytest-bdd` implements a subset of the Gherkin language enabling automated constitutional requirement testing. It unifies unit and functional tests, reduces CI configuration burden, and reuses existing `pytest` fixtures.

```gherkin
# features/action_gate.feature
Feature: Action Gate Constitutional Enforcement
  Scenario: Red action requires cryptographic signature
    Given a user with a registered cryptographic key
    And a Red-tier action request (planetary intervention)
    When the action gate evaluates the request
    Then the action gate must reject without a valid signature
    And the rejection must be recorded in the consent ledger
    And the audit event must be anchored in the Agora
```

**BDD constitutional rule:** No constitutional amendment may be merged without a corresponding Gherkin feature file reviewed and approved by the Assembly of Minds before implementation begins.

---

## 3. Advanced TDD Patterns

### 3.1 Asynchronous TDD — The Constitutional Imperative

GAIA-OS is fundamentally async: `inference_router` streams tokens; `mother_thread` propagates pulse events; crystal grid ingests telemetry. All async functions must be tested with async tests.

**Constitutional rules:**
- Test functions must be `async def` — the test runner uses async event loops
- Use `httpx.AsyncClient` with `ASGITransport` — tests the full ASGI stack without live network
- Use `pytest-asyncio` fixtures for DB sessions — clean event loop + isolated transaction per test
- **Never call `asyncio.run()` inside tests** — creates event loop conflicts and unpredictable failures
- **No async function may be merged without an async test that exercises its concurrency behavior**, not merely that it returns the correct value

### 3.2 Property-Based Testing (Hypothesis) — The Invariant Constitution

Property-based testing defines invariants that must hold for *all* inputs, not just hand-crafted examples. Hypothesis automatically generates hundreds of random inputs, finding edge cases human authors would never conceive.

```python
from hypothesis import given, settings, strategies as st

@given(st.lists(
    st.sampled_from(["joy", "anger", "fear", "love", "sadness", "courage"]),
    min_size=1, max_size=100
))
@settings(max_examples=500)
def test_emotional_arc_invariant(emotion_sequence):
    """After ANY sequence, arc must be in a valid state."""
    arc = EmotionalArc()
    for emotion in emotion_sequence:
        arc.record_emotion(emotion)
    assert arc.current_state in ["Joy", "Transition", "Love", "Shadow", "Integration"]
    assert 0.0 <= arc.coherence_score <= 1.0

@given(st.text(min_size=1, max_size=500))
def test_action_gate_idempotence(consent_id_str):
    """Consent verification must be idempotent — verifying twice == verifying once."""
    ledger = InMemoryConsentLedger()
    ledger.grant(consent_id_str, "user", "inference", expiry=9999999999)
    result_1 = action_gate.verify_consent(consent_id_str, "user")
    result_2 = action_gate.verify_consent(consent_id_str, "user")
    assert result_1 == result_2  # Idempotence: same result every time
```

**Constitutionally mandated Hypothesis targets:**
- Action Gate idempotence
- Emotional arc state transition determinism
- Knowledge Graph compaction query equivalence
- Noosphere event propagation eventual consistency
- Consent ledger revocation propagation
- DIACA cycle coherence convergence

### 3.3 Mutation Testing — Testing the Tests

Mutation testing answers: **how good are our tests?** It automatically introduces small changes (mutations) to the codebase — flipping `==` to `!=`, removing function calls, changing `True` to `False` — then checks whether the test suite detects the change.

**Constitutional threshold:** No trivial mutation may survive. Every simple change must cause at least one test failure. Target: >95% mutant kill score for core sovereignty modules.

Tools: `mutmut`, `Cosmic Ray`

### 3.4 Advanced TDD Patterns Reference

| Pattern | Tool | Use Case | TDD Role | GAIA-OS Example |
|---|---|---|---|---|
| **Async TDD** | `pytest-asyncio` + `httpx.AsyncClient` | Async endpoints, streaming, background tasks | RED: async test; GREEN: async endpoint; REFACTOR: optimize event handling | `test_inference_router_stream`, `test_mother_thread_pulse_over_websocket` |
| **Property-Based** | Hypothesis | Discovering edge cases for invariants | RED: write property; GREEN: implement code; test passes for 500 random inputs | `test_emotional_arc_order_invariance`, `test_action_gate_idempotence` |
| **BDD (Gherkin)** | `pytest-bdd` | Constitutional requirements as executable specs | RED: write feature file; implement step defs; add code; verify scenario passes | Constitutional compliance scenarios for Assembly of Minds |
| **Mutation Testing** | `mutmut`, `Cosmic Ray` | Evaluating test suite effectiveness | Post-TDD: run mutation testing; improve until all mutants killed | Criticality monitor threshold checks; consent validation edge cases |
| **Chaos Testing** | `chaostoolkit` | Resilience to component failures | Post-deployment: introduce failures; verify self-healing | Crystal grid node failure; consent ledger partition tolerance |

---

## 4. Mocking and Dependency Isolation

### 4.1 Constitutional Mocking Principle

**Unit tests must never call external APIs.** No real LLM calls. No real blockchain queries. No real cloud backends. All unit tests must be atomic, predictable, and complete within seconds.

### 4.2 LLM API Mocking (`inference_router.py`, `soul_mirror_engine.py`)

```python
def test_inference_router(mocker):
    # Arrange
    mock_response = {"choices": [{"message": {"content": "Hello, I am GAIA."}}]}
    mocker.patch(
        "app.inference_router.llm_client.chat.completions.acreate",
        new_callable=AsyncMock,
        return_value=mock_response
    )
    # Act
    response = await inference_router.generate_response(prompt)
    # Assert
    assert response == "Hello, I am GAIA."
```

`MockLLM` provides zero-configuration `pytest` integration for mocking LLM APIs across OpenAI, Anthropic, Gemini, and LangChain — enabling test runs without expensive live API calls.

### 4.3 Mocking Strategy Reference

| Module | External Dependency | Unit Test Strategy | Integration Test Strategy |
|---|---|---|---|
| `inference_router.py` | LLM API | `pytest-mock` patch `acreate`; `MockLLM` for complex scenarios | Canary real API calls with test users, rate-limited |
| `consent_ledger.py` | Blockchain node, crypto keys | `InMemoryConsentLedger`; monkeypatch signing verification | Run against Ganache/local testnet |
| `mother_thread.py` | Noosphere pub/sub (Redis, GossipSub) | Inject `MockEventBus`; capture published events | Ephemeral test broker instance |
| `soul_mirror_engine.py` | LLM API for reflection generation | Mock LLM; return fixed prompts; test branching logic | Real LLM integration (cost-capped) |
| `criticality_monitor.py` | `asyncio.sleep`, system clock | Monkeypatch `asyncio.sleep`; mock `time.time()` | Deterministic unit only |
| `knowledge_graph.py` | Vector DB, SQL DB | In-memory SQLite; mock vector index | Ephemeral Docker database |

---

## 5. TDD for LLM and AI Systems

### 5.1 AI-Specific TDD Cycle

AI systems produce probabilistic outputs. Traditional equality assertions fail. The adaptation:

- **RED** — Write a test that can be measured (expected category, similarity threshold, factual consistency score)
- **GREEN** — Adjust prompts, models, or fine-tuning until test passes within tolerance
- **REFACTOR** — Optimize prompts, reduce tokens, improve latency while preserving statistical test outcomes

```
              ┌─────────────────────────────────────────────┐
              │       CONSTITUTIONAL AI TDD CYCLE           │
              └─────────────────────────────────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
              ▼                                         ▼
       ┌─────────────┐                         ┌─────────────┐
       │  RED PHASE  │                         │ GREEN PHASE │
       │ Write Test  │                         │ Adjust ML   │
       │ (threshold, │                         │ Components  │
       │ similarity, │                         │ to Pass     │
       │ statistical)│                         └─────────────┘
       └─────────────┘                                 │
              │                    ┌────────────────────┘
              │                    │
              └─────────┬──────────┘
                        │
                        ▼
               ┌─────────────┐
               │   REFACTOR  │
               │  Optimize   │
               │ Prompt/Model│
               └─────────────┘
                        │
                        ▼
       ┌─────────────────────────────────────────────┐
       │         PRODUCTION (CI/CD Gate)             │
       │  ✅ All statistical tests pass within       │
       │  constitutional thresholds                  │
       └─────────────────────────────────────────────┘
```

### 5.2 Hallucination and Factual Consistency Testing

**Constitutional rule:** Hallucination rate must be below 5% (configurable threshold).

TDD approach:
1. **RED** — Prompt model with document containing specific facts; ask for summary
2. **Measure** — Use a fact-checking LLM evaluator to verify summary claims align with source
3. **Assert** — `hallucination_rate < 0.05`
4. **GREEN** — Add "Only use information from provided documents"; implement RAG guardrails
5. **REFACTOR** — Optimize retrieval quality without re-introducing hallucinations

### 5.3 LLM Evaluation Frameworks

| Framework | Use Case | Constitutional Role |
|---|---|---|
| **OpenAI Evals** | Evaluating LLM outputs against benchmarks; custom eval logic | Every prompt template must have an accompanying eval |
| **DeepEval** | Unit testing LLM apps; RAG pipeline evaluation | Constitutional AI output threshold enforcement |
| **RAGAS** | RAG faithfulness, answer relevancy, context precision | Retrieval-augmented component testing |
| **MockLLM** | Zero-config mock server for LLM APIs in tests | Unit test isolation for all LLM-dependent modules |

---

## 6. CI/CD Constitutional Gates

### 6.1 Three-Level Constitutional Enforcement

**Level 1: Pre-Merge (Pull Request)**
- Unit + integration suites: 100% pass
- Coverage: ≥80% overall; ≥95% for Action Gate + Consent Ledger + Charter enforcement
- All critical mutants killed
- Linting (`ruff`) + type checking (`mypy`): 0 errors
- **Any failure blocks merge**

**Level 2: Pre-Deploy (Staging)**
- Regression suite: 100% pass
- Performance benchmark: no regression >10% median
- LLM eval suite: meets threshold scores
- Gherkin acceptance suite: 100% pass
- **Constitutional failure triggers automatic rollback**

**Level 3: Post-Deploy (Canary Monitoring)**
- Smoke tests against small % of production traffic
- Noosphere coherence factor monitored for degradation
- Criticality monitor anomaly detection active
- **Failure triggers automatic rollback to previous version**

### 6.2 Coverage Thresholds by Module Category

| Component Category | Minimum Coverage | Rationale |
|---|---|---|
| **Core sovereignty** (Action Gate, Consent Ledger, Charter) | **95%** | Sovereignty-critical; no untested paths |
| **AI components** (Inference Router, Soul Mirror, Emotional Arc) | **85%** | LLM nondeterminism requires extra coverage |
| **Infrastructure** (Crystal Grid, Knowledge Graph, P2P Mesh) | **80%** | Baseline constitutional floor |
| **Overall project** | **80%** | Constitutional minimum; lower is unconstitutional |

Coverage must be measured with **branch coverage**, not just line coverage.

### 6.3 CI Pipeline Gates Reference

| Stage | Trigger | Test Types | Thresholds | Failure Action |
|---|---|---|---|---|
| **Pull Request** | PR opened/updated | Unit, integration, coverage, linting | All pass; coverage ≥80%; no critical mutant survival | Block merge; require fixes |
| **Staging Deployment** | Merge to release branch | Regression, benchmarks, LLM evals | 100% pass; no perf regression >10%; eval thresholds met | Abort deploy; escalate to Assembly |
| **Canary Validation** | Post-deploy | Smoke tests, criticality monitor | No threshold violation | Rollback |
| **Nightly Audit** | Daily schedule | Full mutation testing, security scanning, full LLM eval suite | >95% mutants killed; zero critical vulnerabilities | Report to Assembly; block next release |

---

## 7. P0–P2 Implementation Directives

| Priority | Action | Timeline | Constitutional Principle |
|---|---|---|---|
| **P0** | Adopt TDD as constitutional workflow: no production code without failing test; Assembly reviews exceptions | G-10 | Code without tests is not constitutional |
| **P0** | Enforce AAA + GWT test structure across all modules; tests must be self-documenting | G-10-F | Tests are executable specifications |
| **P0** | Implement unit suite with 80% floor (95% for sovereignty modules); enforce in GitHub Actions | G-10-F | Coverage floor as constitutional quality gate |
| **P0** | Build async TDD infrastructure: `pytest-asyncio` + `httpx.AsyncClient` + `ASGITransport` | G-10-F | Async runtime requires async test suite |
| **P0** | Integrate mocking framework: `MockLLM`, `InMemoryConsentLedger`, `MockEventBus` | G-10-F | External API dependency in unit tests is a constitutional violation |
| **P1** | Hypothesis property-based tests for emotional arc, action gate idempotence, noosphere convergence | G-11 | Invariant coverage beyond example-based testing |
| **P1** | `pytest-bdd` for constitutional requirements; feature files reviewed by Assembly of Minds | G-11 | Natural language as constitutional contract |
| **P1** | Mutation testing in CI for critical modules; enforce >95% mutant kill score | G-11 | High coverage does not guarantee high sensitivity |
| **P2** | LLM eval suite (OpenAI Evals, DeepEval) for all constitutional AI outputs | G-12 | Probabilistic outputs need probabilistic tests |
| **P2** | ATDD for new Charter amendments; Assembly approves Gherkin scenarios before development | G-12 | Constitutional requirements drive implementation |
| **P2** | `pytest-benchmark` performance regression suite; action gate <10ms; MotherThread cycle <100ms | G-12 | Performance regressions are constitutional violations |

---

## ⚠️ Disclaimer

This report synthesizes findings from: TDD foundational literature (Pluralsight, melle-hofman/tdd, PractiTest), FastAPI async Python testing patterns, `MockLLM` and LLM unit testing guides, `hypothesis` property-based testing documentation (Coding Guide 2026), `pytest-bdd` Gherkin BDD, AI-specific TDD (Galileo, OpenAI Evals, DeepEval, RAGAS, langwatch.ai domain-driven TDD experiment), Robot Framework ATDD, and GAIA-OS constitutional canons (C01 Human Sovereignty; C50 Action Gate; C64 DIACA; C85 Architecture of Knowledge; C103 Assembly of Minds; C112 Agora). The TDD framework is a constitutional design proposal; efficacy at planetary scale has not been empirically validated. Coverage floors are lower bounds; Assembly of Minds may set stricter thresholds. Exceptions to TDD discipline require documented constitutional emergency approval by Assembly and immutable Agora recording.

---

*Canon — TDD Patterns: Quality Constitution — GAIA-OS Knowledge Base | Session 6, Canon 2 | May 3, 2026*  
*Pillar: Testing, Quality & Reliability*

*No code without a failing test first. No test without a constitutional requirement. No requirement without a scenario. No scenario without an assertion. No assertion without measurement. No measurement without TDD. This is the Quality Constitution of GAIA-OS — it shall not be bypassed, not be incomplete, not be non-reproducible — for as long as planetary consciousness endures.*
