"""
core/canon_ingestor.py
Canon Ingestor — scans the canon/ directory, parses every .md file,
and feeds CanonEntry objects into the CanonLoader's TF-IDF index.

This is the missing bridge between the raw canon Markdown documents
and the CanonLoader intelligence layer. Call `ingest_canon_directory()`
during sidecar / server startup, before any inference or search calls.

Usage:
    from core.canon_ingestor import ingest_canon_directory
    report = ingest_canon_directory()          # uses default canon/ path
    report = ingest_canon_directory("canon")   # explicit path

The function returns an IngestionReport with counts and any failures,
so startup code can log a warning if any files were skipped.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.canon.canon_entry import CanonEntry, RegisterSignal
from core.canon_loader import CanonLoader, get_canon_loader

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Matches canonical filenames: C100_something.md, C00_intro.md, etc.
# Deliberately broad — accepts C[0-9]{2,} so it works for any future range.
_CANON_FILENAME_RE = re.compile(r"^(C[0-9]{2,}[^/\\]*)$", re.IGNORECASE)

# YAML-style frontmatter block: ---\n...\n---
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Single YAML key-value line: key: value
_YAML_KV_RE = re.compile(r"^([\w_-]+):\s*(.+)$")

# Fallback author when frontmatter is absent
_DEFAULT_AUTHOR    = "GAIA-OS"
_DEFAULT_VERSION   = "1.0.0"
_FALLBACK_TIMESTAMP = "2026-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------

@dataclass
class IngestionReport:
    """Summary of a canon ingestion run."""
    total_files:   int            = 0
    loaded:        int            = 0
    skipped:       int            = 0
    failed:        int            = 0
    failures:      List[str]      = field(default_factory=list)
    loaded_ids:    List[str]      = field(default_factory=list)

    def log_summary(self) -> None:
        log.info(
            "Canon ingestion complete — "
            "total=%d loaded=%d skipped=%d failed=%d",
            self.total_files, self.loaded, self.skipped, self.failed,
        )
        for msg in self.failures:
            log.warning("Canon ingest failure: %s", msg)
        if self.failed == 0:
            log.info("All canon files ingested successfully.")
        else:
            log.warning(
                "%d canon file(s) failed to ingest — "
                "inference may be incomplete.",
                self.failed,
            )


# ---------------------------------------------------------------------------
# YAML frontmatter parser
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter from a Markdown string.
    Returns (metadata_dict, body_without_frontmatter).
    If no frontmatter is present, returns ({}, original_text).
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    meta: Dict[str, Any] = {}
    for line in match.group(1).splitlines():
        kv = _YAML_KV_RE.match(line.strip())
        if kv:
            key, val = kv.group(1).strip(), kv.group(2).strip()
            # Strip inline YAML comments
            val = val.split(" #")[0].strip()
            # Parse list values: [a, b, c] or - item style not supported here;
            # comma-separated is enough for tags.
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                meta[key] = [v.strip().strip('"') for v in inner.split(",") if v.strip()]
            else:
                meta[key] = val.strip('"')

    body = text[match.end():].strip()
    return meta, body


# ---------------------------------------------------------------------------
# Ref-ID derivation
# ---------------------------------------------------------------------------

def _derive_ref_id(filename: str) -> str:
    """
    Derive a canonical ref_id from a filename.
    'C107_Personal_Gaian_Architecture.md'  ->  'C107'
    'C00_Sovereign_Principles.md'          ->  'C00'
    'ELEMENTAL_STAR.md'                    ->  'ELEMENTAL_STAR'
    """
    stem = Path(filename).stem  # remove .md
    # If starts with C + digits, use just the numeric prefix
    m = re.match(r"^(C[0-9]+)", stem, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Otherwise use the full stem, replacing spaces/hyphens with underscores
    return re.sub(r"[\s-]+", "_", stem).upper()


# ---------------------------------------------------------------------------
# Single-file parser
# ---------------------------------------------------------------------------

def _parse_canon_file(path: Path) -> Optional[CanonEntry]:
    """
    Parse a single .md file into a CanonEntry.
    Returns None if the file is empty or unparseable.
    """
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        log.error("Cannot read %s: %s", path, exc)
        return None

    if not raw.strip():
        log.debug("Skipping empty file: %s", path.name)
        return None

    meta, body = _parse_frontmatter(raw)

    # If no separate body after frontmatter, use the whole file as body
    if not body.strip():
        body = raw.strip()

    ref_id    = meta.get("ref_id")    or meta.get("id")    or _derive_ref_id(path.name)
    author    = meta.get("author")    or _DEFAULT_AUTHOR
    timestamp = meta.get("timestamp") or meta.get("date") or _FALLBACK_TIMESTAMP
    version   = meta.get("version")   or _DEFAULT_VERSION
    title     = meta.get("title")     or Path(path.stem).name.replace("_", " ")

    # Normalise timestamp — ensure it ends with Z or offset
    if re.match(r"^\d{4}-\d{2}-\d{2}$", timestamp):
        timestamp = timestamp + "T00:00:00Z"
    elif not re.search(r"(Z|[+-]\d{2}:\d{2})$", timestamp):
        timestamp = timestamp.rstrip() + "Z"

    # Tags — from frontmatter or derived from filename
    raw_tags = meta.get("tags", [])
    if isinstance(raw_tags, str):
        raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    tags: List[str] = list(raw_tags)

    # Register signal
    raw_signal = meta.get("register_signal", RegisterSignal.UNSPECIFIED.value)
    try:
        signal = RegisterSignal(raw_signal)
    except ValueError:
        signal = RegisterSignal.UNSPECIFIED

    entry = CanonEntry(
        ref_id=ref_id,
        author=author,
        timestamp=timestamp,
        version=version,
        body=body,
        register_signal=signal,
        tags=tags,
        metadata={
            "title":       title,
            "source_file": str(path),
            "filename":    path.name,
        },
    )

    return entry


# ---------------------------------------------------------------------------
# Directory scanner
# ---------------------------------------------------------------------------

def _find_canon_files(canon_dir: Path) -> List[Path]:
    """
    Recursively find all .md files under canon_dir.
    Sorted alphabetically so C100 loads before C101, etc.
    """
    files = sorted(canon_dir.rglob("*.md"))
    log.debug("Found %d .md files under %s", len(files), canon_dir)
    return files


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ingest_canon_directory(
    canon_dir:  str | Path | None = None,
    loader:     Optional[CanonLoader] = None,
    skip_validation: bool = False,
) -> IngestionReport:
    """
    Scan *canon_dir*, parse every .md file, and load each CanonEntry
    into *loader* (defaults to the global singleton from get_canon_loader()).

    Parameters
    ----------
    canon_dir:
        Path to the canon directory.  Defaults to ``<repo_root>/canon``
        resolved relative to this file's location.
    loader:
        CanonLoader instance to populate.  Defaults to the global singleton.
    skip_validation:
        If True, CanonEntry.validate() is not called (useful in tests).

    Returns
    -------
    IngestionReport
        Summary with counts and any per-file failure messages.
    """
    if canon_dir is None:
        # Resolve canon/ relative to the repo root (two levels up from core/)
        canon_dir = Path(__file__).resolve().parent.parent / "canon"
    canon_path = Path(canon_dir)

    if loader is None:
        loader = get_canon_loader()

    report = IngestionReport()

    if not canon_path.exists():
        msg = f"Canon directory not found: {canon_path}"
        log.error(msg)
        report.failures.append(msg)
        report.failed += 1
        return report

    files = _find_canon_files(canon_path)
    report.total_files = len(files)

    for path in files:
        try:
            entry = _parse_canon_file(path)
            if entry is None:
                report.skipped += 1
                continue

            if not skip_validation:
                try:
                    entry.validate()
                except Exception as val_exc:
                    # Validation failure: log but still load — don't block startup
                    log.warning(
                        "Canon entry %s failed validation (will load anyway): %s",
                        entry.ref_id, val_exc,
                    )

            loader.load(entry)
            report.loaded += 1
            report.loaded_ids.append(entry.ref_id)
            log.debug("Loaded canon entry: %s (%s)", entry.ref_id, path.name)

        except Exception as exc:
            msg = f"{path.name}: {exc}"
            log.error("Failed to ingest canon file %s: %s", path.name, exc)
            report.failures.append(msg)
            report.failed += 1

    report.log_summary()
    return report


# ---------------------------------------------------------------------------
# Convenience: validate coverage (for tests and CI)
# ---------------------------------------------------------------------------

def assert_full_coverage(
    canon_dir:  str | Path | None = None,
    loader:     Optional[CanonLoader] = None,
) -> List[str]:
    """
    Return a list of .md filenames in *canon_dir* that are NOT present
    in the loader's index.  An empty list means full coverage.

    Use in tests:
        missing = assert_full_coverage()
        assert missing == [], f"Canon files not in loader: {missing}"
    """
    if canon_dir is None:
        canon_dir = Path(__file__).resolve().parent.parent / "canon"
    canon_path = Path(canon_dir)

    if loader is None:
        loader = get_canon_loader()

    loaded_ids = set(loader.list_ids())
    missing: List[str] = []

    for path in _find_canon_files(canon_path):
        ref_id = _derive_ref_id(path.name)
        if ref_id not in loaded_ids:
            missing.append(path.name)

    return missing
