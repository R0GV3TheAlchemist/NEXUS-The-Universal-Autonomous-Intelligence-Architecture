#!/usr/bin/env python3
"""
GAIA-OS Canon Linter
Verifies that canon/ directory has no unregistered active files,
no duplicate C-number active files, and that REGISTRY.json is valid.

Exit codes:
  0 = PASS
  1 = FAIL (prints violations)

Usage:
  python scripts/canon_lint.py
"""

import json
import os
import re
import sys

REGISTRY_PATH = "canon/REGISTRY.json"
CANON_DIR = "canon"

# Suffixes that mark a file as non-authoritative (safe to exist alongside canonical)
NON_AUTH_SUFFIXES = [
    "_ARCHIVED.md",
    "_DEPRECATED.md",
    "_DEPRECATED_FSO002.md",
    "_CANONICAL.md",  # old naming pattern, now superseded by registry
]

SKIP_FILES = [
    "REGISTRY.json",
    ".block12_deletion_marker",
]


def load_registry():
    with open(REGISTRY_PATH, "r") as f:
        return json.load(f)


def get_all_canonical_files(registry):
    """Return set of all files declared canonical in registry."""
    canonicals = set()
    for section in ["canon", "named_canons"]:
        for key, entry in registry.get(section, {}).items():
            cf = entry.get("canonical_file", "")
            if cf and cf != "PENDING":
                canonicals.add(cf)
    return canonicals


def get_all_registered_files(registry):
    """Return set of ALL files mentioned in registry (canonical + superseded)."""
    all_files = set()
    for section in ["canon", "named_canons"]:
        for key, entry in registry.get(section, {}).items():
            cf = entry.get("canonical_file", "")
            if cf and cf != "PENDING":
                all_files.add(cf)
            for sup in entry.get("supersedes", []):
                all_files.add(sup)
    return all_files


def is_non_authoritative(filename):
    for suffix in NON_AUTH_SUFFIXES:
        if filename.endswith(suffix):
            return True
    return False


def extract_c_number(filename):
    """Extract C-number prefix from filename like C154_..."""
    match = re.match(r"(C\d+[a-z]?)_", filename)
    if match:
        return match.group(1).upper()
    return None


def lint():
    violations = []

    if not os.path.exists(REGISTRY_PATH):
        print(f"FATAL: Registry not found at {REGISTRY_PATH}")
        sys.exit(1)

    registry = load_registry()
    canonical_files = get_all_canonical_files(registry)
    all_registered = get_all_registered_files(registry)

    # Collect actual files in canon/
    canon_files = [
        f for f in os.listdir(CANON_DIR)
        if os.path.isfile(os.path.join(CANON_DIR, f))
        and f not in SKIP_FILES
    ]

    # Track active (non-deprecated) files per C-number
    active_by_cnumber = {}

    for fname in canon_files:
        fpath = os.path.join(CANON_DIR, fname)  # e.g. canon/C157_...
        relative_path = f"canon/{fname}"

        # Skip known non-authoritative files
        if is_non_authoritative(fname):
            continue

        # Check if this active file is registered
        if relative_path not in canonical_files:
            violations.append(
                f"UNREGISTERED ACTIVE FILE: {relative_path}\n"
                f"  → Add to REGISTRY.json or add a _DEPRECATED/_ARCHIVED suffix."
            )

        # Track duplicates by C-number
        c_num = extract_c_number(fname)
        if c_num:
            active_by_cnumber.setdefault(c_num, []).append(fname)

    # Check for duplicate active files under same C-number
    for c_num, files in active_by_cnumber.items():
        active_non_deprecated = [
            f for f in files if not is_non_authoritative(f)
        ]
        if len(active_non_deprecated) > 1:
            violations.append(
                f"DUPLICATE ACTIVE FILES for {c_num}:\n"
                + "\n".join(f"  - {f}" for f in active_non_deprecated)
                + f"\n  → Only one file per C-number may be active. Mark others _ARCHIVED."
            )

    if violations:
        print(f"\n❌ CANON LINT FAILED — {len(violations)} violation(s):\n")
        for v in violations:
            print(v)
            print()
        sys.exit(1)
    else:
        print(f"✅ CANON LINT PASSED — {len(canon_files)} files checked, registry consistent.")
        sys.exit(0)


if __name__ == "__main__":
    lint()
