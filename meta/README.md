# GAIA-OS · `meta/`

The `meta/` folder is the **self-describing layer** of the GAIA-OS canon. It does not contain doctrine — it describes, indexes, and validates all other content so that the runtime (synergy engine, canon retriever, trace system) can navigate the corpus without scanning raw files.

---

## Files

| File | Purpose |
|------|---------|
| `CANON_MANIFEST.json` | Machine-readable index of every canon document: ID, path, domain, tags, weight, last-updated |
| `SCHEMA.md` | Canonical field definitions and validation rules for all meta structures |
| `README.md` | This file |

---

## Design Principles

1. **Single source of truth.** If a new canon document is added, its entry in `CANON_MANIFEST.json` is the authoritative record. Nothing else needs updating for the runtime to discover it.
2. **Domain routing, not keyword search.** Each document carries a `domain` tag that maps to a synergy-engine register (FOUNDATION, GOVERNANCE, CONSCIOUSNESS, BIOLOGY, AVATAR, LANGUAGE, METAPHYSICS, CHARTER, ECONOMICS, TELEMETRY, RITUAL, MEMORY, TOOLS). The planner uses these to prioritize relevant context windows.
3. **Weight is additive signal, not override.** A document's `weight` (0.0–1.0) biases retrieval probability but never blocks access. The engine may still consult any document regardless of weight.
4. **No circular dependency.** `meta/` files reference canon paths; canon files must not reference `meta/` paths.

---

## Updating the Manifest

When you add a canon document:

```jsonc
// Append to CANON_MANIFEST.json → "documents" array:
{
  "id": "C143",
  "path": "canon/C143_Your_New_Document.md",
  "title": "Your New Document Title",
  "domain": "MEMORY",
  "tags": ["memory", "retrieval", "architecture"],
  "weight": 0.8,
  "last_updated": "2026-06-08"
}
```

Then bump `meta_version` in the manifest root.
