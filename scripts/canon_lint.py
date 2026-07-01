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
    """Return set of files declared as the single canonical authority."""
    canonicals = set()
    for section in ["canon", "named_canons"]:
        for key, entry in registry.get(section, {}).items():
            cf = entry.get("canonical_file", "")
            if cf and cf != "PENDING":
                canonicals.add(cf)
    return canonicals


def get_all_registered_files(registry):
    """
    Return set of ALL files known to the registry:
      - canonical_file entries
      - supersedes[] entries (retired variants)
      - archived_files[] top-level list (explicit archive declarations)
    Any file in this set is considered registered and will not trigger
    an UNREGISTERED ACTIVE FILE violation.
    """
    all_files = set()
    for section in ["canon", "named_canons"]:
        for key, entry in registry.get(section, {}).items():
            cf = entry.get("canonical_file", "")
            if cf and cf != "PENDING":
                all_files.add(cf)
            for sup in entry.get("supersedes", []):
                all_files.add(sup)
    # Top-level archived_files list
    for af in registry.get("archived_files", []):
        all_files.add(af)
    return all_files


def get_superseded_files(registry):
    """
    Return set of files that are explicitly superseded (non-canonical variants).
    These are excluded from the duplicate-active check.
    """
    superseded = set()
    for section in ["canon", "named_canons"]:
        for key, entry in registry.get(section, {}).items():
            for sup in entry.get("supersedes", []):
                superseded.add(sup)
    for af in registry.get("archived_files", []):
        superseded.add(af)
    return superseded


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
    superseded_files = get_superseded_files(registry)

    # Collect actual files in canon/
    canon_files = [
        f for f in os.listdir(CANON_DIR)
        if os.path.isfile(os.path.join(CANON_DIR, f))
        and f not in SKIP_FILES
    ]

    # Track active (non-deprecated, non-superseded) files per C-number
    active_by_cnumber = {}

    for fname in canon_files:
        fpath = os.path.join(CANON_DIR, fname)  # e.g. canon/C157_...
        relative_path = f"canon/{fname}"

        # Skip known non-authoritative files (by filename suffix)
        if is_non_authoritative(fname):
            continue

        # Skip files explicitly registered as superseded/archived
        if relative_path in superseded_files:
            continue

        # Check if this active file is registered as a canonical
        if relative_path not in canonical_files:
            violations.append(
                f"UNREGISTERED ACTIVE FILE: {relative_path}\n"
                f"  → Add to REGISTRY.json or add a _DEPRECATED/_ARCHIVED suffix."
            )

        # Track duplicates by C-number (only non-superseded files)
        c_num = extract_c_number(fname)
        if c_num:
            active_by_cnumber.setdefault(c_num, []).append(fname)

    # Check for duplicate active files under same C-number
    for c_num, files in active_by_cnumber.items():
        active_non_deprecated = [
            f for f in files
            if not is_non_authoritative(f)
            and f"canon/{f}" not in superseded_files
        ]
        if len(active_non_deprecated) > 1:
            violations.append(
                f"DUPLICATE ACTIVE FILES for {c_num}:\n"
                + "\n".join(f"  - {f}" for f in active_non_deprecated)
                + "\n  → Only one file per C-number may be active. Mark others _ARCHIVED."
            )

    if violations:
        print(f"\n\u274c CANON LINT FAILED \u2014 {len(violations)} violation(s):\n")
        for v in violations:
            print(v)
            print()
        sys.exit(1)
    else:
        print(f"\u2705 CANON LINT PASSED \u2014 {len(canon_files)} files checked, registry consistent.")
        sys.exit(0)


if __name__ == "__main__":
    lint()
