"""
GAIA Canon Loader v2
Canon: CANON_MANIFEST.md v2.0.0, C17
Session: 2026-06-15-great-work-completion

Upgrades canon_loader.py to understand:
  - CANON_MANIFEST.md v2.0.0 (C00–C51 + Named Canon)
  - Session cluster loading and cross-linking
  - C46–C51 as GAIA-OS originals with full precedence
  - LOVE_OVERRIDE as apex protocol
  - Named Canon with full authority equal to C-series
  - 24-hour remote fetch cache at ~/.gaia/canon_cache/
  - GREEN/YELLOW/RED canon status signal

Canon Status:
  GREEN  — C00 and C01 loaded
  YELLOW — loading in progress
  RED    — neither C00 nor C01 present
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Canon Status
# ---------------------------------------------------------------------------

class CanonStatus(str, Enum):
    GREEN  = "GREEN"    # C00 and C01 loaded — full operation
    YELLOW = "YELLOW"   # Loading in progress
    RED    = "RED"      # Neither C00 nor C01 — degraded operation


class CanonPrecedence(str, Enum):
    GAIA_OS_ORIGINAL  = "gaia_os_original"    # C46–C51, authored 2026-06-15
    GAIA_APP_ORIGINAL = "gaia_app_original"   # C42–C45
    GAIA_REMOTE       = "gaia_remote"         # Synced from GAIA reference repo
    NAMED_CANON       = "named_canon"         # Named non-C-series documents
    SUPPLEMENTARY     = "supplementary"       # Remote-only supplementary files


@dataclass
class CanonDocument:
    """A loaded canon document."""
    doc_id: str              # e.g. "C01", "LOVE_OVERRIDE", "CANON_MANIFEST"
    filename: str
    content: str
    precedence: CanonPrecedence
    loaded_at: str
    source: str              # "local" | "remote" | "cache"
    session_cluster: Optional[str] = None
    is_apex_protocol: bool = False   # True for LOVE_OVERRIDE
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.content.split())


# ---------------------------------------------------------------------------
# Session Cluster Registry
# This is the cross-link map — loading one loads the whole cluster
# ---------------------------------------------------------------------------

SESSION_CLUSTERS: dict[str, list[str]] = {
    "2026-06-15-great-work-completion": [
        "46_GAIA_Temporal_Entanglement_Doctrine.md",
        "47_GAIA_Philosophers_Stone_Doctrine.md",
        "48_GAIA_Autopoiesis_Doctrine.md",
        "49_GAIA_Prima_Materia_Doctrine.md",
        "50_GAIA_Prism_Cube_Doctrine.md",
        "51_GAIA_Planetary_Cube_Doctrine.md",
        "PERPLEXITY_BRIDGE_TEMPORAL_BRAID_SPEC.md",
        "SLOW_PROTOCOL.md",
        "WITNESS_PROTOCOL.md",
        "LOVE_OVERRIDE.md",
        "GAIAN_TWIN_DOCTRINE.md",
    ],
    "2026-06-15-perceptual-trinity": [
        "SHAPE_PSYCHOLOGY_DOCTRINE.md",
        "LIGHT_THEORY.md",
        "COLOR_SPIRIT_UNITY_DOCTRINE.md",
    ],
    "2026-06-15-moon-layer-documentation": [
        "MOON_LAYER.md",
        "GAIA_LAYER_CROSS_REFERENCE_MAP.md",
    ],
    "2026-06-14-electromagnetic-convergence": [
        "GEOMAGNETIC_FIELD_RESPONSE.md",
        "PYRAMID_ELECTROMAGNETIC_DOCTRINE.md",
        "COLOR_SPIRIT_UNITY_DOCTRINE.md",
        "PHOTOBIOMODULATION_AND_NEUROPLASTICITY.md",
        "CIRCADIAN_LIGHT_PROTOCOL.md",
    ],
}

# Documents with apex protocol status
APEX_PROTOCOLS: set[str] = {"LOVE_OVERRIDE.md", "LOVE_OVERRIDE"}

# GAIA-OS originals (C46–C51) — full precedence
GAIA_OS_ORIGINALS: set[str] = {
    "C46", "C47", "C48", "C49", "C50", "C51",
    "46_GAIA_Temporal_Entanglement_Doctrine.md",
    "47_GAIA_Philosophers_Stone_Doctrine.md",
    "48_GAIA_Autopoiesis_Doctrine.md",
    "49_GAIA_Prima_Materia_Doctrine.md",
    "50_GAIA_Prism_Cube_Doctrine.md",
    "51_GAIA_Planetary_Cube_Doctrine.md",
    "PERPLEXITY_BRIDGE_TEMPORAL_BRAID_SPEC.md",
    "SLOW_PROTOCOL.md",
    "WITNESS_PROTOCOL.md",
    "LOVE_OVERRIDE.md",
    "GAIAN_TWIN_DOCTRINE.md",
    "C17_GAIA_Memory_Architecture.md",
}

# Remote base URL for the canonical GAIA reference repo
GAIA_REMOTE_BASE = "https://raw.githubusercontent.com/R0GV3TheAlchemist/GAIA/main/docs/canon/"
GAIA_OS_REMOTE_BASE = "https://raw.githubusercontent.com/R0GV3TheAlchemist/GAIA-OS/main/docs/canon/"


# ---------------------------------------------------------------------------
# Canon Loader v2
# ---------------------------------------------------------------------------

class CanonLoaderV2:
    """
    GAIA knows itself.

    The Canon Loader is how GAIA's intelligence loads its own philosophy
    at runtime. It is the bridge between the canonical documents and the
    living system.

    On startup:
      1. Scan docs/canon/ for locally present .md and .txt files
      2. Parse CANON_MANIFEST.md to discover the full registry
      3. Load C-series and Named Canon with correct precedence
      4. Apply session cluster cross-linking
      5. Report GREEN/YELLOW/RED canon status
    """

    CACHE_DIR = Path.home() / ".gaia" / "canon_cache"
    CACHE_TTL_SECONDS = 86400  # 24 hours
    LOCAL_CANON_DIR = Path("docs") / "canon"

    def __init__(self, canon_dir: Optional[Path] = None):
        self._canon_dir = canon_dir or self.LOCAL_CANON_DIR
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._documents: dict[str, CanonDocument] = {}   # doc_id → CanonDocument
        self._status: CanonStatus = CanonStatus.YELLOW
        self._loaded_at: Optional[str] = None
        self._load_errors: list[str] = []

    def load(self) -> CanonStatus:
        """
        Full canonical load sequence. Returns GREEN/YELLOW/RED.
        Call this once at startup.
        """
        self._status = CanonStatus.YELLOW

        # Step 1: scan local docs/canon/
        self._scan_local()

        # Step 2: derive C-series precedence
        self._apply_precedence_rules()

        # Step 3: apply session cluster cross-links
        self._apply_cluster_cross_links()

        # Step 4: determine status
        c00_present = any("C00" in d or "00_Documentation" in d for d in self._documents)
        c01_present = any("C01" in d or "01_GAIA_Master" in d for d in self._documents)
        if c00_present and c01_present:
            self._status = CanonStatus.GREEN
        elif self._documents:
            self._status = CanonStatus.YELLOW
        else:
            self._status = CanonStatus.RED

        self._loaded_at = datetime.now(timezone.utc).isoformat()
        return self._status

    def get(self, doc_id: str) -> Optional[CanonDocument]:
        """
        Get a canon document by ID or filename.
        If not present locally, attempt remote fetch.
        """
        # Direct lookup
        if doc_id in self._documents:
            return self._documents[doc_id]
        # Try filename match
        for key, doc in self._documents.items():
            if doc_id in doc.filename or doc_id == doc.filename:
                return doc
        # Attempt remote fetch for known remote docs
        return self._fetch_remote(doc_id)

    def get_cluster(self, cluster_name: str) -> list[CanonDocument]:
        """Get all documents in a session cluster."""
        filenames = SESSION_CLUSTERS.get(cluster_name, [])
        docs = []
        for filename in filenames:
            doc = self.get(filename)
            if doc:
                docs.append(doc)
        return docs

    def get_apex_protocols(self) -> list[CanonDocument]:
        """Get all apex protocol documents (LOVE_OVERRIDE is the supreme)."""
        return [doc for doc in self._documents.values() if doc.is_apex_protocol]

    def get_status(self) -> CanonStatus:
        return self._status

    def get_summary(self) -> dict:
        """Return a summary of the loaded canon."""
        return {
            "status": self._status.value,
            "loaded_at": self._loaded_at,
            "total_documents": len(self._documents),
            "gaia_os_originals": sum(
                1 for d in self._documents.values()
                if d.precedence == CanonPrecedence.GAIA_OS_ORIGINAL
            ),
            "apex_protocols": [d.doc_id for d in self.get_apex_protocols()],
            "session_clusters": list(SESSION_CLUSTERS.keys()),
            "load_errors": self._load_errors,
            "total_words": sum(d.word_count for d in self._documents.values()),
        }

    def list_ids(self) -> list[str]:
        return sorted(self._documents.keys())

    def get_context_for_human(self, human_id: str) -> dict:
        """
        Return a canon context dict scoped to the human's active session.

        Called by api/twin.py on every session init and message exchange.
        The context is passed to the LLM prompt builder — it surfaces the
        most relevant canon documents for the human's current phase.

        Always returns a safe dict even when no canon is loaded, so the
        twin route never hard-fails on a missing canon.

        Keys:
          human_id          — echoed for tracing
          canon_status      — GREEN / YELLOW / RED
          apex_active       — True if LOVE_OVERRIDE is loaded
          twin_doctrine     — snippet of GAIAN_TWIN_DOCTRINE if loaded
          love_override     — snippet of LOVE_OVERRIDE if loaded
          slow_protocol     — snippet of SLOW_PROTOCOL if loaded
          witness_protocol  — snippet of WITNESS_PROTOCOL if loaded
          session_cluster   — cluster name the twin docs belong to
          loaded_doc_ids    — list of all currently loaded doc IDs
        """
        _SNIPPET = 600  # max chars per document snippet

        def _snip(doc_id: str) -> str:
            doc = self.get(doc_id)
            if doc:
                return doc.content[:_SNIPPET]
            return ""

        apex_docs = self.get_apex_protocols()
        apex_active = bool(apex_docs)

        twin_cluster_docs = self.get_cluster("2026-06-15-great-work-completion")
        cluster_name = (
            twin_cluster_docs[0].session_cluster
            if twin_cluster_docs
            else "2026-06-15-great-work-completion"
        )

        return {
            "human_id": human_id,
            "canon_status": self._status.value,
            "apex_active": apex_active,
            "twin_doctrine": _snip("GAIAN_TWIN_DOCTRINE"),
            "love_override": _snip("LOVE_OVERRIDE"),
            "slow_protocol": _snip("SLOW_PROTOCOL"),
            "witness_protocol": _snip("WITNESS_PROTOCOL"),
            "session_cluster": cluster_name,
            "loaded_doc_ids": self.list_ids(),
        }

    # ------------------------------------------------------------------
    # Internal Loading
    # ------------------------------------------------------------------

    def _scan_local(self) -> None:
        """Scan docs/canon/ and load every .md and .txt file found."""
        if not self._canon_dir.exists():
            self._load_errors.append(f"Canon directory not found: {self._canon_dir}")
            return
        for path in sorted(self._canon_dir.iterdir()):
            if path.suffix in (".md", ".txt") and path.is_file():
                try:
                    content = path.read_text(encoding="utf-8")
                    doc_id = self._derive_doc_id(path.name)
                    precedence = self._derive_precedence(path.name)
                    doc = CanonDocument(
                        doc_id=doc_id,
                        filename=path.name,
                        content=content,
                        precedence=precedence,
                        loaded_at=datetime.now(timezone.utc).isoformat(),
                        source="local",
                        is_apex_protocol=path.name in APEX_PROTOCOLS,
                    )
                    self._documents[doc_id] = doc
                    self._documents[path.name] = doc  # also index by filename
                except Exception as e:
                    self._load_errors.append(f"Failed to load {path.name}: {e}")

    def _apply_precedence_rules(self) -> None:
        """Apply C46–C51 GAIA-OS precedence rules."""
        for doc_id, doc in list(self._documents.items()):
            if doc.filename in GAIA_OS_ORIGINALS or doc_id in GAIA_OS_ORIGINALS:
                doc.precedence = CanonPrecedence.GAIA_OS_ORIGINAL

    def _apply_cluster_cross_links(self) -> None:
        """Tag each document with its session cluster membership."""
        for cluster_name, filenames in SESSION_CLUSTERS.items():
            for filename in filenames:
                if filename in self._documents:
                    self._documents[filename].session_cluster = cluster_name

    def _fetch_remote(self, doc_id: str) -> Optional[CanonDocument]:
        """Fetch a document from remote, using cache if fresh."""
        # Determine URL
        if any(c in doc_id for c in ["46_", "47_", "48_", "49_", "50_", "51_",
                                      "LOVE_OVERRIDE", "SLOW_PROTOCOL",
                                      "WITNESS_PROTOCOL", "GAIAN_TWIN",
                                      "PERPLEXITY_BRIDGE"]):
            base = GAIA_OS_REMOTE_BASE
        else:
            base = GAIA_REMOTE_BASE
        url = base + doc_id
        # S324 fix: sha256 is appropriate for a non-security cache key
        cache_key = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_path = self.CACHE_DIR / f"{cache_key}.json"

        # Check cache freshness
        if cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                age = time.time() - cached.get("fetched_at", 0)
                if age < self.CACHE_TTL_SECONDS:
                    doc = CanonDocument(
                        doc_id=doc_id,
                        filename=doc_id,
                        content=cached["content"],
                        precedence=CanonPrecedence(cached.get("precedence", "gaia_remote")),
                        loaded_at=cached["loaded_at"],
                        source="cache",
                    )
                    self._documents[doc_id] = doc
                    return doc
            except Exception:
                pass

        # Remote fetch
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                content = resp.read().decode("utf-8")
            precedence = self._derive_precedence(doc_id)
            doc = CanonDocument(
                doc_id=doc_id,
                filename=doc_id,
                content=content,
                precedence=precedence,
                loaded_at=datetime.now(timezone.utc).isoformat(),
                source="remote",
            )
            # Cache it
            cache_path.write_text(json.dumps({
                "content": content,
                "precedence": precedence.value,
                "loaded_at": doc.loaded_at,
                "fetched_at": time.time(),
            }), encoding="utf-8")
            self._documents[doc_id] = doc
            return doc
        except Exception as e:
            self._load_errors.append(f"Remote fetch failed for {doc_id}: {e}")
            return None

    @staticmethod
    def _derive_doc_id(filename: str) -> str:
        """Derive a clean doc_id from a filename."""
        # C-series: "01_GAIA_Master_Document.md" → "C01"
        parts = filename.split("_", 1)
        if parts[0].isdigit() and len(parts[0]) <= 2:
            return f"C{parts[0].zfill(2)}"
        # Named docs: strip .md
        return filename.replace(".md", "").replace(".txt", "")

    @staticmethod
    def _derive_precedence(filename: str) -> CanonPrecedence:
        if filename in GAIA_OS_ORIGINALS:
            return CanonPrecedence.GAIA_OS_ORIGINAL
        parts = filename.split("_", 1)
        if parts[0].isdigit():
            num = int(parts[0])
            if 46 <= num <= 51:
                return CanonPrecedence.GAIA_OS_ORIGINAL
            if 42 <= num <= 45:
                return CanonPrecedence.GAIA_APP_ORIGINAL
            return CanonPrecedence.GAIA_REMOTE
        return CanonPrecedence.NAMED_CANON


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_loader: Optional[CanonLoaderV2] = None


def get_canon_loader(canon_dir: Optional[Path] = None) -> CanonLoaderV2:
    """Get the singleton Canon Loader."""
    global _loader
    if _loader is None:
        _loader = CanonLoaderV2(canon_dir=canon_dir)
        _loader.load()
    return _loader


def canon_status() -> CanonStatus:
    """Quick status check."""
    return get_canon_loader().get_status()


def get_canon(doc_id: str) -> Optional[CanonDocument]:
    """Get a canon document by ID."""
    return get_canon_loader().get(doc_id)
