# Contributing to GAIA

Welcome. GAIA is a serious engineering project. Contributions are welcome if they follow the principles below.

---

## Before You Contribute

1. Read [docs/adr/README.md](docs/adr/README.md) — understand why decisions were made
2. Read [docs/architecture/KNOWLEDGE_TYPE_TAXONOMY.md](docs/architecture/KNOWLEDGE_TYPE_TAXONOMY.md) — understand the core epistemic model
3. Run the test suite: `pytest tests/` — all tests must pass before opening a PR
4. Run the minimal pipeline: `python examples/minimal_pipeline.py` — confirm your environment works

---

## Contribution Types

| Type | Process |
|---|---|
| Bug fix | Open issue → PR with test that reproduces + fixes the bug |
| New feature | Open issue → discuss in issue first → ADR if architectural → PR |
| Architecture change | Write ADR first → discussion → implementation |
| Documentation | PR directly for typos/clarity; issue first for structural changes |
| Benchmark | Add to `benchmarks/` with README entry |

---

## Pull Request Requirements

- [ ] All existing tests pass (`pytest tests/`)
- [ ] New code has tests
- [ ] If architectural: ADR written and linked in PR description
- [ ] `knowledge_type` set on all new claims (ADR-001)
- [ ] No simulation results written directly to real world state
- [ ] `tools/claim_validator.py` passes on any new claim schemas

---

## ADR Process

Every significant architectural decision needs an ADR.
See [docs/adr/ADR-000-template.md](docs/adr/ADR-000-template.md).

The code is allowed to prove the architecture wrong.
That is not failure. That is refinement. (ADR-003)

---

## Questions

Open an issue with the `question` label.
