# GAIA Tools

Developer and research tools for working with GAIA internals.

## Available Tools

| Tool | Purpose |
|---|---|
| `claim_validator.py` | Validate a claim JSON against the GAIA schema |
| `adr_check.py` | Verify all ADRs have required sections |
| `ontology_diff.py` | Compare two ontology snapshots |

## Usage

```bash
# Validate a claim
python tools/claim_validator.py '{"statement": "X", "knowledge_type": "observed", "confidence": 0.8}'

# Check ADR completeness
python tools/adr_check.py docs/adr/
```
