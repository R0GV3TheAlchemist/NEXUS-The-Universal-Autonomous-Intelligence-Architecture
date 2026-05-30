#!/usr/bin/env python3
"""
scripts/validate_crystal_db.py
GAIA-OS Crystal Database — Programmatic Consistency Checker
Version: 1.0.1 (bump: re-run trigger post batch-a1 R13 fix 2026-05-30)

Scans all 25 batch files (A1–C7) in src/crystals/db/ and validates every
CrystalRecord against the rule-set derived from crystal.schema.ts v1.3 and
the Crystal Theory document.

Usage:
    python scripts/validate_crystal_db.py
    python scripts/validate_crystal_db.py --batch a1          # single batch
    python scripts/validate_crystal_db.py --json              # JSON output
    python scripts/validate_crystal_db.py --fix-report        # show fix hints

Exit codes:
    0  — all records pass
    1  — one or more violations found
    2  — file not found / parse error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / "src" / "crystals" / "db"

BATCH_SERIES = {
    "A": ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8"],
    "B": ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9"],
    "C": ["c1", "c2", "c3", "c4", "c5", "c6", "c7"],
}
ALL_BATCHES = [
    f"batch-{b}" for batches in BATCH_SERIES.values() for b in batches
]

# ─────────────────────────────────────────────────────────────────────────────
# Rule severity levels
# ─────────────────────────────────────────────────────────────────────────────

ERROR = "ERROR"    # Data is definitely wrong — must fix
WARN  = "WARN"     # Likely wrong — review required
INFO  = "INFO"     # Informational — flagged for human review


# ─────────────────────────────────────────────────────────────────────────────
# Violation dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Violation:
    batch:    str
    crystal:  str
    rule:     str
    severity: str
    detail:   str
    fix_hint: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Lightweight TypeScript record extractor
# Parses the batch TS files via regex — no TS runtime required.
# Extracts key scalar fields sufficient for all 14 rules.
# ─────────────────────────────────────────────────────────────────────────────

def _extract_string(src: str, key: str) -> str | None:
    """Extract a simple string value: key: 'value' or key: \"value\"."""
    m = re.search(rf"\b{key}:\s*['\"]([^'\"]*)['\"\.]", src)
    return m.group(1) if m else None


def _extract_bool(src: str, key: str) -> bool | None:
    """Extract a boolean: key: true / key: false."""
    m = re.search(rf"\b{key}:\s*(true|false)", src)
    if m:
        return m.group(1) == "true"
    return None


def _extract_number(src: str, key: str) -> float | None:
    """Extract a number: key: 123 or key: 1.23."""
    m = re.search(rf"\b{key}:\s*(-?[\d]+\.?[\d]*)", src)
    return float(m.group(1)) if m else None


def _extract_array_strings(src: str, key: str) -> list[str]:
    """Extract a string-array: key: ['a', 'b'] or key: [\"a\", \"b\"]."""
    m = re.search(rf"\b{key}:\s*\[([^\]]*)", src)
    if not m:
        return []
    inner = m.group(1)
    return re.findall(r"['\"]([^'\"]+)['\"]", inner)


def _has_key(src: str, key: str) -> bool:
    """Return True if the key appears as an object property."""
    return bool(re.search(rf"\b{key}:\s*", src))


# ─────────────────────────────────────────────────────────────────────────────
# Record splitter — splits a batch file into per-record TS source blobs
# ─────────────────────────────────────────────────────────────────────────────

def split_records(source: str) -> list[tuple[str, str]]:
    """
    Returns a list of (crystal_name, record_source_blob) tuples.
    Heuristic: records start at a top-level '{' following a block comment
    that begins with // ─── or //  N.
    """
    record_blobs: list[tuple[str, str]] = []

    array_m = re.search(r"const BATCH_[A-Z0-9_]+:\s*CrystalRecord\[\]\s*=\s*\[", source)
    if not array_m:
        return []

    array_start = array_m.end()
    depth = 0
    record_start: int | None = None
    records_raw: list[str] = []

    for i in range(array_start, len(source)):
        ch = source[i]
        if ch == "{":
            if depth == 0:
                record_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and record_start is not None:
                records_raw.append(source[record_start : i + 1])
                record_start = None
        elif ch == "]" and depth == 0:
            break

    for blob in records_raw:
        name = _extract_string(blob, "name") or "<unknown>"
        record_blobs.append((name, blob))

    return record_blobs


# ─────────────────────────────────────────────────────────────────────────────
# Toxic / water-unsafe element detection helpers
# ─────────────────────────────────────────────────────────────────────────────

TOXIC_FORMULAS = [
    r"CuS", r"Cu2S", r"CuFeS", r"FeAsS", r"As2S", r"As4S", r"Pb",
    r"HgS", r"Sb2S", r"CdS", r"AsO", r"Cu2O", r"CuO", r"PbSO",
    r"BaSO4",
    r"Na3AlF6", r"CaF2",
]

TOXIC_NAME_PATTERNS = [
    r"chalcopyrite", r"bornite", r"covellite", r"galena", r"cinnabar",
    r"arsenopyrite", r"realgar", r"orpiment", r"stibnite", r"cuprite",
    r"malachite",
    r"azurite",
    r"chrysocolla",
    r"cryolite", r"fluorite",
    r"adamite", r"olivenite", r"legrandite",
    r"scorodite", r"erythrite", r"annabergite",
    r"tyrolite", r"conichalcite",
    r"sulfur", r"sulphur",
]

ORGANIC_NAME_PATTERNS = [
    r"amber", r"jet", r"coral", r"pearl", r"abalone", r"shell",
    r"ivory", r"bone",
]


def _is_likely_toxic(name: str, formula_blob: str) -> bool:
    name_lower = name.lower()
    for pat in TOXIC_NAME_PATTERNS:
        if re.search(pat, name_lower):
            return True
    for frag in TOXIC_FORMULAS:
        if re.search(frag, formula_blob):
            return True
    return False


def _is_organic(name: str) -> bool:
    name_lower = name.lower()
    return any(re.search(p, name_lower) for p in ORGANIC_NAME_PATTERNS)


def _is_trade_name_expected(name: str, ima_status_blob: str) -> bool:
    not_ima_patterns = [
        r"not ima", r"biogenic", r"variety", r"trade name", r"tradename",
    ]
    combined = (name + " " + ima_status_blob).lower()
    return any(re.search(p, combined) for p in not_ima_patterns)


# ─────────────────────────────────────────────────────────────────────────────
# 14-rule validator
# ─────────────────────────────────────────────────────────────────────────────

def validate_record(batch: str, name: str, blob: str) -> list[Violation]:
    violations: list[Violation] = []

    def v(rule: str, severity: str, detail: str, fix: str = "") -> None:
        violations.append(Violation(batch, name, rule, severity, detail, fix))

    # ── R01 trade_name consistency ────────────────────────────────────────────
    trade_name = _extract_bool(blob, "trade_name")
    ima_status_val = _extract_string(blob, "ima_status") or ""
    if trade_name is False and _is_trade_name_expected(name, ima_status_val):
        v("R01", WARN,
          f"trade_name: false but IMA status suggests non-mineral/trade name",
          "Set trade_name: true if this is a biogenic, organic, or variety name")
    if trade_name is None:
        v("R01", ERROR,
          "trade_name field is missing",
          "Add trade_name: true or trade_name: false to the root record")

    # ── R02 safe_for_water — toxic minerals ──────────────────────────────────
    safe_water = _extract_bool(blob, "safe_for_water")
    formula_blob = blob
    if _is_likely_toxic(name, formula_blob) and safe_water is True:
        v("R02", ERROR,
          f"safe_for_water: true on likely-toxic mineral",
          "Set safe_for_water: false — mineral formula/name matches toxic pattern")
    if safe_water is None:
        v("R02", ERROR,
          "safe_for_water field is missing",
          "Add safe_for_water: true or false under physical.{}")

    # ── R03 safe_for_water — organics ────────────────────────────────────────
    if _is_organic(name) and safe_water is True:
        v("R03", ERROR,
          f"safe_for_water: true on organic material — organics degrade in water",
          "Set safe_for_water: false for all organic gemstones")

    # ── R04 mindat_id null ↔ IMA status null/Not IMA ─────────────────────────
    mindat_id_null = bool(re.search(r"mindat_id:\s*null", blob))
    mindat_id_val  = _extract_number(blob, "mindat_id") if not mindat_id_null else None
    ima_null       = bool(re.search(r"ima_status:\s*null", blob))
    ima_not_ima    = bool(re.search(r"ima_status:\s*['\"]Not IMA", blob, re.IGNORECASE))
    if mindat_id_val and ima_null and not ima_not_ima:
        v("R04", WARN,
          f"mindat_id is set ({int(mindat_id_val)}) but ima_status is null",
          "If mineral has a Mindat ID it should have an IMA status (A / Rd / Q / etc.)")
    if not mindat_id_null and mindat_id_val is None and not ima_null:
        v("R04", WARN,
          "ima_status is set but mindat_id is null — verify Mindat entry exists",
          "Locate the Mindat ID for this mineral and populate mindat_id")

    # ── R05 OKLCH L range ────────────────────────────────────────────────────
    oklch_l = _extract_number(blob, r"\bl\b")
    if oklch_l is not None and not (0.0 <= oklch_l <= 1.0):
        v("R05", ERROR,
          f"OKLCH L={oklch_l} is out of range [0.0, 1.0]",
          "Recalculate OKLCH L; must be in [0, 1]")

    # ── R06 OKLCH C range ────────────────────────────────────────────────────
    oklch_c = _extract_number(blob, r"\bc\b")
    if oklch_c is not None and not (0.0 <= oklch_c <= 0.40):
        v("R06", ERROR,
          f"OKLCH C={oklch_c} is out of range [0.0, 0.40]",
          "Recalculate OKLCH C; maximum chroma for real colours is ~0.37")

    # ── R07 OKLCH H range ────────────────────────────────────────────────────
    oklch_h = _extract_number(blob, r"\bh\b")
    if oklch_h is not None and not (0 <= oklch_h <= 360):
        v("R07", ERROR,
          f"OKLCH H={oklch_h} is out of range [0, 360]",
          "Recalculate OKLCH H; must be in [0, 360]")

    # ── R08 hex format ────────────────────────────────────────────────────────
    hex_val = _extract_string(blob, "hex")
    if hex_val is not None:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", hex_val):
            v("R08", ERROR,
              f"hex='{hex_val}' is not a valid 6-digit hex colour",
              "Fix hex to format #RRGGBB")
    else:
        if re.search(r"\bcolor:\s*{", blob) or re.search(r"colour:\s*{", blob):
            v("R08", WARN,
              "hex field appears to be missing from color block",
              "Add hex: '#RRGGBB' to the color object")

    # ── R09 numerology range ────────────────────────────────────────────────
    num = _extract_number(blob, "numerology")
    if num is not None:
        valid_nums = set(range(1, 10)) | {11, 22, 33}
        if num not in valid_nums:
            v("R09", WARN,
              f"numerology={int(num)} is outside canonical range (1–9, 11, 22, 33)",
              "Recalculate numerology from crystal name gematria")

    # ── R10 angel_number range ────────────────────────────────────────────
    angel = _extract_number(blob, "angel_number")
    if angel is not None:
        if not (1 <= angel <= 9999):
            v("R10", WARN,
              f"angel_number={int(angel)} is outside expected range [1, 9999]",
              "Verify angel_number assignment")

    # ── R11 chakra_primary required ──────────────────────────────────────────
    chakra_primary = _extract_string(blob, "chakra_primary")
    if not chakra_primary:
        v("R11", ERROR,
          "chakra_primary is missing or empty",
          "Add chakra_primary: '<ChakraName>' to the metaphysical block")

    # ── R12 element required ────────────────────────────────────────────────
    elements = _extract_array_strings(blob, "element")
    if not elements:
        if re.search(r"\belement:\s*\[\s*\]", blob):
            v("R12", ERROR,
              "element array is empty",
              "Populate element: ['Element1', ...] in the metaphysical block")
        elif not re.search(r"\belement:\s*", blob):
            v("R12", ERROR,
              "element field is missing from metaphysical block",
              "Add element: ['Element1', ...] to the metaphysical block")

    # ── R13 safety_warning required ──────────────────────────────────────────
    has_safety = re.search(r"safety_warning:", blob)
    if not has_safety:
        v("R13", ERROR,
          "safety_warning field is missing from metaphysical block",
          "Add safety_warning: '...' to describe handling / water / toxicity")
    else:
        sw_val = _extract_string(blob, "safety_warning")
        if sw_val is not None and len(sw_val.strip()) < 10:
            v("R13", WARN,
              f"safety_warning is too short ('{sw_val}')",
              "Expand safety_warning with toxicity, water safety, and hardness info")

    # ── R14 gaia_resonance required ──────────────────────────────────────────
    has_gr = re.search(r"gaia_resonance:", blob)
    if not has_gr:
        v("R14", ERROR,
          "gaia_resonance field is missing from metaphysical block",
          "Add gaia_resonance: '<Module1> + <Module2>' to the metaphysical block")
    else:
        gr_val = _extract_string(blob, "gaia_resonance")
        if gr_val is not None and len(gr_val.strip()) < 3:
            v("R14", WARN,
              f"gaia_resonance is empty or too short ('{gr_val}')",
              "Assign valid GAIA resonance modules (e.g. 'ClarusLens + QuantumNexus')")

    return violations


# ─────────────────────────────────────────────────────────────────────────────
# Batch file parser
# ─────────────────────────────────────────────────────────────────────────────

def validate_batch(batch_id: str) -> tuple[list[Violation], int]:
    """
    Validate a single batch (e.g. 'batch-a1').
    Returns (violations, record_count).
    """
    path = DB_DIR / f"{batch_id}.data.ts"
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(2)

    source = path.read_text(encoding="utf-8")
    records = split_records(source)
    violations: list[Violation] = []

    for name, blob in records:
        violations.extend(validate_record(batch_id, name, blob))

    return violations, len(records)


# ─────────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────────

SEV_COLOUR = {
    ERROR: "\033[91m",
    WARN:  "\033[93m",
    INFO:  "\033[94m",
}
RESET = "\033[0m"


def _sev(s: str, text: str) -> str:
    return f"{SEV_COLOUR.get(s, '')}{text}{RESET}"


def print_text_report(
    all_violations: list[Violation],
    batch_stats: dict[str, int],
    show_fix: bool,
) -> None:
    total_records = sum(batch_stats.values())
    total_violations = len(all_violations)

    print()
    print("═" * 72)
    print("  GAIA-OS Crystal DB Validator — Batch Audit A1–C7")
    print("═" * 72)
    print(f"  Batches scanned : {len(batch_stats)}")
    print(f"  Records scanned : {total_records}")
    print(f"  Total violations: {total_violations}")
    print()

    if not all_violations:
        print("  ✅  All records pass — zero violations found.")
        print()
        return

    by_batch: dict[str, list[Violation]] = {}
    for v in all_violations:
        by_batch.setdefault(v.batch, []).append(v)

    for batch_id in sorted(by_batch):
        batch_viols = by_batch[batch_id]
        n_rec = batch_stats.get(batch_id, "?")
        print(f"  ── {batch_id.upper()}  ({n_rec} records, "
              f"{len(batch_viols)} violation{'s' if len(batch_viols) != 1 else ''})")
        print()
        for viol in batch_viols:
            sev_label = _sev(viol.severity, f"[{viol.severity}]")
            print(f"    {sev_label}  {viol.rule}  {viol.crystal}")
            print(f"           {viol.detail}")
            if show_fix and viol.fix_hint:
                print(f"           ↳ FIX: {viol.fix_hint}")
        print()

    print("  Summary table")
    print("  " + "─" * 52)
    print(f"  {'Batch':<12} {'Records':>8} {'Errors':>8} {'Warns':>8} {'Status':>8}")
    print("  " + "─" * 52)
    for batch_id in sorted(batch_stats):
        n_rec = batch_stats[batch_id]
        errs  = sum(1 for v in all_violations if v.batch == batch_id and v.severity == ERROR)
        warns = sum(1 for v in all_violations if v.batch == batch_id and v.severity == WARN)
        status = _sev(ERROR, "FAIL") if errs else (_sev(WARN, "WARN") if warns else "PASS")
        print(f"  {batch_id:<12} {n_rec:>8} {errs:>8} {warns:>8}   {status}")
    print("  " + "─" * 52)
    print()


def print_json_report(
    all_violations: list[Violation],
    batch_stats: dict[str, int],
) -> None:
    payload = {
        "summary": {
            "batches_scanned": len(batch_stats),
            "records_scanned": sum(batch_stats.values()),
            "total_violations": len(all_violations),
        },
        "batch_stats": {
            k: {
                "records": v,
                "errors": sum(1 for x in all_violations if x.batch == k and x.severity == ERROR),
                "warnings": sum(1 for x in all_violations if x.batch == k and x.severity == WARN),
            }
            for k, v in sorted(batch_stats.items())
        },
        "violations": [
            {
                "batch":    v.batch,
                "crystal":  v.crystal,
                "rule":     v.rule,
                "severity": v.severity,
                "detail":   v.detail,
                "fix_hint": v.fix_hint,
            }
            for v in all_violations
        ],
    }
    print(json.dumps(payload, indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="GAIA-OS Crystal DB consistency checker."
    )
    parser.add_argument(
        "--batch", "-b",
        help="Validate a single batch (e.g. a1, b3, c7). Omit to scan all 25.",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Emit JSON output instead of human-readable text.",
    )
    parser.add_argument(
        "--fix-report", "-f",
        action="store_true",
        help="Include fix hints in text output.",
    )
    args = parser.parse_args()

    if args.batch:
        target = args.batch.lower().strip()
        if not target.startswith("batch-"):
            target = f"batch-{target}"
        batches_to_run = [target]
    else:
        batches_to_run = list(ALL_BATCHES)

    all_violations: list[Violation] = []
    batch_stats: dict[str, int] = {}

    for batch_id in batches_to_run:
        violations, record_count = validate_batch(batch_id)
        all_violations.extend(violations)
        batch_stats[batch_id] = record_count

    if args.json:
        print_json_report(all_violations, batch_stats)
    else:
        print_text_report(all_violations, batch_stats, show_fix=args.fix_report)

    has_errors = any(v.severity == ERROR for v in all_violations)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
