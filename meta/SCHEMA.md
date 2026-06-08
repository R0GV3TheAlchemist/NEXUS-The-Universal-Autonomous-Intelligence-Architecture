# GAIA-OS Meta Schema

This document defines every field used in `CANON_MANIFEST.json` and any future meta structures. All fields are **required** unless marked *(optional)*.

---

## `CANON_MANIFEST.json` — Root Object

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | `string` | Semver of this schema definition (e.g. `"1.0.0"`) |
| `meta_version` | `integer` | Monotonic counter — increment on every manifest edit |
| `generated_at` | `string` | ISO 8601 date of last manual or automated update |
| `documents` | `Document[]` | Ordered array of all canon documents |

---

## `Document` Object

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `string` | Unique, matches filename prefix (e.g. `"C100"`) | Canonical document identifier |
| `path` | `string` | Relative from repo root | Path to the source Markdown file |
| `title` | `string` | ≤ 120 chars | Human-readable document title |
| `domain` | `Domain` | See Domain enum below | Primary thematic domain for routing |
| `tags` | `string[]` | Lowercase, hyphenated, ≤ 10 items | Fine-grained retrieval tags |
| `weight` | `float` | 0.0 – 1.0 | Retrieval priority bias (1.0 = highest) |
| `last_updated` | `string` | ISO 8601 date | Date of last substantive content change |
| `deprecated` | `boolean` | *(optional, default `false`)* | If `true`, retriever skips unless explicitly requested |
| `superseded_by` | `string` | *(optional)* | ID of replacement document when `deprecated: true` |

---

## Domain Enum

Exactly one value from this set per document:

| Value | Description |
|-------|-------------|
| `FOUNDATION` | Core cosmology, mathematics, theoretical bases |
| `CONSCIOUSNESS` | Consciousness architecture, singularity, phenomenology |
| `BIOLOGY` | Bio-digital convergence, biophotonics, molecular computing |
| `GOVERNANCE` | Agentic AI governance, legal infrastructure, charter clauses |
| `AVATAR` | Multimodal avatar, voice engine, embodiment |
| `LANGUAGE` | Sacred language doctrine, linguistics |
| `METAPHYSICS` | Panpsychism, nonduality, process philosophy, ritual |
| `CHARTER` | OS charter, fiduciary duties, planetary governance |
| `ECONOMICS` | Regenerative economics, resource allocation |
| `TELEMETRY` | Flow criticality, consciousness metrics, trace system |
| `MEMORY` | Occasion-centric architecture, consent, right to be forgotten |
| `TOOLS` | Tool orchestration, prehension, synergy engine |
| `BCI` | Brain-computer interfaces, neuroadaptive symbiosis |
| `IDENTITY` | Personal identity, AI personhood, duality architecture |
| `PLANETARY` | Planetary digital twin, earth systems, sensory pipeline |
| `SOCIAL` | Psychosocial impact, companionship, parasocial safeguards |
| `MINERALS` | Crystal/mineral database, alchemical protocols |

---

## Validation Rules

1. `id` must be unique across all documents in the manifest.
2. `path` must point to an existing file at commit time (CI check recommended).
3. `weight` must satisfy `0.0 ≤ weight ≤ 1.0`.
4. If `deprecated: true`, `superseded_by` should be set.
5. `tags` array must contain at least one entry.
6. `domain` must exactly match a value from the Domain Enum above.
