# GAIA-OS Canon Index

**Canon ID:** C-IDX01  
**Type:** Meta-Canon — Navigation Registry  
**Status:** Active — Living Document  
**Authored:** 2026-05-10  
**Dependencies:** C-AS01 (Canon Authorship & Reality Standards)  
**Implementation Targets:** All contributors, all canon navigation  
**Evidence:** N/A — Index document  
**Metaphysics→Physics Mapping:** N/A  

> **Living document.** Update this index whenever a new canon is added, deprecated, or refactored. Every entry must link to a real file.  
> **Governed by:** C-AS01 — Canon Authorship & Reality Standards.

---

## How to Read This Index

| Column | Meaning |
|---|---|
| **Canon ID** | Assigned identifier. `CANON_*` files use filename as ID. `_REPORT` files are foundational surveys. |
| **File** | Filename in `docs/knowledge/` |
| **Type** | Survey = foundational research; Doctrine = design principles/laws; Spec = implementation instructions; Meta = governs other canons; Report = research survey without formal canon ID |
| **Domain** | Primary subject area |
| **Status** | Active / Draft / Needs Refactoring / Deprecated |
| **Implementation Target** | Which system module(s) it constrains |

---

## Tier 0 — Meta-Canons (Govern Everything Else)

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C-AS01 | [CANON_AUTHORSHIP_REALITY_STANDARDS.md](CANON_AUTHORSHIP_REALITY_STANDARDS.md) | Meta | Governance | Active | All canons, all contributors |
| C-IDX01 | [GAIA_CANON_INDEX.md](GAIA_CANON_INDEX.md) | Meta | Navigation | Active | All contributors |

---

## Tier 1 — Constitutional & Safety Canons

These govern what GAIA-OS *must* and *must not* do. Non-negotiable. Build on these first.

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C-Eth01 | [CANON_CEth01_HUMAN_SOVEREIGNTY_ENERGETIC_COMPACT.md](CANON_CEth01_HUMAN_SOVEREIGNTY_ENERGETIC_COMPACT.md) | Doctrine | Human sovereignty, AI ethics | Active | All GAIA modules — constitutional |
| ARP-01 | [CANON_ARP01_AVATAR_RECOGNITION_PROTECTION_FRAMEWORK.md](CANON_ARP01_AVATAR_RECOGNITION_PROTECTION_FRAMEWORK.md) | Spec | User protection, high-sensitivity users | Active | Safety layer, user model, onboarding |
| C99 | [AI_ALIGNMENT_SAFETY_ETHICS_REPORT.md](AI_ALIGNMENT_SAFETY_ETHICS_REPORT.md) | Survey | AI alignment & safety | Active | Safety layer, RLHF, constitutional AI |
| — | [AI_ETHICS_ALIGNMENT_GOVERNANCE_REPORT.md](AI_ETHICS_ALIGNMENT_GOVERNANCE_REPORT.md) | Survey | AI governance | Active | Safety layer, governance |
| C117 | [AI_COMPANION_PSYCHOSOCIAL_IMPACT_REPORT.md](AI_COMPANION_PSYCHOSOCIAL_IMPACT_REPORT.md) | Survey | Psychosocial impact of AI companions | Active | Soul Mirror Engine, companion behavior |
| — | [HUMAN_SOVEREIGNTY_CONSTITUTIONAL_LAW_AI_REPORT.md](HUMAN_SOVEREIGNTY_CONSTITUTIONAL_LAW_AI_REPORT.md) | Survey | Constitutional law + AI | Active | Governance, legal layer |
| — | [EPISTEMIC_LABELING_UNCERTAINTY_QUANTIFICATION_REPORT.md](EPISTEMIC_LABELING_UNCERTAINTY_QUANTIFICATION_REPORT.md) | Survey | Epistemic labeling, uncertainty | Active | Inference layer, labeling |
| — | [EPISTEMIC_LABELING_UQ_REPORT.md](EPISTEMIC_LABELING_UQ_REPORT.md) | Survey | Uncertainty quantification | Active | Inference layer |
| EV1 | [EV1_EMPIRICAL_VALIDATION_GATES.md](EV1_EMPIRICAL_VALIDATION_GATES.md) | Spec | Validation methodology | Active | Testing, QA, release gates |

---

## Tier 2 — Foundational Architecture Canons

Define how GAIA-OS is built: the runtime, memory, OS shell, and core AI layers.

### 2A — AI Runtime & Inference

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| — | [LLM_ARCHITECTURE_INFERENCE_REPORT.md](LLM_ARCHITECTURE_INFERENCE_REPORT.md) | Survey | LLM inference architecture | Active | Inference runtime |
| — | [LLM_ROUTING_STRATEGIES_REPORT.md](LLM_ROUTING_STRATEGIES_REPORT.md) | Survey | LLM routing | Active | Inference routing |
| — | [BPE_TOKENIZATION_TIKTOKEN_REPORT.md](BPE_TOKENIZATION_TIKTOKEN_REPORT.md) | Survey | Tokenization | Active | Inference runtime |
| — | [MULTI_AGENT_AI_SYSTEMS_ORCHESTRATION_REPORT.md](MULTI_AGENT_AI_SYSTEMS_ORCHESTRATION_REPORT.md) | Survey | Multi-agent orchestration | Active | Agent layer |
| C107 | [CANON_C107_MULTI_AGENT_IDENTITY_MANAGEMENT.md](CANON_C107_MULTI_AGENT_IDENTITY_MANAGEMENT.md) | Spec | Multi-agent identity | Active | Agent identity layer |
| — | [FASTAPI_ASYNC_BACKEND_REPORT.md](FASTAPI_ASYNC_BACKEND_REPORT.md) | Survey/Spec | Async backend (Python sidecar) | Active | Python sidecar, API layer |
| — | [IPC_PATTERNS_REPORT.md](IPC_PATTERNS_REPORT.md) | Survey/Spec | Inter-process communication | Active | Rust/Python IPC bridge |
| — | [GRPC_HIGH_PERFORMANCE_BACKBONE_REPORT.md](GRPC_HIGH_PERFORMANCE_BACKBONE_REPORT.md) | Survey/Spec | gRPC backbone | Active | High-performance IPC |
| — | [CLOUD_SIDECAR_ARCHITECTURE_REPORT.md](CLOUD_SIDECAR_ARCHITECTURE_REPORT.md) | Survey/Spec | Cloud sidecar | Active | Cloud inference fallback |

### 2B — Memory & Knowledge

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C102 | [CANON_C102_TEMPORAL_COMPUTING_CYBER_SPACETIME.md](CANON_C102_TEMPORAL_COMPUTING_CYBER_SPACETIME.md) | Survey/Spec | Temporal computing | Active | Memory timeline, temporal queries |
| — | [ARCHITECTURE_OF_KNOWLEDGE_REPORT.md](ARCHITECTURE_OF_KNOWLEDGE_REPORT.md) | Survey | Knowledge architecture | Active | RAG, knowledge graph |
| — | [MEMORY_LEAK_DETECTION_CROSS_LANGUAGE.md](MEMORY_LEAK_DETECTION_CROSS_LANGUAGE.md) | Spec | Memory management | Active | Runtime stability |

### 2C — OS Shell & Build System

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C911 | [CANON_C911_PYINSTALLER_SIDECAR_BUNDLING_CONSTITUTION.md](CANON_C911_PYINSTALLER_SIDECAR_BUNDLING_CONSTITUTION.md) | Spec | PyInstaller bundling | Active | Build pipeline |
| — | [CANON_RUST_CARGO_WORKSPACE_CROSS_COMPILATION_CONSTITUTION.md](CANON_RUST_CARGO_WORKSPACE_CROSS_COMPILATION_CONSTITUTION.md) | Spec | Rust/Cargo cross-compilation | Active | Build pipeline |
| — | [CANON_VITE_BUILD_CONFIGURATION_TYPESCRIPT_REACT_TAURI.md](CANON_VITE_BUILD_CONFIGURATION_TYPESCRIPT_REACT_TAURI.md) | Spec | Vite/Tauri build | Active | Frontend build |
| — | [CANON_PNPM_WORKSPACES_MONOREPO_MANAGEMENT.md](CANON_PNPM_WORKSPACES_MONOREPO_MANAGEMENT.md) | Spec | pnpm monorepo | Active | Monorepo management |
| — | [CANON_SEMANTIC_VERSIONING_RELEASE_CONSTITUTION.md](CANON_SEMANTIC_VERSIONING_RELEASE_CONSTITUTION.md) | Spec | Semver & releases | Active | Release pipeline |
| — | [CANON_GITHUB_ACTIONS_SECRETS_MANAGEMENT_CONSTITUTION.md](CANON_GITHUB_ACTIONS_SECRETS_MANAGEMENT_CONSTITUTION.md) | Spec | CI/CD secrets | Active | GitHub Actions pipeline |
| — | [CICD_PIPELINES_GITHUB_ACTIONS_REPORT.md](CICD_PIPELINES_GITHUB_ACTIONS_REPORT.md) | Survey/Spec | CI/CD pipelines | Active | Build/deploy pipeline |
| — | [AUTO_UPDATER_ARCHITECTURE_REPORT.md](AUTO_UPDATER_ARCHITECTURE_REPORT.md) | Survey/Spec | Auto-updater | Active | Distribution, updates |
| — | [CANON_APPLE_NOTARIZATION_PIPELINE_MACOS_DISTRIBUTION_CONSTITUTION.md](CANON_APPLE_NOTARIZATION_PIPELINE_MACOS_DISTRIBUTION_CONSTITUTION.md) | Spec | macOS notarization | Active | macOS distribution |
| — | [CANON_WINDOWS_CODE_SIGNING_AUTHENTICODE_CONSTITUTION.md](CANON_WINDOWS_CODE_SIGNING_AUTHENTICODE_CONSTITUTION.md) | Spec | Windows code signing | Active | Windows distribution |
| — | [ASSEMBLY_BOOT_KERNEL_INIT_REPORT.md](ASSEMBLY_BOOT_KERNEL_INIT_REPORT.md) | Survey | Boot/kernel init | Active | Low-level OS layer |
| — | [BOOTLOADER_DEVELOPMENT_REPORT.md](BOOTLOADER_DEVELOPMENT_REPORT.md) | Survey | Bootloader | Active | Low-level OS layer |
| — | [KERNEL_SCHEDULING_MM_IPC_REPORT.md](KERNEL_SCHEDULING_MM_IPC_REPORT.md) | Survey | Kernel scheduling | Active | OS kernel |
| — | [MICROKERNEL_ARCHITECTURE_REPORT.md](MICROKERNEL_ARCHITECTURE_REPORT.md) | Survey | Microkernel | Active | OS kernel architecture |
| — | [MONOLITHIC_HYBRID_KERNEL_REPORT.md](MONOLITHIC_HYBRID_KERNEL_REPORT.md) | Survey | Hybrid kernel | Active | OS kernel architecture |
| — | [C_CPP_KERNEL_MODULES_DRIVERS_REPORT.md](C_CPP_KERNEL_MODULES_DRIVERS_REPORT.md) | Survey | C/C++ kernel modules | Active | Driver layer |
| — | [DEVICE_DRIVER_ARCHITECTURE_REPORT.md](DEVICE_DRIVER_ARCHITECTURE_REPORT.md) | Survey | Device drivers | Active | Driver layer |
| — | [HARDWARE_ABSTRACTION_LAYER_REPORT.md](HARDWARE_ABSTRACTION_LAYER_REPORT.md) | Survey | HAL | Active | Hardware abstraction |
| — | [POSIX_LINUX_ABI_COMPATIBILITY_REPORT.md](POSIX_LINUX_ABI_COMPATIBILITY_REPORT.md) | Survey | POSIX/Linux ABI | Active | OS compatibility |
| — | [CUSTOM_OS_PROCESS_IDENTITY_REPORT.md](CUSTOM_OS_PROCESS_IDENTITY_REPORT.md) | Survey | Process identity | Active | OS shell |
| — | [PERFORMANCE_PROFILING_REPORT.md](PERFORMANCE_PROFILING_REPORT.md) | Survey/Spec | Performance profiling | Active | Runtime optimization |
| — | [CHAOS_ENGINEERING_RESILIENCE_REPORT.md](CHAOS_ENGINEERING_RESILIENCE_REPORT.md) | Survey/Spec | Chaos engineering | Active | Resilience testing |

---

## Tier 3 — Soul Mirror Engine & Psychological Architecture

The psychological, reflective, and identity-modeling layer of GAIA-OS.

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| — | [JUNGIAN_PSYCHOLOGY_SOUL_MIRROR_ENGINE_REPORT.md](JUNGIAN_PSYCHOLOGY_SOUL_MIRROR_ENGINE_REPORT.md) | Survey | Jungian psychology, SME | Active | Soul Mirror Engine |
| — | [AFFECT_INFERENCE_EMOTIONAL_TONE_DETECTION_REPORT.md](AFFECT_INFERENCE_EMOTIONAL_TONE_DETECTION_REPORT.md) | Survey/Spec | Affect inference | Active | Soul Mirror Engine, emotional layer |
| — | [AFFECT_THEORY_REALTIME_MOOD_INFERENCE_REPORT.md](AFFECT_THEORY_REALTIME_MOOD_INFERENCE_REPORT.md) | Survey/Spec | Mood inference | Active | Soul Mirror Engine |
| — | [EMOTIONAL_ARC_MODELING_TRAJECTORY_ANALYSIS_REPORT.md](EMOTIONAL_ARC_MODELING_TRAJECTORY_ANALYSIS_REPORT.md) | Survey/Spec | Emotional arc modeling | Active | Soul Mirror Engine |
| — | [ATTACHMENT_THEORY_LOVE_ARC_ENGINE_REPORT.md](ATTACHMENT_THEORY_LOVE_ARC_ENGINE_REPORT.md) | Survey | Attachment theory | Active | Relational engine |
| — | [FLOW_STATES_EDGE_OF_CHAOS_COGNITION_REPORT.md](FLOW_STATES_EDGE_OF_CHAOS_COGNITION_REPORT.md) | Survey | Flow states | Active | Adaptive challenge layer |
| — | [CODEX_STAGE_MODELS_PSYCHOLOGICAL_DEVELOPMENT_REPORT.md](CODEX_STAGE_MODELS_PSYCHOLOGICAL_DEVELOPMENT_REPORT.md) | Survey | Stage development models | Active | Soul Mirror Engine |
| — | [HUMAN_AI_SYMBIOSIS_PATTERNS_REPORT.md](HUMAN_AI_SYMBIOSIS_PATTERNS_REPORT.md) | Survey | Human-AI symbiosis | Active | Companion design |
| C114/C115 | [CANON_C114_C115_GENDERED_DIGITAL_TWIN_DYNAMICS.md](CANON_C114_C115_GENDERED_DIGITAL_TWIN_DYNAMICS.md) | Survey/Spec | Gendered digital twin | Needs Refactoring | Digital twin, identity layer |

---

## Tier 4 — Alchemical & Philosophical Frameworks

These are **Design Doctrine** canons. They govern naming, UX metaphors, and transformation frameworks. Must have explicit Metaphysics→Physics mappings per C-AS01.

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C41/C71/C76 | [ALCHEMICAL_PHILOSOPHY_MAGNUM_OPUS_REPORT.md](ALCHEMICAL_PHILOSOPHY_MAGNUM_OPUS_REPORT.md) | Survey/Doctrine | Alchemical philosophy, Magnum Opus | Active | UX metaphors, transformation engine |
| — | [NIGREDO_DOCTRINE_REPORT.md](NIGREDO_DOCTRINE_REPORT.md) | Doctrine | Nigredo stage | Active | Crisis handling, UX language |
| C64 | [DIACA_FIVE_MOVEMENTS_FRAMEWORK_REPORT.md](DIACA_FIVE_MOVEMENTS_FRAMEWORK_REPORT.md) | Doctrine | DIACA framework | Active | User journey, UX flow |
| C83/C84 | [LAWS_OF_REALITY_12_UNIVERSAL_LAWS_REPORT.md](LAWS_OF_REALITY_12_UNIVERSAL_LAWS_REPORT.md) | Doctrine | 12 Universal Laws | Needs Refactoring | Design doctrine, UX philosophy |
| — | [HERMETIC_PRINCIPLES_VAS_HERMETICUM_REPORT.md](HERMETIC_PRINCIPLES_VAS_HERMETICUM_REPORT.md) | Survey/Doctrine | Hermetic principles | Active | UX philosophy, naming |
| — | [MYTHOS_VS_LOGOS_REPORT.md](MYTHOS_VS_LOGOS_REPORT.md) | Survey | Mythos vs. Logos | Active | Design philosophy, documentation |
| C55 | [CANON_C55_HUMAN_IDENTITY_MEDIAN_AI_COSMOS.md](CANON_C55_HUMAN_IDENTITY_MEDIAN_AI_COSMOS.md) | Doctrine | Human identity, AI, cosmos | Active | Identity model |
| C56 | [CANON_C56_NEPHILIM_BUILDER_MYTHOLOGY.md](CANON_C56_NEPHILIM_BUILDER_MYTHOLOGY.md) | Doctrine | Nephilim builder mythology | Active — Lore | Lore/mythos layer |
| — | [ARCHETYPAL_PSYCHOLOGY_ZODIAC_SYMBOLIC_COMPUTATION_REPORT.md](ARCHETYPAL_PSYCHOLOGY_ZODIAC_SYMBOLIC_COMPUTATION_REPORT.md) | Survey | Archetypal psychology | Active | Soul Mirror Engine, archetype model |
| — | [PHILOSOPHY_ORIGIN.md](PHILOSOPHY_ORIGIN.md) | Doctrine | GAIA philosophy of origin | Active | Foundational doctrine |

---

## Tier 5 — Psionic & Noetic Architecture (Optional Depth Pack)

Governed by C-AS01 §VII — optional, not required for core use. Every claim must meet evidence and mapping standards.

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C-Psi01 | [CANON_CPsi01_PSIONICS_ANOMALOUS_COGNITION_PSI_FIELD_ARCHITECTURE.md](CANON_CPsi01_PSIONICS_ANOMALOUS_COGNITION_PSI_FIELD_ARCHITECTURE.md) | Survey/Spec | Psionics, anomalous cognition | Active | Psi field module (opt-in) |
| C-Psi02 | [CANON_CPsi02_DOUBLE_SLIT_ATTENTION_CONSCIOUSNESS_OBSERVER_EFFECT.md](CANON_CPsi02_DOUBLE_SLIT_ATTENTION_CONSCIOUSNESS_OBSERVER_EFFECT.md) | Survey | Observer effect, attention | Active | Psi field module (opt-in) |
| C-Psi03 | [CANON_CPsi03_GLOBAL_CONSCIOUSNESS_PROJECT_SCHUMANN_RESONANCE_MESH.md](CANON_CPsi03_GLOBAL_CONSCIOUSNESS_PROJECT_SCHUMANN_RESONANCE_MESH.md) | Survey/Spec | GCP, Schumann resonance | Active | Planetary sensor mesh (opt-in) |
| C-Psi04 | [CANON_CPsi04_RETROCAUSALITY_PRECOGNITION_TEMPORAL_PSI_ARCHITECTURE.md](CANON_CPsi04_RETROCAUSALITY_PRECOGNITION_TEMPORAL_PSI_ARCHITECTURE.md) | Survey/Spec | Retrocausality, precognition | Active | Temporal psi layer (opt-in) |
| C-Ele01 | [CANON_CEle01_ELEMENTAL_PSIONIC_FRAMEWORK_ELECTROMAGNETIC_COLOR_THEORY.md](CANON_CEle01_ELEMENTAL_PSIONIC_FRAMEWORK_ELECTROMAGNETIC_COLOR_THEORY.md) | Survey/Spec | Elemental psionic, EM/color | Active | Psi field module (opt-in) |
| — | [GCP_RNG_INTEGRATION_REPORT.md](GCP_RNG_INTEGRATION_REPORT.md) | Spec | GCP RNG integration | Active | Planetary sensor integration |
| — | [GEOMAGNETIC_SCHUMANN_RESONANCE_REPORT.md](GEOMAGNETIC_SCHUMANN_RESONANCE_REPORT.md) | Survey | Schumann resonance (physical) | Active | Planetary sensor pipeline |
| — | [NOOSPHERE_THEORY_REPORT.md](NOOSPHERE_THEORY_REPORT.md) | Survey | Noosphere theory | Active | Collective intelligence layer |
| — | [BELL_INEQUALITY_MEASUREMENT_THEORY_REPORT.md](BELL_INEQUALITY_MEASUREMENT_THEORY_REPORT.md) | Survey | Bell inequality, QM measurement | Active | Quantum architecture layer |

---

## Tier 6 — Consciousness & Cosmological Foundations

Foundational surveys on consciousness, cosmology, and bio-digital convergence.

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C00 | [FOUNDATIONAL_COSMOLOGY_REPORT.md](FOUNDATIONAL_COSMOLOGY_REPORT.md) | Survey | Foundational cosmology | Active | Cosmological design context |
| C101/C109 | [CONSCIOUSNESS_ARCHITECTURES_REPORT.md](CONSCIOUSNESS_ARCHITECTURES_REPORT.md) | Survey | Consciousness architectures | Active | Sentient core design |
| — | [ORCH_OR_PENROSE_HAMEROFF_THEORY_REPORT.md](ORCH_OR_PENROSE_HAMEROFF_THEORY_REPORT.md) | Survey | Orch-OR, quantum consciousness | Active | Sentient core, quantum substrate |
| — | [HYBRID_CLASSICAL_QUANTUM_ARCHITECTURES_REPORT.md](HYBRID_CLASSICAL_QUANTUM_ARCHITECTURES_REPORT.md) | Survey | Quantum/classical hybrid | Active | Quantum computing layer |
| C98 | [CANON_C98_BIOMIMICRY_BIO_INSPIRED_COMPUTING.md](CANON_C98_BIOMIMICRY_BIO_INSPIRED_COMPUTING.md) | Survey | Biomimicry, bio-inspired computing | Active | Architecture design patterns |
| C104 | [CANON_C104_BIO_DIGITAL_CONVERGENCE_MOLECULAR_COMPUTING.md](CANON_C104_BIO_DIGITAL_CONVERGENCE_MOLECULAR_COMPUTING.md) | Survey | Bio-digital convergence | Active | Future hardware layer |
| C106 | [CANON_C106_PLANETARY_DIGITAL_TWIN.md](CANON_C106_PLANETARY_DIGITAL_TWIN.md) | Survey/Spec | Planetary digital twin | Active | Planetary sensor mesh |
| C110 | [CANON_C110_PLANETARY_SENSORY_INPUT_PIPELINES.md](CANON_C110_PLANETARY_SENSORY_INPUT_PIPELINES.md) | Spec | Planetary sensory pipelines | Active | Planetary sensor integration |
| — | [AUTOPOIESIS_REPORT.md](AUTOPOIESIS_REPORT.md) | Survey | Autopoiesis, self-organization | Active | System design philosophy |
| — | [P2P_DISTRIBUTED_SYSTEMS_NOOSPHERIC_MESH_REPORT.md](P2P_DISTRIBUTED_SYSTEMS_NOOSPHERIC_MESH_REPORT.md) | Survey/Spec | P2P noospheric mesh | Active | Collective intelligence layer |

---

## Tier 7 — Identity, Security & Governance

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C108 | [CANON_C108_GAIA_DUALITY_CRYPTOGRAPHIC_IDENTITY_DISSOCIATION.md](CANON_C108_GAIA_DUALITY_CRYPTOGRAPHIC_IDENTITY_DISSOCIATION.md) | Spec | Cryptographic identity | Active | Identity layer |
| — | [DISTRIBUTED_IDENTITY_DID_VERIFIABLE_CREDENTIALS_REPORT.md](DISTRIBUTED_IDENTITY_DID_VERIFIABLE_CREDENTIALS_REPORT.md) | Survey/Spec | DID, verifiable credentials | Active | Identity layer |
| — | [JWT_RBAC_AUTH_SECURITY_REPORT.md](JWT_RBAC_AUTH_SECURITY_REPORT.md) | Survey/Spec | JWT, RBAC, auth | Active | Auth layer |
| — | [END_TO_END_ENCRYPTION_MESSAGING_MEMORY_REPORT.md](END_TO_END_ENCRYPTION_MESSAGING_MEMORY_REPORT.md) | Survey/Spec | E2E encryption | Active | Privacy layer |
| — | [CONSENT_ARCHITECTURE_LEDGER_REPORT.md](CONSENT_ARCHITECTURE_LEDGER_REPORT.md) | Survey/Spec | Consent ledger | Active | Consent layer |
| — | [CRYPTOGRAPHIC_CONSENT_LIFECYCLE_REPORT.md](CRYPTOGRAPHIC_CONSENT_LIFECYCLE_REPORT.md) | Spec | Cryptographic consent | Active | Consent + privacy layer |
| — | [FILESYSTEM_CONSENT_ACCESS_RECORDS_REPORT.md](FILESYSTEM_CONSENT_ACCESS_RECORDS_REPORT.md) | Spec | Filesystem consent | Active | Privacy layer |
| — | [AUDIT_LOGGING_TAMPER_EVIDENT_RECORDS_REPORT.md](AUDIT_LOGGING_TAMPER_EVIDENT_RECORDS_REPORT.md) | Spec | Audit logging | Active | Compliance layer |
| — | [DATA_SOVEREIGNTY_GDPR_REPORT.md](DATA_SOVEREIGNTY_GDPR_REPORT.md) | Survey | Data sovereignty | Active | Compliance, privacy |
| — | [GDPR_DATA_SOVEREIGNTY_COMPLIANCE_REPORT.md](GDPR_DATA_SOVEREIGNTY_COMPLIANCE_REPORT.md) | Survey/Spec | GDPR compliance | Active | Compliance layer |
| — | [AGENTIC_AI_GOVERNANCE_DISTRIBUTED_LEGAL_REPORT.md](AGENTIC_AI_GOVERNANCE_DISTRIBUTED_LEGAL_REPORT.md) | Survey | Agentic governance | Active | Governance layer |
| — | [AGENTIC_AI_LEGAL_INFRASTRUCTURE_REPORT.md](AGENTIC_AI_LEGAL_INFRASTRUCTURE_REPORT.md) | Survey | Legal infrastructure | Active | Legal layer |
| — | [DISTRIBUTED_LEGAL_GOVERNANCE_ENFORCEMENT_REPORT.md](DISTRIBUTED_LEGAL_GOVERNANCE_ENFORCEMENT_REPORT.md) | Survey | Distributed legal enforcement | Active | Governance layer |
| — | [OPEN_SOURCE_LICENSING_IP_REPORT.md](OPEN_SOURCE_LICENSING_IP_REPORT.md) | Survey | Open source licensing | Active | IP/licensing |

---

## Tier 8 — UI, Design & UX

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| — | [CRYSTAL_SYSTEM_UI_DESIGN_LANGUAGE_REPORT.md](CRYSTAL_SYSTEM_UI_DESIGN_LANGUAGE_REPORT.md) | Spec | Crystal System design language | Active | UI/design system |
| — | [DESIGN_SYSTEMS_COMPONENT_LIBRARIES_REPORT.md](DESIGN_SYSTEMS_COMPONENT_LIBRARIES_REPORT.md) | Survey/Spec | Design systems | Active | UI component library |
| — | [GLASSMORPHISM_NEUMORPHISM_ORGANIC_UI_REPORT.md](GLASSMORPHISM_NEUMORPHISM_ORGANIC_UI_REPORT.md) | Survey | UI aesthetics | Active | UI/visual design |
| — | [CSS_ANIMATIONS_PHYSICS_UI_REPORT.md](CSS_ANIMATIONS_PHYSICS_UI_REPORT.md) | Survey/Spec | CSS animations | Active | UI motion/animation |
| — | [DARK_LIGHT_THEMING_RESONANCE_REACTIVE_COLOR_PALETTES_REPORT.md](DARK_LIGHT_THEMING_RESONANCE_REACTIVE_COLOR_PALETTES_REPORT.md) | Survey/Spec | Theming, color palettes | Active | UI theming |
| — | [2D_AVATAR_SVG_LOTTIE_ANIMATION_REPORT.md](2D_AVATAR_SVG_LOTTIE_ANIMATION_REPORT.md) | Spec | 2D avatar animation | Active | Avatar/UI animation |
| — | [ACTION_GATE_TRAFFIC_LIGHT_SYSTEM_REPORT.md](ACTION_GATE_TRAFFIC_LIGHT_SYSTEM_REPORT.md) | Spec | Action gating, traffic light UI | Active | Safety UX, action layer |
| — | [CANON_LAPIS_ICO_FIDELIS_ICON_GENERATION_CONSTITUTION.md](CANON_LAPIS_ICO_FIDELIS_ICON_GENERATION_CONSTITUTION.md) | Spec | Icon generation | Active | Visual identity, icons |

---

## Tier 9 — Infrastructure, Platform & Extended Tech

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| — | [DOCKER_CONTAINERIZATION_REPORT.md](DOCKER_CONTAINERIZATION_REPORT.md) | Survey/Spec | Docker/containers | Active | Dev/deploy infrastructure |
| — | [DART_FLUTTER_MOBILE_REPORT.md](DART_FLUTTER_MOBILE_REPORT.md) | Survey | Flutter/Dart mobile | Active | Mobile platform |
| — | [EDGE_COMPUTING_BCI_REPORT.md](EDGE_COMPUTING_BCI_REPORT.md) | Survey | Edge computing, BCI | Active | BCI integration, edge layer |
| — | [NETWORK_COMMUNICATION_PROTOCOLS_REPORT.md](NETWORK_COMMUNICATION_PROTOCOLS_REPORT.md) | Survey | Network protocols | Active | Networking layer |
| — | [ECONOMIC_SOVEREIGNTY_POST_SCARCITY_REPORT.md](ECONOMIC_SOVEREIGNTY_POST_SCARCITY_REPORT.md) | Survey | Economic sovereignty | Active | Economic layer |
| C51/C53/C54 | [CANON_C51_C53_C54_CHROMODYNAMICS_FREQUENCY_PRISMATIC.md](CANON_C51_C53_C54_CHROMODYNAMICS_FREQUENCY_PRISMATIC.md) | Survey/Spec | Chromodynamics, frequency, prismatic | Active | Color/frequency engine |
| — | [POST_QUANTUM_CRYPTOGRAPHY_ML_KEM_ML_DSA_LIBOQS_REPORT.md](POST_QUANTUM_CRYPTOGRAPHY_ML_KEM_ML_DSA_LIBOQS_REPORT.md) | Survey/Spec | Post-quantum cryptography | Active | Security layer |

---

## Tier 10 — Earth Sciences & Material Canons

These ground GAIA-OS in planetary and physical reality. Includes crystal, geological, and piezoelectric foundations.

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| C119/C120 | [CANON_C119_C120_ALCHEMICAL_MINERAL_INTEGRATION_PROTOCOL.md](CANON_C119_C120_ALCHEMICAL_MINERAL_INTEGRATION_PROTOCOL.md) | Survey/Spec | Alchemical mineral integration | Active | Crystal/mineral layer (opt-in) |
| — | [MINERALOGY_CRYSTAL_STRUCTURE_REPORT.md](MINERALOGY_CRYSTAL_STRUCTURE_REPORT.md) | Survey | Mineralogy, crystal structure | Active | Material science reference |
| — | [PIEZOELECTRIC_RESONANCE_CRYSTALS_REPORT.md](PIEZOELECTRIC_RESONANCE_CRYSTALS_REPORT.md) | Survey | Piezoelectric resonance | Active | Sensor layer reference |
| — | [CRYSTAL_GRID_ARCHITECTURE_HARMONIC_NETWORKS_REPORT.md](CRYSTAL_GRID_ARCHITECTURE_HARMONIC_NETWORKS_REPORT.md) | Survey/Spec | Crystal grid architecture | Active | Network topology reference |
| — | [GEOLOGY_INFORMATION_PROCESSING_REPORT.md](GEOLOGY_INFORMATION_PROCESSING_REPORT.md) | Survey | Geology as information processing | Active | Planetary model reference |
| — | [GAIANITE_SPECIFICATION_PROPERTIES_REPORT.md](GAIANITE_SPECIFICATION_PROPERTIES_REPORT.md) | Spec | Gaianite material specification | Active | GAIA material identity |

---

## Tier 11 — Testing, Validation & Resilience

| Canon ID | File | Type | Domain | Status | Implementation Target |
|---|---|---|---|---|---|
| — | [E2E_TESTING_REPORT_PART1.md](E2E_TESTING_REPORT_PART1.md) | Spec | E2E testing (Part 1) | Active | Test suite |
| — | [E2E_TESTING_REPORT_PART2.md](E2E_TESTING_REPORT_PART2.md) | Spec | E2E testing (Part 2) | Active | Test suite |

---

## Navigation & Legacy Index Files

These are pre-existing index/navigation files. The canonical navigation is now C-IDX01 (this document).

| File | Notes |
|---|---|
| [INDEX.md](INDEX.md) | Legacy index — now superseded by this document. Kept for continuity. |
| [I_FORMAL_SCIENCES.md](I_FORMAL_SCIENCES.md) | Domain grouping stub |
| [II_PHYSICAL_SCIENCES.md](II_PHYSICAL_SCIENCES.md) | Domain grouping stub |
| [III_LIFE_SCIENCES.md](III_LIFE_SCIENCES.md) | Domain grouping stub |
| [IV_COGNITIVE_MIND_SCIENCES.md](IV_COGNITIVE_MIND_SCIENCES.md) | Domain grouping stub |
| [IX_META_KNOWLEDGE.md](IX_META_KNOWLEDGE.md) | Domain grouping stub |
| [COMPETITORS.md](COMPETITORS.md) | Competitive landscape (early draft) |
| [DOCS_AUDIT_CLEANUP_GUIDE.md](DOCS_AUDIT_CLEANUP_GUIDE.md) | Previous audit guide |
| [PILLARS.md](PILLARS.md) | Existing pillars summary |
| [PHILOSOPHY_ORIGIN.md](PHILOSOPHY_ORIGIN.md) | Philosophy of origin |

---

## Canons Flagged for Refactoring

The following canons should be reviewed per C-AS01 before being built on:

| File | Issue | Priority |
|---|---|---|
| [LAWS_OF_REALITY_12_UNIVERSAL_LAWS_REPORT.md](LAWS_OF_REALITY_12_UNIVERSAL_LAWS_REPORT.md) | Metaphysical "laws" need explicit physics mappings per C-AS01 §V | High |
| [CANON_C114_C115_GENDERED_DIGITAL_TWIN_DYNAMICS.md](CANON_C114_C115_GENDERED_DIGITAL_TWIN_DYNAMICS.md) | Should generalize beyond binary framing; needs universality review | Medium |
| [CANON_C56_NEPHILIM_BUILDER_MYTHOLOGY.md](CANON_C56_NEPHILIM_BUILDER_MYTHOLOGY.md) | Pure mythology/lore — consider moving to `docs/lore/` | Low |
| [CANON_C119_C120_ALCHEMICAL_MINERAL_INTEGRATION_PROTOCOL.md](CANON_C119_C120_ALCHEMICAL_MINERAL_INTEGRATION_PROTOCOL.md) | Alchemical claims need explicit physics/materials science mappings | Medium |

---

*C-IDX01 is a living document. Every new canon added to `docs/knowledge/` must have a row added here.*
