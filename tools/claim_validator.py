"""
GAIA Tool — Claim Validator
Validate a claim JSON against the GAIA minimum schema.

Usage:
    python tools/claim_validator.py '{"statement": "X", "knowledge_type": "observed", "confidence": 0.8}'
    echo '{...}' | python tools/claim_validator.py
"""

import sys
import json

REQUIRED_FIELDS = {
    "knowledge_type": ["observed", "inferred", "hypothesis", "simulation"],
    "confidence":     None,  # float 0-1
}

OPTIONAL_FIELDS = [
    "statement", "subject", "predicate", "object",
    "entity_type", "relation_type", "input_source",
    "id", "stored_at", "gaia_version"
]


def validate(claim: dict) -> tuple[bool, list[str]]:
    errors = []

    # Required: knowledge_type
    kt = claim.get("knowledge_type")
    if kt is None:
        errors.append("MISSING: knowledge_type (required by ADR-001)")
    elif kt not in REQUIRED_FIELDS["knowledge_type"]:
        valid = REQUIRED_FIELDS["knowledge_type"]
        errors.append(f"INVALID: knowledge_type={kt!r} — must be one of {valid}")

    # Required: confidence
    conf = claim.get("confidence")
    if conf is None:
        errors.append("MISSING: confidence (required)")
    elif not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        errors.append(f"INVALID: confidence={conf!r} — must be float in [0.0, 1.0]")

    return len(errors) == 0, errors


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        raw = sys.stdin.read().strip()

    try:
        claim = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

    valid, errors = validate(claim)
    if valid:
        kt   = claim.get('knowledge_type')
        conf = claim.get('confidence')
        print(f"✅ Valid GAIA claim  [type={kt}, confidence={conf}]")
    else:
        print(f"❌ Invalid GAIA claim — {len(errors)} error(s):")
        for e in errors:
            print(f"   • {e}")
        sys.exit(1)
