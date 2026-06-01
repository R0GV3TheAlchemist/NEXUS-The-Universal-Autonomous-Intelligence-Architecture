#!/usr/bin/env python3
"""
scripts/validate_crystal_db.py
GAIA-OS Crystal Database — Programmatic Consistency Checker
Version: 1.1.0 (2026-06-01: add c8a/c8b/c9a/c9b to BATCH_SERIES; now scans all 29 batches)

Scans all batch files in src/crystals/db/ and validates every
CrystalRecord object against the defined rule-set. Exits with code 1
if any ERROR-level violations are found.

Usage:
  python scripts/validate_crystal_db.py              # full scan
  python scripts/validate_crystal_db.py --fix-report # include fix suggestions
  python scripts/validate_crystal_db.py --batch a4   # single batch
"""

import re
import sys
import json
import os
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BATCH_SERIES = {
    "A": ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8"],
    "B": ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9"],
    "C": ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8a", "c8b", "c9a", "c9b"],
}
ALL_BATCHES = [
    f"batch-{series.lower()}{suffix}"
    for series, suffixes in BATCH_SERIES.items()
    for suffix in suffixes
]

DB_DIR = os.path.join("src", "crystals", "db")

# Severity constants
ERROR = "ERROR"
WARN  = "WARN"
INFO  = "INFO"

# ---------------------------------------------------------------------------
# Violation record
# ---------------------------------------------------------------------------

@dataclass
class Violation:
    severity: str
    rule:     str
    batch:    str
    crystal:  str
    detail:   str
    fix:      Optional[str] = None

# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------

# Minerals whose formulas contain these fragments must be water-unsafe (R02)
WATER_UNSAFE_FORMULA_FRAGMENTS = [
    "Cu", "Pb", "As", "Hg", "Sb", "Tl",    # toxic metals
    "S",                                      # sulfides/sulfates (dissolution risk)
    "F",                                      # fluorides
    "Cl",                                     # chlorides
]

# Minerals that are organic / amorphous organic must be water-unsafe (R03)
ORGANIC_KEYWORDS = [
    "resin", "organic", "fossil", "amber", "jet",
    "copal", "kauri", "Baltic",
]

# Valid numerology values (Pythagorean + master numbers)
VALID_NUMEROLOGY = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33}

# Asbestos-form minerals that must carry explicit safety_warning (R12)
ASBESTOS_KEYWORDS = [
    "actinolite", "tremolite", "chrysotile", "crocidolite",
    "amosite", "anthophyllite", "riebeckite", "byssolite",
    "asbestos", "ASBESTOS",
]

# ---------------------------------------------------------------------------
# Parser (TypeScript record extractor)
# ---------------------------------------------------------------------------

def extract_field(blob: str, field_name: str) -> Optional[str]:
    """Extract a simple scalar field value from a TS object blob."""
    pattern = rf"(?:^|\s){re.escape(field_name)}\s*:\s*([^,\n]+)"
    m = re.search(pattern, blob)
    if m:
        return m.group(1).strip().strip("'\"")
    return None


def extract_bool_field(blob: str, field_name: str) -> Optional[bool]:
    val = extract_field(blob, field_name)
    if val is None:
        return None
    return val.lower() == "true"


def extract_string_field(blob: str, field_name: str) -> Optional[str]:
    return extract_field(blob, field_name)


def extract_int_field(blob: str, field_name: str) -> Optional[int]:
    val = extract_field(blob, field_name)
    if val is None:
        return None
    try:
        return int(val.rstrip(","))
    except ValueError:
        return None


def split_records(source: str) -> list[tuple[str, str]]:
    """Return list of (crystal_name, record_blob) tuples."""
    records = []
    # Find each top-level { ... } in the array
    depth = 0
    start = None
    i = 0
    while i < len(source):
        ch = source[i]
        if ch == '{' and depth == 0:
            # Check we're not inside a comment
            start = i
            depth = 1
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                blob = source[start:i+1]
                # Extract name
                name_match = re.search(r"name:\s*['\"]([^'\"]+)['\"]", blob)
                name = name_match.group(1) if name_match else "<unknown>"
                records.append((name, blob))
                start = None
        i += 1
    return records


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

def validate_record(batch_id: str, name: str, blob: str) -> list[Violation]:
    violations = []

    # Pull commonly-used fields once
    physical_match = re.search(r"physical\s*:\s*\{(.+?)\n    \}", blob, re.DOTALL)
    physical_blob  = physical_match.group(1) if physical_match else ""

    meta_match  = re.search(r"metaphysical\s*:\s*\{(.+?)\n    \}", blob, re.DOTALL)
    meta_blob   = meta_match.group(1) if meta_match else ""

    ima_formula     = extract_string_field(physical_blob, "ima_formula")
    mindat_formula  = extract_string_field(physical_blob, "mindat_formula")
    safe_water      = extract_bool_field(physical_blob, "safe_for_water")
    safe_hw         = extract_bool_field(physical_blob, "safe_for_hardware")
    piezo           = extract_bool_field(physical_blob, "piezoelectric")
    shortdesc       = extract_string_field(physical_blob, "shortdesc")
    safety_warning  = extract_string_field(meta_blob, "safety_warning")
    numerology      = extract_int_field(meta_blob, "numerology")
    hardness_min    = extract_field(physical_blob, "hardness_min")
    hardness_max    = extract_field(physical_blob, "hardness_max")

    formula = (ima_formula or mindat_formula or "").upper()

    # R01 — safe_for_hardware must be false when piezoelectric is true
    if piezo is True and safe_hw is True:
        violations.append(Violation(
            ERROR, "R01", batch_id, name,
            "piezoelectric=true but safe_for_hardware=true (should be false)",
            fix="Set safe_for_hardware: false",
        ))

    # R02 — water-unsafe formula fragments
    if safe_water is True:
        for frag in WATER_UNSAFE_FORMULA_FRAGMENTS:
            if frag.upper() in formula:
                violations.append(Violation(
                    ERROR, "R02", batch_id, name,
                    f"safe_for_water=true but formula contains '{frag}' ({formula})",
                    fix="Set safe_for_water: false and add safety_warning in metaphysical block",
                ))
                break

    # R03 — organic material must be water-unsafe
    if safe_water is True and shortdesc:
        for kw in ORGANIC_KEYWORDS:
            if kw.lower() in shortdesc.lower():
                violations.append(Violation(
                    ERROR, "R03", batch_id, name,
                    f"safe_for_water=true but shortdesc contains organic keyword '{kw}'",
                    fix="Set safe_for_water: false",
                ))
                break

    # R04 — hardness must be numeric and 0.5 <= h <= 10
    for hfield, hval in [("hardness_min", hardness_min), ("hardness_max", hardness_max)]:
        if hval is not None:
            try:
                h = float(hval)
                if not (0.5 <= h <= 10.0):
                    violations.append(Violation(
                        ERROR, "R04", batch_id, name,
                        f"{hfield}={h} is outside valid range 0.5–10.0",
                    ))
            except ValueError:
                violations.append(Violation(
                    ERROR, "R04", batch_id, name,
                    f"{hfield} is non-numeric: {hval!r}",
                ))

    # R05 — hardness_min must not exceed hardness_max
    if hardness_min and hardness_max:
        try:
            if float(hardness_min) > float(hardness_max):
                violations.append(Violation(
                    ERROR, "R05", batch_id, name,
                    f"hardness_min ({hardness_min}) > hardness_max ({hardness_max})",
                ))
        except ValueError:
            pass

    # R06 — mindat_id must be present and positive integer (or null for trade names)
    mindat_id_raw = extract_field(blob, "mindat_id")
    trade_name    = extract_bool_field(blob, "trade_name")
    if not trade_name:
        if mindat_id_raw is None or mindat_id_raw.lower() == "null":
            violations.append(Violation(
                WARN, "R06", batch_id, name,
                "mindat_id is null for a non-trade-name mineral — verify on mindat.org",
            ))
        else:
            try:
                mid = int(mindat_id_raw.rstrip(","))
                if mid <= 0:
                    violations.append(Violation(
                        ERROR, "R06", batch_id, name,
                        f"mindat_id must be a positive integer, got {mid}",
                    ))
            except ValueError:
                violations.append(Violation(
                    ERROR, "R06", batch_id, name,
                    f"mindat_id is non-numeric: {mindat_id_raw!r}",
                ))

    # R07 — mindat_url must contain the mindat_id
    mindat_url = extract_string_field(physical_blob, "mindat_url")
    if mindat_url and mindat_id_raw and mindat_id_raw.lower() not in ("null", ""):
        try:
            mid_str = str(int(mindat_id_raw.rstrip(",")))
            if mid_str not in mindat_url:
                violations.append(Violation(
                    WARN, "R07", batch_id, name,
                    f"mindat_url '{mindat_url}' does not contain mindat_id {mid_str}",
                ))
        except ValueError:
            pass

    # R08 — if ima_status is 'A', ima_year must be present
    ima_status = extract_string_field(physical_blob, "ima_status")
    ima_year   = extract_string_field(physical_blob, "ima_year")
    if ima_status == "A" and (ima_year is None or ima_year.lower() == "null"):
        violations.append(Violation(
            WARN, "R08", batch_id, name,
            "ima_status='A' but ima_year is null — populate from IMA list",
        ))

    # R09 — numerology must be a valid Pythagorean value
    if numerology is not None and numerology not in VALID_NUMEROLOGY:
        violations.append(Violation(
            WARN, "R09", batch_id, name,
            f"numerology={numerology} is not a valid value (valid: 1–9, 11, 22, 33)",
            fix=f"Set numerology to the correct Pythagorean value (0 is invalid)",
        ))

    # R10 — angel_number should match numerology digit pattern
    angel_raw = extract_field(meta_blob, "angel_number")
    if angel_raw and numerology:
        angel_clean = angel_raw.strip("'\"")
        # angel_number should be a string of repeating numerology digit(s)
        expected_patterns = [
            str(numerology) * 3,
            str(numerology) * 4,
            "0" * 3,  # 000 is special (void / new beginning)
        ]
        if angel_clean not in expected_patterns:
            violations.append(Violation(
                INFO, "R10", batch_id, name,
                f"angel_number='{angel_clean}' does not match expected pattern for numerology={numerology} (expected e.g. '{str(numerology)*3}')",
            ))

    # R11 — shortdesc must be non-empty for non-trade-name minerals
    if not trade_name and (shortdesc is None or shortdesc.strip() == ""):
        violations.append(Violation(
            WARN, "R11", batch_id, name,
            "shortdesc is empty for a non-trade-name mineral",
        ))

    # R12 — asbestos-form minerals must carry explicit safety_warning
    combined_text = f"{shortdesc or ''} {safety_warning or ''} {name}"
    is_asbestos = any(kw.lower() in combined_text.lower() for kw in ASBESTOS_KEYWORDS)
    if is_asbestos and (safety_warning is None or "asbestos" not in safety_warning.lower()):
        violations.append(Violation(
            ERROR, "R12", batch_id, name,
            "mineral appears to be asbestos-form but safety_warning does not mention 'asbestos'",
            fix="Add explicit ASBESTOS HAZARD safety_warning to metaphysical block",
        ))

    # R13 — safe_for_hardware must be false for piezoelectric minerals
    # (same as R01 but explicit for documentation)
    if piezo is True and safe_hw is not False:
        # Only flag if not already caught by R01
        if not any(v.rule == "R01" for v in violations):
            violations.append(Violation(
                ERROR, "R13", batch_id, name,
                "Piezoelectric mineral must have safe_for_hardware: false",
                fix="Set safe_for_hardware: false",
            ))

    return violations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GAIA Crystal DB Validator")
    parser.add_argument("--fix-report", action="store_true", help="Include fix suggestions")
    parser.add_argument("--batch", type=str, help="Validate a single batch (e.g. a4, b9)")
    parser.add_argument("--json-out", type=str, help="Write JSON report to file")
    args = parser.parse_args()

    if args.batch:
        target_batches = [f"batch-{args.batch.lower()}"]
    else:
        target_batches = ALL_BATCHES

    all_violations: list[Violation] = []
    record_count = 0
    missing_batches = []

    for batch_id in target_batches:
        filepath = os.path.join(DB_DIR, f"{batch_id}.data.ts")
        if not os.path.exists(filepath):
            missing_batches.append(batch_id)
            continue

        with open(filepath, encoding="utf-8") as f:
            source = f.read()

        records = split_records(source)
        record_count += len(records)

        for name, blob in records:
            violations = validate_record(batch_id, name, blob)
            all_violations.extend(violations)

    errors   = [v for v in all_violations if v.severity == ERROR]
    warnings = [v for v in all_violations if v.severity == WARN]
    infos    = [v for v in all_violations if v.severity == INFO]

    # Console output
    if missing_batches:
        print(f"[SKIP] Missing batch files: {', '.join(missing_batches)}")

    for v in all_violations:
        line = f"[{v.severity:<5}] {v.rule} {v.batch} → {v.crystal}: {v.detail}"
        if args.fix_report and v.fix:
            line += f"\n         FIX: {v.fix}"
        print(line)

    print()
    print(f"Records scanned : {record_count}")
    print(f"Batches scanned : {len(target_batches) - len(missing_batches)}/{len(target_batches)}")
    print(f"Errors          : {len(errors)}")
    print(f"Warnings        : {len(warnings)}")
    print(f"Info            : {len(infos)}")

    # JSON report
    if args.json_out:
        report = {
            "version": "1.1.0",
            "records_scanned": record_count,
            "batches_scanned": len(target_batches) - len(missing_batches),
            "missing_batches": missing_batches,
            "summary": {
                "errors":   len(errors),
                "warnings": len(warnings),
                "infos":    len(infos),
            },
            "violations": [
                {
                    "severity": v.severity,
                    "rule":     v.rule,
                    "batch":    v.batch,
                    "crystal":  v.crystal,
                    "detail":   v.detail,
                    "fix":      v.fix,
                }
                for v in all_violations
            ],
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"JSON report written to {args.json_out}")

    has_errors = len(errors) > 0
    if has_errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
