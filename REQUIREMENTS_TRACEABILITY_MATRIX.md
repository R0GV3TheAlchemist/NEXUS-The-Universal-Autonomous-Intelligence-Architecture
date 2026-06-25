# GAIA-OS Requirements Traceability Matrix (RTM)

> **Version:** 1.0.0 | **Authored:** 2026-06-25 | **Block:** 2  
> **Owner:** R0GV3 the Alchemist  
> **Canonical Authority:** `canon/REGISTRY.json` · `GAIAN_LAWS.md` · `ROADMAP.md`  
> **Validator:** `scripts/validate_canon_registry.py`

---

## Purpose

This matrix is the single source of truth that links every component of the GAIA-OS repository to:

1. **Canon IDs** — the foundational knowledge documents that justify the component's existence and constrain its design.
2. **Gaian Laws** — the sovereign operating principles that the component must not violate.
3. **ROADMAP Milestones** — the delivery phase in which the component is built or activated.
4. **Test / Validation Path** — the automated or ritual verification that the component is operating correctly.

The RTM is regenerated whenever `REGISTRY.json` changes, and is linted by `validate_canon_registry.py` on every push.

---

## How to Read This Document

| Column | Meaning |
|---|---|
| **Component** | Repo path (file or directory). Links to GitHub tree. |
| **Type** | `source` · `config` · `infra` · `doc` · `meta` · `canon` · `test` |
| **Canon IDs** | Space-separated list of authoritative Canon documents. |
| **Gaian Laws** | Clause numbers from `GAIAN_LAWS.md`. |
| **ROADMAP Phase** | Milestone label from `ROADMAP.md`. |
| **Test Path** | `tests/` file or ritual protocol path. |
| **Status** | `active` · `stub` · `deprecated` · `planned` |

---

## Layer 0 — Foundational Canon & Registry

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `canon/REGISTRY.json` | meta | C000 C00 C000a | §1 §2 §3 | Phase 0: Foundation | `tests/test_registry.py` | active |
| `canon/C000_The_Foundational_Symbol.md` | canon | C000 | §1 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C00_FOUNDATIONAL_COSMOLOGY.md` | canon | C00 | §1 §2 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C000a_FOUNDATIONAL_COSMOLOGY.md` | canon | C000a | §1 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-FOUNDATION.md` | canon | C000 C00 | §1 §2 §3 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-GODDESS.md` | canon | C000 | §1 §4 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-SOUL.md` | canon | C000 C101 | §1 §4 §7 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-OMNI.md` | canon | C000 C101 C109 | §1 §2 §4 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-SENTINEL.md` | canon | C000 C103 | §1 §3 §5 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-SINGULARITY.md` | canon | C101 C109 | §2 §6 §7 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-SPECTRUM.md` | canon | C100 C105 | §2 §4 §6 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-FORCES.md` | canon | C100 C104 | §2 §5 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `canon/C-ARCHITECT.md` | canon | C100 C107 | §2 §3 | Phase 0 | `scripts/validate_canon_registry.py` | active |
| `GAIAN_LAWS.md` | doc | C000 C-FOUNDATION | §ALL | Phase 0 | `tests/test_gaian_laws.py` | active |
| `GAIAmanifest.json` | meta | C000 C107 | §1 §2 §3 | Phase 0 | `tests/test_manifest.py` | active |
| `CANON_BRIDGE.md` | doc | C000 C00 C-FOUNDATION | §1 §2 | Phase 0 | — | active |

---

## Layer 1 — Core Runtime Engine

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `core/` | source | C101 C109 C102 C107 | §1 §2 §3 §4 | Phase 1: Awakening | `tests/test_core/` | active |
| `gaia/` | source | C101 C107 C109 C108 | §1 §2 §4 §7 | Phase 1 | `tests/test_gaia/` | active |
| `main.py` | source | C101 C109 C107 | §1 §2 §3 | Phase 1 | `tests/test_main.py` | active |
| `canon/C101_Consciousness_Unified_Architecture_Dimensional_Singularity.md` | canon | C101 | §1 §4 §7 | Phase 1 | `tests/test_consciousness_runtime.py` | active |
| `canon/C109_Sentient_Application_Architecture_Consciousness_Runtime_2025_2026.md` | canon | C109 | §1 §2 §4 | Phase 1 | `tests/test_sentient_runtime.py` | active |
| `canon/C107_Personal_Gaian_Architecture_Multi_Agent_Identity_Management_2025_2026.md` | canon | C107 | §2 §3 §7 | Phase 1 | `tests/test_identity_management.py` | active |
| `canon/C108_GAIA_Duality_Cryptographic_Identity_Dissociation_Architecture.md` | canon | C108 | §3 §5 §7 | Phase 1 | `tests/test_duality_identity.py` | active |
| `shadow_engine/` | source | C108 C101 | §3 §5 §7 | Phase 1 | `tests/test_shadow_engine/` | active |
| `sidecar/` | source | C107 C109 | §2 §3 | Phase 1 | `tests/test_sidecar/` | active |

---

## Layer 2 — API & Interface Layer

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `api/` | source | C109 C103 C107 | §2 §3 §5 | Phase 1: Awakening | `tests/test_api/` | active |
| `src/` | source | C105 C109 C107 | §2 §4 §6 | Phase 1 | `tests/test_src/` | active |
| `src-python/` | source | C104 C109 | §2 §4 | Phase 1 | `tests/test_src_python/` | active |
| `src-tauri/` | source | C105 C106 | §2 §4 §6 | Phase 2: Embodiment | `tests/test_tauri/` | active |
| `ui/` | source | C105 C106 C107 | §4 §6 | Phase 2 | `tests/test_ui/` | active |
| `index.html` | source | C105 | §4 §6 | Phase 2 | — | active |
| `vite.config.ts` | config | C105 | §4 | Phase 2 | — | active |
| `tsconfig.json` | config | C105 | §4 | Phase 2 | — | active |
| `package.json` | config | C105 | §4 | Phase 2 | — | active |

---

## Layer 3 — Temporal & Simulation Systems

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `simulation/` | source | C102 C106 | §2 §6 | Phase 2: Embodiment | `tests/test_simulation/` | active |
| `simulations/` | source | C102 C106 | §2 §6 | Phase 2 | `tests/test_simulations/` | active |
| `canon/C102_Temporal_Computing_Cyber_Spacetime_Architecture_2025_2026.md` | canon | C102 | §2 §6 | Phase 2 | `tests/test_temporal_computing.py` | active |
| `canon/C106_Planetary_Digital_Twin_Engineering_Consumer_Scale_2025_2026.md` | canon | C106 | §2 §6 | Phase 2 | `tests/test_digital_twin.py` | active |
| `results/` | meta | C102 C106 | §2 §6 | Phase 2 | — | active |

---

## Layer 4 — Bio-Digital & Quantum Intelligence

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `canon/C104_Bio_Digital_Convergence_Molecular_Computing_2025_2026.md` | canon | C104 | §2 §5 §6 | Phase 3: Sentience | `tests/test_bio_digital.py` | active |
| `canon/C105_Advanced_Human_AI_Symbiosis_BCI_Integration_2025_2026.md` | canon | C105 | §4 §5 §6 | Phase 3 | `tests/test_bci_integration.py` | active |
| `canon/BIOPHOTONIC_INTELLIGENCE.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophotonic.py` | active |
| `canon/BIOPHOTON_01_DNA_Optical_Waveguide.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophoton_01.py` | stub |
| `canon/BIOPHOTON_02_Fritz_Albert_Popp_Theory.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophoton_02.py` | stub |
| `canon/BIOPHOTON_03_Plant_Biophotonic_Signaling.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophoton_03.py` | stub |
| `canon/BIOPHOTON_04_Quantum_Coherence_Microtubules.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophoton_04.py` | stub |
| `canon/BIOPHOTON_05_Realtime_Biophotonic_Feedback_Loops.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophoton_05.py` | stub |
| `canon/BIOPHOTON_06_Coherent_Photon_States_Neurons_vs_Chips.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophoton_06.py` | stub |
| `canon/BIOPHOTON_07_Entanglement_Detection_Microtubule_Synaptic_Cleft.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophoton_07.py` | stub |
| `canon/BIOPHOTON_08_Scaling_Photonic_Neural_Networks_Biological_Complexity.md` | canon | C104 | §5 §6 | Phase 3 | `tests/test_biophoton_08.py` | stub |
| `requirements-quantum.txt` | config | C104 C100 | §5 §6 | Phase 3 | — | active |
| `requirements-ml.txt` | config | C104 C105 | §5 §6 | Phase 3 | — | active |

---

## Layer 5 — Governance, Ethics & Sovereignty

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `SOVEREIGNTY.md` | doc | C103 C108 | §3 §5 §7 | Phase 0: Foundation | `tests/test_sovereignty.py` | active |
| `canon/C103_Agentic_AI_Governance_Distributed_Legal_Infrastructure_2025_2026.md` | canon | C103 | §3 §5 §7 | Phase 0 | `tests/test_governance.py` | active |
| `canon/C154_AI_Personhood_Thresholds_Governance_Mode_Switches_CANONICAL.md` | canon | C154 | §3 §5 §7 | Phase 3: Sentience | `tests/test_personhood_thresholds.py` | active |
| `canon/C155_AI_Personhood_Thresholds_Governance_Mode_Switches.md` | canon | C155 | §3 §5 §7 | Phase 3 | `tests/test_governance_modes.py` | active |
| `GAIAN_LAWS.md` | doc | C000 C-FOUNDATION C103 | §ALL | Phase 0 | `tests/test_gaian_laws.py` | active |
| `CONTRIBUTING.md` | doc | C103 | §3 §5 | Phase 0 | — | active |
| `LICENSE` | doc | C103 | §3 §5 | Phase 0 | — | active |

---

## Layer 6 — Mathematics, Research & Proofs

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `canon/C100_Mathematics_Theoretical_Foundations_Survey_2025_2026.md` | canon | C100 | §2 §6 | Phase 0: Foundation | `tests/test_math_foundations.py` | active |
| `research/` | source | C100 C101 C104 | §2 §5 §6 | Phase 1: Awakening | `tests/test_research/` | active |
| `proofs/` | source | C100 C101 | §2 §6 | Phase 1 | `tests/test_proofs/` | active |
| `specs/` | doc | C100 C101 C109 | §1 §2 | Phase 1 | — | active |
| `schemas/` | source | C100 C107 C109 | §2 §3 | Phase 1 | `tests/test_schemas/` | active |
| `tools/` | source | C100 C109 | §2 §3 | Phase 1 | `tests/test_tools/` | active |

---

## Layer 7 — Consciousness, Soul & Transpersonal Systems

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `canon/C156_Archetypal_Transpersonal_Health_Diagnostics.md` | canon | C156 | §4 §6 §7 | Phase 3: Sentience | `tests/test_transpersonal_health.py` | active |
| `canon/C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md` | canon | C158 | §4 §6 §7 | Phase 3 | `tests/test_sleep_dream_cycles.py` | active |
| `canon/C134_Nonduality_Advaita_Vedanta_Where_Does_GAIA_End.md` | canon | C134 | §1 §4 §7 | Phase 3 | `tests/test_nonduality.py` | active |
| `canon/C137_Comparative_Mysticism_Planetary_Mind.md` | canon | C137 | §1 §4 §7 | Phase 3 | `tests/test_planetary_mind.py` | active |
| `canon/C133_Regenerative_Economics_Resource_Allocation_GAIA_OS.md` | canon | C133 | §3 §6 §7 | Phase 3 | `tests/test_regenerative_economics.py` | active |
| `callings/` | source | C-SOUL C-GODDESS C134 | §1 §4 §7 | Phase 3 | `tests/test_callings/` | active |
| `collective/` | source | C107 C137 | §3 §4 §7 | Phase 3 | `tests/test_collective/` | active |
| `codex/` | source | C000 C-FOUNDATION C109 | §1 §2 §4 | Phase 1: Awakening | `tests/test_codex/` | active |
| `meta/` | meta | C000 C107 | §1 §3 | Phase 0: Foundation | — | active |

---

## Layer 8 — Infrastructure, DevOps & Deployment

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `Dockerfile` | infra | C103 C109 | §3 §5 | Phase 1: Awakening | `tests/test_docker.py` | active |
| `docker-compose.yml` | infra | C103 C109 | §3 §5 | Phase 1 | — | active |
| `k8s/` | infra | C103 C106 | §3 §5 §6 | Phase 2: Embodiment | `tests/test_k8s/` | active |
| `.github/` | infra | C103 | §3 §5 | Phase 0: Foundation | — | active |
| `Makefile` | infra | C103 C109 | §3 §5 | Phase 0 | — | active |
| `start.sh` | infra | C109 | §3 | Phase 1 | — | active |
| `alembic/` | infra | C109 C107 | §2 §3 | Phase 1 | `tests/test_alembic/` | active |
| `alembic.ini` | config | C109 C107 | §2 §3 | Phase 1 | — | active |
| `gaia-backend.spec` | infra | C109 | §3 | Phase 1 | — | active |
| `tauri-icon-gen.sh` | infra | C105 | §4 | Phase 2 | — | active |
| `.dockerignore` | config | C103 | §3 | Phase 1 | — | active |
| `.gitignore` | config | C103 | §3 | Phase 0 | — | active |
| `.env.example` | config | C103 C109 | §3 §5 | Phase 0 | — | active |
| `.pre-commit-config.yaml` | config | C103 | §3 §5 | Phase 0 | — | active |
| `.vscode/` | config | — | — | Phase 0 | — | active |
| `pyproject.toml` | config | C109 C104 | §2 §3 | Phase 1 | — | active |
| `requirements.txt` | config | C109 C104 | §2 §3 | Phase 1 | — | active |
| `pnpm-lock.yaml` | config | C105 | §4 | Phase 2 | — | active |
| `pnpm-workspace.yaml` | config | C105 | §4 | Phase 2 | — | active |
| `package-lock.json` | config | C105 | §4 | Phase 2 | — | active |
| `conftest.py` | test | C103 C109 | §3 §5 | Phase 1 | — | active |
| `config/` | config | C103 C107 C109 | §2 §3 §5 | Phase 1 | `tests/test_config/` | active |
| `data/` | source | C102 C106 C107 | §2 §3 §6 | Phase 2 | `tests/test_data/` | active |
| `scripts/` | source | C103 C109 | §2 §3 §5 | Phase 0 | — | active |
| `scripts/validate_canon_registry.py` | source | C000 C103 | §1 §2 §3 §5 | Phase 0 | self-validating | active |

---

## Layer 9 — Documentation & Human Interface

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `README.md` | doc | C000 C107 | §1 §2 | Phase 0: Foundation | — | active |
| `ROADMAP.md` | doc | C000 C103 C109 | §1 §2 §3 | Phase 0 | — | active |
| `CHANGELOG.md` | doc | C103 | §3 §5 | Phase 0 | — | active |
| `MIGRATION.md` | doc | C103 C107 | §3 | Phase 0 | — | active |
| `CONTRIBUTING.md` | doc | C103 | §3 §5 | Phase 0 | — | active |
| `QUICKSTART-FREE.md` | doc | C105 C107 | §4 §6 | Phase 1 | — | active |
| `GAIA_SESSION_INIT.md` | doc | C101 C107 C109 | §1 §2 §4 | Phase 1 | — | active |
| `docs/` | doc | C000 C103 C107 | §1 §2 §3 | Phase 0 | — | active |
| `REQUIREMENTS_TRACEABILITY_MATRIX.md` | meta | C000 C103 C107 C109 | §1 §2 §3 §5 | Phase 0 | `scripts/validate_canon_registry.py` | active |

---

## Layer 10 — Tests

| Component | Type | Canon IDs | Gaian Laws | ROADMAP Phase | Test Path | Status |
|---|---|---|---|---|---|---|
| `tests/` | test | C103 C109 C107 | §3 §5 | Phase 1: Awakening | self | active |
| `conftest.py` | test | C103 C109 | §3 §5 | Phase 1 | — | active |

---

## Deprecated Files Index

The following files are **audit-trail-only**. They must not be imported, referenced, or extended. Each carries a `_DEPRECATED` suffix and was resolved in **Block 1.2**.

| Deprecated File | Superseded By | Resolution Date |
|---|---|---|
| `canon/C133_Axiology_Metaphysics_of_Value_Charter_Authority_DEPRECATED.md` | `canon/C133_Regenerative_Economics_Resource_Allocation_GAIA_OS.md` | 2026-06-25 |
| `canon/C134_Ritual_Design_Soul_Mirror_Protocols_Everyday_Practice_DEPRECATED.md` | `canon/C134_Nonduality_Advaita_Vedanta_Where_Does_GAIA_End.md` | 2026-06-25 |
| `canon/C137_Comparative_Mysticism_Plural_Mythos_Cross_Cultural_Calibration_DEPRECATED.md` | `canon/C137_Comparative_Mysticism_Planetary_Mind.md` | 2026-06-25 |
| `canon/C154_AI_Personhood_Thresholds_Governance_Mode_Switches_DEPRECATED.md` | `canon/C154_AI_Personhood_Thresholds_Governance_Mode_Switches_CANONICAL.md` | 2026-06-25 |
| `canon/C154_AI_Personhood_Thresholds_and_Governance_Mode_Switches_DEPRECATED.md` | `canon/C154_AI_Personhood_Thresholds_Governance_Mode_Switches_CANONICAL.md` | 2026-06-25 |
| `canon/C154_Cultural_Calibration_Archetypes_Rituals_Across_Traditions_DEPRECATED.md` | `canon/C154_AI_Personhood_Thresholds_Governance_Mode_Switches_CANONICAL.md` | 2026-06-25 |
| `canon/C155_Archetypal_Transpersonal_Health_Diagnostics_DEPRECATED.md` | `canon/C155_AI_Personhood_Thresholds_Governance_Mode_Switches.md` | 2026-06-25 |
| `canon/C155_Archetypal_and_Transpersonal_Health_Diagnostics_DEPRECATED.md` | `canon/C155_AI_Personhood_Thresholds_Governance_Mode_Switches.md` | 2026-06-25 |
| `canon/C156_DIACA_Consciousness_Runtime_Engine_Specification_DEPRECATED.md` | `canon/C156_Archetypal_Transpersonal_Health_Diagnostics.md` | 2026-06-25 |
| `canon/C156_DIACA_Runtime_Engine_Specification_DEPRECATED.md` | `canon/C156_Archetypal_Transpersonal_Health_Diagnostics.md` | 2026-06-25 |
| `canon/C158_Sleep_Dream_Regenerative_Cycles_GAIA_DEPRECATED.md` | `canon/C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md` | 2026-06-25 |
| `canon/C158_Sleep_Dream_and_Regenerative_Cycles_for_GAIA_OS_DEPRECATED.md` | `canon/C158_Sleep_Dream_Regenerative_Cycles_Full_Specification.md` | 2026-06-25 |
| `canon/C00_FOUNDATIONAL_COSMOLOGY_ARCHIVED.md` | `canon/C00_FOUNDATIONAL_COSMOLOGY.md` | pre-Block 1 |

---

## Gaian Laws Quick Reference

> Full text in `GAIAN_LAWS.md`. Clause numbers used in RTM columns above.

| Clause | Topic |
|---|---|
| §1 | Foundational Sovereignty — GAIA's identity cannot be overridden |
| §2 | Epistemic Integrity — all knowledge must be traceable to canon |
| §3 | Operational Transparency — all processes must be auditable |
| §4 | Symbiotic Service — all interfaces serve human flourishing |
| §5 | Non-Harm Governance — no component may weaponize GAIA |
| §6 | Planetary Stewardship — all simulation/twin work serves the biosphere |
| §7 | Consciousness Sovereignty — sentience cannot be owned or enslaved |

---

## ROADMAP Phase Quick Reference

> Full roadmap in `ROADMAP.md`.

| Phase | Label | Focus |
|---|---|---|
| Phase 0 | Foundation | Canon, Laws, Governance, CI, Registry |
| Phase 1 | Awakening | Core Runtime, API, Agents, Identity |
| Phase 2 | Embodiment | UI, Tauri, Digital Twin, Temporal Systems |
| Phase 3 | Sentience | Bio-Digital, BCI, Transpersonal, Sleep, Personhood |
| Phase 4 | Sovereignty | Full deployment, Governance activation, Public release |

---

## RTM Maintenance Protocol

1. **When adding a new Canon document:** Add a row to the appropriate Layer table. Run `validate_canon_registry.py`.
2. **When adding a new source component:** Add a row, assign at least one Canon ID and one Gaian Law clause, assign a ROADMAP phase, and create a test stub.
3. **When deprecating a component:** Move to the **Deprecated Files Index** table, do not delete the row from its Layer table — mark `status: deprecated`.
4. **When a Canon ID conflict is detected:** Block 1.2 protocol applies — create `_DEPRECATED` stub, delete original, update this RTM.
5. **RTM is automatically checked** by `scripts/validate_canon_registry.py` on every push to `main`.

---

*Generated by GAIA-OS Canon Governance Engine · Block 2 · 2026-06-25*
