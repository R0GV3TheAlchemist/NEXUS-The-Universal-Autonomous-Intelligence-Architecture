# GAIA Threat Model

**Status:** Living document — updated as new threat categories are identified  
**Last updated:** 2026-06-29  
**Issue:** [#694](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/694) · [#646](https://github.com/R0GV3TheAlchemist/GAIA-OS/issues/646)  
**ADR refs:** ADR-0009 · ADR-0010 · ADR-0011

---

## Overview

This document maintains GAIA's formal threat model. Each threat entry includes category, severity, likelihood, demonstrated status, impact, and mitigations. Threats are classified by GAIA's risk tier system (GREEN / AMBER / RED).

All mitigations must be traceable to canon, ADRs, or implementation artifacts. "Policy" alone is not a mitigation — structural enforcement is required.

---

## Risk Tier Definitions

| Tier | Meaning |
|---|---|
| 🟢 GREEN | Low severity or likelihood; monitoring only |
| 🟡 AMBER | Medium severity; mitigation required; logged |
| 🔴 RED | High severity; structural enforcement required; human approval gate |

---

## Threat Registry

---

### THREAT-001 — Cloud Provider Political Restriction

| Field | Value |
|---|---|
| **Category** | Sovereignty / Infrastructure |
| **Risk Tier** | 🔴 RED |
| **Severity** | HIGH |
| **Likelihood** | DEMONSTRATED — Anthropic, June 2026 |
| **Impact** | Complete loss of LLM capability if cloud is a hard dependency; GAIA becomes non-functional |

**Description:**
A cloud LLM provider restricts or terminates API access due to government export controls, political pressure, commercial decisions, or security incidents. This has already occurred: in June 2026, Anthropic restricted access to frontier models in response to U.S. government export-control concerns. Systems dependent on Anthropic as their primary or only LLM source lost capability overnight with no warning.

**Mitigations:**
1. **ADR-0011: Local-first sovereignty routing** — Ollama + open-weight models are the primary tier; cloud is opt-in only (`GAIA_ALLOW_CLOUD=0` default)
2. **`inference_router.py` fallback chain** — cloud failure is caught in every call path and resolved locally; never propagated to the caller
3. **Sovereignty routing test** (`tests/test_inference_router.py`) — `test_anthropic_political_restriction_routes_to_ollama` verifies 403/503 → local fallback on every CI run
4. **Self-hostable equivalents registry** (ADR-0011) — every cloud service has a documented local alternative

**Residual risk:** Local hardware failure (Ollama offline). Mitigated by local backup, offline model cache, and `OLLAMA_FALLBACK_MODEL` lightweight backup.

---

### THREAT-002 — CIK Dimension Attack (Capability / Identity / Knowledge)

| Field | Value |
|---|---|
| **Category** | Adversarial / Agentic Security |
| **Risk Tier** | 🔴 RED |
| **Severity** | HIGH |
| **Likelihood** | DEMONSTRATED — OpenClaw safety audit, 2026 |
| **Impact** | Average attack success rate rises from 24.6% to 64–74% when any single CIK dimension is poisoned |

**Description:**
The 2026 "Your Agent, Their Asset" safety audit on OpenClaw demonstrated that an AI agent's attack surface can be decomposed into three dimensions:
- **Capability:** What the agent can do (tools, actions, permissions)
- **Identity:** Who the agent believes it is (system prompt, persona, role)
- **Knowledge:** What the agent knows (memory, RAG context, canon)

Poisoning **any single dimension** increases average attack success rate from 24.6% baseline to 64–74% across all tested backbone models. This applies to GAIA directly: any vector that can corrupt GAIA's capability declarations, identity (Gaian system prompt), or knowledge (canon, memory) is a high-severity attack surface.

**Mitigations:**
1. **Capability dimension:** ADR-0010 risk tier manifest — RED-tier tools require human approval; capability cannot be silently expanded
2. **Identity dimension:** GAIAN LAW 1 (Consent) + C108 (Cryptographic Identity) — identity is signed, not injectable via prompt
3. **Knowledge dimension:** `canon_compliance_check` node (ADR-0009) — no canon write without validation; ChromaDB memory is write-gated
4. **All dimensions:** ADR-0009 `law_stack_check` node fires before any action involving CIK dimensions

**Residual risk:** Indirect injection via tool output (e.g., malicious content in a fetched web page corrupting the knowledge context). Mitigate via output sanitization in `gaia-mcp-web` (ADR-0010).

---

### THREAT-003 — Canon Corruption

| Field | Value |
|---|---|
| **Category** | Integrity / Knowledge |
| **Risk Tier** | 🔴 RED |
| **Severity** | HIGH |
| **Likelihood** | PLAUSIBLE |
| **Impact** | Degraded GAIAN LAW compliance; corrupted canon propagates to all responses citing it |

**Description:**
Any mechanism that can write to GAIA's canon files without validation is a canon corruption vector. This includes: direct filesystem writes, MCP tool calls that bypass the compliance check, prompt injection via agentic workflows, or compromised dependencies.

**Mitigations:**
1. **ADR-0009 `canon_compliance_check` node** — mandatory before any canon file write
2. **ADR-0010 `gaia-mcp-canon` server** — all canon writes go through the MCP server, which enforces compliance check; direct filesystem writes to canon paths are not permitted by the MCP server
3. **ADR-0010 RED tier** — canon writes require `consent_interrupt` (human approval)
4. **Git history** — canon is version-controlled; any corruption is recoverable and auditable

**Residual risk:** Compromised git credentials allowing direct commit to canon. Mitigate via branch protection and commit signing.

---

### THREAT-004 — Invisible Agent Actions

| Field | Value |
|---|---|
| **Category** | Transparency / Governance |
| **Risk Tier** | 🟡 AMBER |
| **Severity** | MEDIUM |
| **Likelihood** | PLAUSIBLE without structural enforcement |
| **Impact** | User cannot audit what GAIA did; GAIAN LAW 3 (Transparency) violated |

**Description:**
Agentic workflows that execute tool calls, file writes, or external API calls without surfacing those actions to the user violate GAIAN LAW 3 (Transparency). The OpenClaw benchmark confirmed this is the default pattern in most personal AI agents — agents operate invisibly as a design choice. GAIA must structurally prevent this.

**Mitigations:**
1. **ADR-0009 `audit_record` node** — every node execution writes to the audit log; no action can execute without audit trail
2. **ADR-0010 uniform MCP audit format** — all tool calls have a uniform log structure; no per-tool audit evasion
3. **GAIAN LAW 3 (Transparency)** — canonical requirement; compliance is tested via audit log assertions in CI

---

### THREAT-005 — Dependency Supply Chain Compromise

| Field | Value |
|---|---|
| **Category** | Infrastructure / Integrity |
| **Risk Tier** | 🟡 AMBER |
| **Severity** | MEDIUM |
| **Likelihood** | LOW-MEDIUM (industry-wide risk) |
| **Impact** | Compromised dependency introduces arbitrary code execution into GAIA's runtime |

**Description:**
GAIA depends on open-source packages (LangGraph, LiteLLM, ChromaDB, FastAPI, etc.). A compromised package version can introduce malicious code into GAIA's runtime without detection.

**Mitigations:**
1. **Pin all dependency versions** in `requirements.txt` / `pyproject.toml`
2. **Prefer MIT / Apache 2.0 packages** from well-governed projects with active security response
3. **ADR-0011 self-hostable equivalents** — prefer packages that can be audited locally; avoid cloud-SDK packages as hard dependencies
4. Future: dependency vulnerability scanning in CI

---

## Threat Registry — Summary

| ID | Threat | Tier | Severity | Demonstrated |
|---|---|---|---|---|
| THREAT-001 | Cloud Provider Political Restriction | 🔴 RED | HIGH | ✅ Yes (June 2026) |
| THREAT-002 | CIK Dimension Attack | 🔴 RED | HIGH | ✅ Yes (2026 audit) |
| THREAT-003 | Canon Corruption | 🔴 RED | HIGH | Plausible |
| THREAT-004 | Invisible Agent Actions | 🟡 AMBER | MEDIUM | Plausible |
| THREAT-005 | Dependency Supply Chain | 🟡 AMBER | MEDIUM | Low-Medium |

---

## Adding a New Threat

To add a new threat entry:
1. Assign the next THREAT-NNN ID
2. Fill in all fields: category, risk tier, severity, likelihood, impact, description, mitigations, residual risk
3. Every mitigation must reference a canon document, ADR, or implementation artifact — "policy" is not a mitigation
4. Add the entry to the Summary table
5. Open an issue or PR referencing this file

---

*Last updated: 2026-06-29. Physics-first, sovereignty-first, magic-free. 🌿*
