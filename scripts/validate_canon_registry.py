#!/usr/bin/env python3
"""
validate_canon_registry.py

Canon Authority Registry Validator — Block 1.3 of Issue #642

Runs against the GAIA-OS canon/ directory and canon/REGISTRY.json to:
  1. Detect any Canon ID with more than one non-suffixed .md file (ERROR)
  2. Detect any canon file missing a Status: header (WARNING)
  3. Detect any canon file not listed in REGISTRY.json (WARNING)
  4. Detect any REGISTRY.json entry whose authoritative file does not exist (ERROR)

Usage:
  python scripts/validate_canon_registry.py
  python scripts/validate_canon_registry.py --strict   # Treat warnings as errors

Exit codes:
  0 — All checks passed
  1 — One or more ERRORs found
  2 — One or more WARNINGs found (only in --strict mode)
"""

import os
import re
import json
import sys
import argparse
from collections import defaultdict
from pathlib import Path

CANON_DIR = Path("canon")
REGISTRY_PATH = Path("canon/REGISTRY.json")

SUFFIXES = [
    "_CANONICAL",
    "_ARCHIVED",
    "_DEPRECATED",
    "_DEPRECATED_FSO002",
]

STATUS_PATTERN = re.compile(r"^Status:\s*\S+", re.MULTILINE)


def is_suffixed(filename: str) -> bool:
    stem = filename.replace(".md", "")
    return any(stem.endswith(suffix) for suffix in SUFFIXES)


def extract_canon_id_prefix(filename: str) -> str:
    """Extract the base Canon ID prefix (e.g. 'C154', 'BIOPHOTON_01') from filename."""
    stem = filename.replace(".md", "")
    for suffix in SUFFIXES:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


def get_all_registry_files(registry: dict) -> set:
    """Collect all files referenced anywhere in the registry."""
    referenced = set()
    skip_keys = {"_meta"}
    for canon_id, entry in registry.items():
        if canon_id in skip_keys:
            continue
        if isinstance(entry, dict):
            auth = entry.get("authoritative", "")
            if auth.startswith("canon/"):
                referenced.add(auth)
            for key in ["supersedes", "deprecated", "archived"]:
                for path in entry.get(key, []):
                    referenced.add(path)
    return referenced


def main():
    parser = argparse.ArgumentParser(description="Validate GAIA-OS Canon Authority Registry")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    errors = []
    warnings = []

    # --- Load Registry ---
    if not REGISTRY_PATH.exists():
        print(f"[ERROR] Registry file not found: {REGISTRY_PATH}")
        sys.exit(1)

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    registry_files = get_all_registry_files(registry)

    # --- Scan canon/ directory ---
    if not CANON_DIR.exists():
        print(f"[ERROR] Canon directory not found: {CANON_DIR}")
        sys.exit(1)

    all_md_files = sorted(CANON_DIR.glob("*.md"))

    # Group non-suffixed files by their base prefix
    prefix_to_files = defaultdict(list)
    for md_file in all_md_files:
        if not is_suffixed(md_file.name):
            prefix = extract_canon_id_prefix(md_file.name)
            prefix_to_files[prefix].append(md_file.name)

    # CHECK 1: Multiple non-suffixed files per prefix
    for prefix, files in prefix_to_files.items():
        if len(files) > 1:
            errors.append(
                f"[ERROR] Canon ID '{prefix}' has {len(files)} non-suffixed files (ambiguity): "
                + ", ".join(files)
            )

    # CHECK 2: Missing Status: header
    for md_file in all_md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
            if not STATUS_PATTERN.search(content):
                warnings.append(
                    f"[WARN] Missing 'Status:' header in: {md_file.name}"
                )
        except Exception as e:
            warnings.append(f"[WARN] Could not read {md_file.name}: {e}")

    # CHECK 3: Files not listed in registry
    for md_file in all_md_files:
        rel_path = f"canon/{md_file.name}"
        if rel_path not in registry_files:
            warnings.append(f"[WARN] File not listed in REGISTRY.json: {md_file.name}")

    # CHECK 4: Registry entries pointing to non-existent files
    skip_keys = {"_meta"}
    for canon_id, entry in registry.items():
        if canon_id in skip_keys:
            continue
        if not isinstance(entry, dict):
            continue
        auth = entry.get("authoritative", "")
        if auth.startswith("canon/"):
            auth_path = Path(auth)
            if not auth_path.exists():
                errors.append(
                    f"[ERROR] Canon ID '{canon_id}' authoritative file does not exist: {auth}"
                )

    # --- Report ---
    total_files = len(all_md_files)
    total_ids = len([k for k in registry.keys() if k != "_meta"])

    print(f"\n{'='*60}")
    print(f"GAIA-OS Canon Authority Registry Validator")
    print(f"{'='*60}")
    print(f"Canon files scanned : {total_files}")
    print(f"Registry IDs loaded : {total_ids}")
    print(f"Errors              : {len(errors)}")
    print(f"Warnings            : {len(warnings)}")
    print(f"{'='*60}\n")

    for err in errors:
        print(err)

    for warn in warnings:
        print(warn)

    if errors:
        print(f"\n[FAIL] {len(errors)} error(s) found. Registry validation failed.")
        sys.exit(1)

    if args.strict and warnings:
        print(f"\n[FAIL] {len(warnings)} warning(s) found (--strict mode). Validation failed.")
        sys.exit(2)

    print("\n[PASS] Canon Registry validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
