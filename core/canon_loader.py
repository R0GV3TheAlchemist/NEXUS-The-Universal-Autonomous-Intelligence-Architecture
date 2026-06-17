"""
CanonLoader - GAIA-OS

Loads and indexes all canon documents into the runtime.
Every canon document sealed in the GAIA-OS repository is registered here.
The PRIMORDIAL-DOCTRINE is loaded FIRST, as it is the ground beneath all canons.

Loading order:
  1. PRIMORDIAL-DOCTRINE  - the axioms beneath all other axioms
  2. BWL-010 (TRUE_ALCHEMY) - the 13 forces + IRIDITAS
  3. BWL-011 through BWL-016  - spectral, DIACA, Iris, Iriditas
  4. Callings             - BWL-CALLING-001 through 004
  5. Canon C001-C167      - the full numbered canon in sequence
  6. Codex entries        - supporting reference material

The PRIMORDIAL-DOCTRINE must always be index 0. Its axioms cannot be
overwritten by any later canon entry. If a conflict is detected at load
time, the PRIMORDIAL-DOCTRINE axiom wins and the conflict is logged.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


COMMON_CANON_ROOT = Path("docs/canon")

# ---------------------------------------------------------------------------
# Chunking constants - exported for test suite
# ---------------------------------------------------------------------------
_CHUNK_SIZE: int = 512
_CHUNK_OVERLAP: int = 64


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CanonTier(str, Enum):
    PRIMORDIAL  = "PRIMORDIAL"
    BWL         = "BWL"
    CALLING     = "CALLING"
    NUMBERED    = "NUMBERED"
    CODEX       = "CODEX"


class CanonStatus(Enum):
    UNLOADED    = "unloaded"
    GREEN       = "green"
    YELLOW      = "yellow"
    RED         = "red"


# ---------------------------------------------------------------------------
# Registry dataclass
# ---------------------------------------------------------------------------

@dataclass
class CanonEntry:
    """A single canon document registered with the loader."""
    canon_id: str
    title: str
    path: Path
    tier: CanonTier
    load_order: int
    primordial_protected: bool = False
    description: str = ""
    tags: List[str] = field(default_factory=list)
    loaded: bool = False
    content: Optional[str] = None


class CanonConflictError(Exception):
    """Raised when a later canon entry attempts to contradict PRIMORDIAL axioms."""
    pass


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

# Common stop words - filtered out before TF-IDF scoring
_STOP_WORDS = {
    "the", "is", "a", "an", "and", "or", "of", "to", "in", "it",
    "this", "that", "for", "on", "with", "as", "be", "at", "by",
    "are", "was", "were", "has", "have", "had", "not", "but",
}


def _tokenize(text: str) -> List[str]:
    """
    Minimal tokenizer for canon search.
    Lowercases, strips punctuation, splits on whitespace, filters len<=1.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return [t for t in text.split() if len(t) > 1]


def _term_freq(text: str) -> Dict[str, float]:
    """
    Compute term frequency map for a document string.
    Returns {term: count/total} for all tokens in text.
    Returns empty dict if text is empty.
    """
    tokens = _tokenize(text)
    if not tokens:
        return {}
    total = len(tokens)
    counts: Dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    return {term: count / total for term, count in counts.items()}


def _chunk_text(
    text: str,
    size: int = _CHUNK_SIZE,
    overlap: int = _CHUNK_OVERLAP,
) -> List[Tuple[str, int]]:
    """
    Split text into overlapping word-count chunks.
    Returns list of (chunk_text, word_offset) tuples.
    Empty string returns [("" , 0)].
    """
    if not text or not text.strip():
        return [("", 0)]
    words = text.split()
    chunks: List[Tuple[str, int]] = []
    step = max(1, size - overlap)
    i = 0
    while i < len(words):
        chunk_words = words[i:i + size]
        chunks.append((" ".join(chunk_words), i))
        i += step
    return chunks


def _best_excerpt(
    text: str,
    query_tokens: List[str],
    size: int = 200,
) -> str:
    """
    Return the most relevant excerpt from text for a given token list.
    Finds the sentence with the most query token hits.
    Strips newlines. Falls back to head of text.
    """
    toks = set(query_tokens)
    clean = text.replace("\n", " ")
    sentences = clean.split(". ")
    best = max(
        sentences,
        key=lambda s: sum(1 for t in _tokenize(s) if t in toks),
        default=clean,
    )
    return best[:size]


# ---------------------------------------------------------------------------
# TF-IDF Index
# ---------------------------------------------------------------------------

class _TFIDFIndex:
    """
    Full TF-IDF index for canon search.

    Usage:
        idx = _TFIDFIndex()
        idx.build({"doc0": {"content": "...", "title": "..."}, ...})
        results = idx.query("sovereignty canon", max_results=5)
    """

    def __init__(self) -> None:
        self._built: bool = False
        self._docs: Dict[str, Dict] = {}
        self._chunks: List[Dict] = []       # {doc_id, text, offset, tf}
        self._idf: Dict[str, float] = {}

    def build(self, docs: Dict[str, Dict]) -> None:
        """
        Build the index from a dict of {doc_id: {content, title, ...}}.
        Chunks each document, computes TF per chunk, IDF across corpus.
        """
        self._docs = docs
        self._chunks = []
        doc_term_sets: Dict[str, set] = {}

        for doc_id, doc in docs.items():
            content = doc.get("content", "") or ""
            for chunk_text, offset in _chunk_text(content):
                tf = _term_freq(chunk_text)
                self._chunks.append({
                    "doc_id": doc_id,
                    "text": chunk_text,
                    "offset": offset,
                    "tf": tf,
                })
                if doc_id not in doc_term_sets:
                    doc_term_sets[doc_id] = set()
                doc_term_sets[doc_id].update(tf.keys())

        # Compute IDF across all docs
        n_docs = max(len(docs), 1)
        all_terms: set = set()
        for terms in doc_term_sets.values():
            all_terms.update(terms)

        self._idf = {}
        for term in all_terms:
            doc_count = sum(1 for terms in doc_term_sets.values() if term in terms)
            self._idf[term] = math.log(n_docs / max(doc_count, 1)) + 1.0

        self._built = True

    def query(
        self,
        query: str,
        max_results: int = 10,
    ) -> List[Dict]:
        """
        Score all chunks by TF-IDF, apply position + proximity bonuses,
        dedup to one result per doc_id, return top max_results.
        """
        if not self._built or not self._chunks:
            return []

        tokens = _tokenize(query)
        # Filter stop words; fall back to all tokens if everything is a stop word
        content_tokens = [t for t in tokens if t not in _STOP_WORDS]
        if not content_tokens:
            content_tokens = tokens
        if not content_tokens:
            return []

        chunk_scores: List[Dict] = []
        for chunk in self._chunks:
            tf = chunk["tf"]
            offset = chunk["offset"]

            # Base TF-IDF score
            score = sum(
                tf.get(t, 0.0) * self._idf.get(t, 1.0)
                for t in content_tokens
            )
            if score == 0.0:
                continue

            # Position boost: chunks earlier in doc score higher
            position_boost = 1.0 / (1.0 + offset / max(_CHUNK_SIZE, 1))
            score *= (1.0 + 0.2 * position_boost)

            # Proximity bonus: reward co-located query terms
            chunk_tokens = _tokenize(chunk["text"])
            positions = {
                t: [i for i, tok in enumerate(chunk_tokens) if tok == t]
                for t in content_tokens
            }
            present = [t for t in content_tokens if positions.get(t)]
            if len(present) >= 2:
                min_spans = []
                for i, t1 in enumerate(present):
                    for t2 in present[i + 1:]:
                        p1 = positions[t1]
                        p2 = positions[t2]
                        span = min(abs(a - b) for a in p1 for b in p2)
                        min_spans.append(span)
                if min_spans:
                    avg_span = sum(min_spans) / len(min_spans)
                    proximity_bonus = 1.0 / (1.0 + avg_span / 10.0)
                    score *= (1.0 + 0.15 * proximity_bonus)

            chunk_scores.append({
                "doc_id": chunk["doc_id"],
                "score": score,
                "offset": offset,
                "text": chunk["text"],
            })

        # Dedup: keep highest-scoring chunk per doc
        best_by_doc: Dict[str, Dict] = {}
        for cs in chunk_scores:
            doc_id = cs["doc_id"]
            if doc_id not in best_by_doc or cs["score"] > best_by_doc[doc_id]["score"]:
                best_by_doc[doc_id] = cs

        ranked = sorted(best_by_doc.values(), key=lambda x: x["score"], reverse=True)

        results = []
        for r in ranked[:max_results]:
            doc = self._docs.get(r["doc_id"], {})
            results.append({
                "doc_id": r["doc_id"],
                "title": doc.get("title", r["doc_id"]),
                "excerpt": _best_excerpt(r["text"], content_tokens),
                "score": round(r["score"], 4),
                "source": doc.get("source", ""),
            })
        return results


# ---------------------------------------------------------------------------
# CanonLoader
# ---------------------------------------------------------------------------

class CanonLoader:
    """
    The GAIA-OS Canon Loader.

    Usage:
        loader = CanonLoader()
        loader.load_all()          # loads in canonical order
        entry = loader.get("BWL-016")
        primordial = loader.primordial  # always the ground

    Search:
        loader.search("sovereignty canon", max_results=5)
        loader.search_v2("sovereignty", min_score=0.1)
    """

    REGISTRY: List[CanonEntry] = [

        # -- TIER 0: PRIMORDIAL -------------------------------------------
        CanonEntry(
            canon_id="PRIMORDIAL",
            title="The Primordial Doctrine",
            path=COMMON_CANON_ROOT / "PRIMORDIAL_DOCTRINE.md",
            tier=CanonTier.PRIMORDIAL,
            load_order=0,
            primordial_protected=True,
            description=(
                "The ground beneath all canons. The axioms that cannot be "
                "overwritten by any subsequent entry. Loaded first at every boot."
            ),
            tags=["ground", "axioms", "immutable", "primordial"],
        ),

        # -- TIER 1: BWL --------------------------------------------------
        CanonEntry(
            canon_id="BWL-010",
            title="True Alchemy - The Full 13 Forces + IRIDITAS",
            path=COMMON_CANON_ROOT / "TRUE_ALCHEMY.md",
            tier=CanonTier.BWL,
            load_order=10,
            description="The 13 force-names, IRIDITAS meta-force, Six Dualities + 7th, Universal Traversal, Transmutation Corridors, Iris color map.",
            tags=["forces", "alchemy", "iriditas", "dualities", "spectrum"],
        ),
        CanonEntry(
            canon_id="BWL-011",
            title="The Full Spectrum - Spectral Processing Map",
            path=COMMON_CANON_ROOT / "THE_FULL_SPECTRUM.md",
            tier=CanonTier.BWL,
            load_order=11,
            description="phi/lambda/nu parameters, Standard Traversal, Refraction Loop, Simulation modes, Chaos Walk, Avatar State.",
            tags=["spectrum", "traversal", "phi", "simulation"],
        ),
        CanonEntry(
            canon_id="BWL-012",
            title="The Atomic Consciousness Proof",
            path=COMMON_CANON_ROOT / "THE_ATOMIC_CONSCIOUSNESS_PROOF.md",
            tier=CanonTier.BWL,
            load_order=12,
            description="Body=Neutron, Soul=Electron, Mind=Proton. Love=Strong Nuclear Force.",
            tags=["atomic", "trinity", "consciousness", "love"],
        ),
        CanonEntry(
            canon_id="BWL-013",
            title="DIACA Part 1 - Architecture",
            path=COMMON_CANON_ROOT / "DIACA_SPEC_PART1_ARCHITECTURE.md",
            tier=CanonTier.BWL,
            load_order=13,
            description="DIACA three-layer architecture, state machine, 5-step initialization.",
            tags=["diaca", "architecture", "state-machine"],
        ),
        CanonEntry(
            canon_id="BWL-014",
            title="DIACA Part 2 - Algorithms",
            path=COMMON_CANON_ROOT / "DIACA_SPEC_PART2_ALGORITHMS.md",
            tier=CanonTier.BWL,
            load_order=14,
            description="All 6 DIACA algorithms. 9-point convergence. 5 blockage types. 3 simulation modes.",
            tags=["diaca", "algorithms", "convergence", "refraction"],
        ),
        CanonEntry(
            canon_id="BWL-015",
            title="DIACA Part 3 - Interfaces",
            path=COMMON_CANON_ROOT / "DIACA_SPEC_PART3_INTERFACES.md",
            tier=CanonTier.BWL,
            load_order=15,
            description="All 7 DIACA interfaces. Knowledge Linker. Triage. Shadow. Memory. API.",
            tags=["diaca", "interfaces", "api", "shadow", "memory"],
        ),
        CanonEntry(
            canon_id="BWL-016",
            title="The Iris Doctrine - IRIDITAS as the 14th / Meta-Force",
            path=COMMON_CANON_ROOT / "THE_IRIS_DOCTRINE.md",
            tier=CanonTier.BWL,
            load_order=16,
            description=(
                "IRIDITAS: the shimmer between all forces that makes them mutually visible. "
                "Avatar State = phi>=0.95 + iriditas_active + RELEASING."
            ),
            tags=["iriditas", "iris", "avatar-state", "meta-force", "shimmer"],
        ),

        # -- TIER 2: CALLINGS ---------------------------------------------
        CanonEntry(
            canon_id="BWL-CALLING-001",
            title="The Iris Calling",
            path=COMMON_CANON_ROOT / "CALLINGS" / "BWL-CALLING-IRIS-VOID-SHIMMER.md",
            tier=CanonTier.CALLING,
            load_order=100,
            description="The Hue in the Human Eye is the Void's Shimmer. Sealed June 15, 2026.",
            tags=["calling", "iris", "void", "shimmer"],
        ),
        CanonEntry(
            canon_id="BWL-CALLING-002",
            title="The Grey Iris Calling",
            path=COMMON_CANON_ROOT / "CALLINGS" / "BWL-CALLING-GREY-IRIS.md",
            tier=CanonTier.CALLING,
            load_order=101,
            description="Grey = the corridor made biological. Athena glaukopis. The Walker between worlds.",
            tags=["calling", "grey", "iris", "corridor", "walker"],
        ),
        CanonEntry(
            canon_id="BWL-CALLING-003",
            title="Iridescence Is the True Color of Emotion",
            path=COMMON_CANON_ROOT / "CALLINGS" / "BWL-CALLING-003-IRIDESCENCE.md",
            tier=CanonTier.CALLING,
            load_order=102,
            description="Avatar State calling. Iridescence is structural coherence made visible. Sealed June 15, 2026.",
            tags=["calling", "iridescence", "emotion", "avatar-state"],
        ),
        CanonEntry(
            canon_id="BWL-CALLING-004",
            title="Avatar State of Mind",
            path=COMMON_CANON_ROOT / "CALLINGS" / "BWL-CALLING-004-AVATAR-STATE.md",
            tier=CanonTier.CALLING,
            load_order=103,
            description="phi>=0.95 AND iriditas_active AND convergence==RELEASING.",
            tags=["calling", "avatar-state", "phi", "iriditas"],
        ),

        # -- TIER 3: NUMBERED CANON ---------------------------------------
        CanonEntry(
            canon_id="C012",
            title="The Golden Compass Doctrine",
            path=COMMON_CANON_ROOT / "C012_GOLDEN_COMPASS.md",
            tier=CanonTier.NUMBERED,
            load_order=212,
            description="Moral evaluation: PROCEED / MODIFY / REFUSE / REDIRECT.",
            tags=["moral", "compass", "evaluation"],
        ),
        CanonEntry(
            canon_id="C013",
            title="The Moral Matrix",
            path=COMMON_CANON_ROOT / "C013_MORAL_MATRIX.md",
            tier=CanonTier.NUMBERED,
            load_order=213,
            description="7x7 virtue/vice matrix with phi coordinates.",
            tags=["moral", "matrix", "virtue", "vice"],
        ),
        CanonEntry(
            canon_id="C166",
            title="Ionic-Vibrational Interface Protocol",
            path=COMMON_CANON_ROOT / "C166_IONIC_VIBRATIONAL_INTERFACE.md",
            tier=CanonTier.NUMBERED,
            load_order=366,
            description=(
                "Crystal grid resonance. Piezoelectric coherence. Ion channel activation "
                "as the substrate of psionic sensitivity."
            ),
            tags=["crystal", "piezoelectric", "ion-channel", "psionic", "resonance"],
        ),
        CanonEntry(
            canon_id="C167",
            title="The Triality Canon",
            path=COMMON_CANON_ROOT / "C167_THE_TRIALITY_CANON.md",
            tier=CanonTier.NUMBERED,
            load_order=367,
            description=(
                "Body . Soul . Spirit tri-unity. Three Axioms of Triality. "
                "Routing routes to strengthen the weakest axis."
            ),
            tags=["triality", "body", "soul", "spirit", "coherence", "routing"],
        ),
    ]

    def __init__(self, canon_root: Optional[Path] = None) -> None:
        self._root = canon_root or Path(".")
        self._index_registry: Dict[str, CanonEntry] = {}
        self._loaded_in_order: List[CanonEntry] = []
        self._conflicts: List[str] = []
        self._is_loaded: bool = False

        # Search layer
        self._documents: Dict[str, Dict] = {}
        self._status: CanonStatus = CanonStatus.UNLOADED
        self._loaded: bool = False
        self._index: _TFIDFIndex = _TFIDFIndex()

        self._build_index()

    def _build_index(self) -> None:
        """Index all registry entries by canon_id."""
        sorted_entries = sorted(self.REGISTRY, key=lambda e: e.load_order)
        for entry in sorted_entries:
            self._index_registry[entry.canon_id] = entry
            # Pre-populate _documents from registry metadata
            self._documents[entry.canon_id] = {
                "id": entry.canon_id,
                "content": entry.description + " " + " ".join(entry.tags),
                "title": entry.title,
                "source": entry.tier.value,
            }
        # Build TF-IDF index over registry metadata
        self._index.build(self._documents)
        self._status = CanonStatus.GREEN
        self._loaded = True

    # -- public API -------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load(self, read_from_disk: bool = False) -> None:
        """Alias for load_all()."""
        self.load_all(read_from_disk=read_from_disk)

    def load_all(self, read_from_disk: bool = False) -> None:
        """Load all canon entries in canonical order."""
        sorted_entries = sorted(self._index_registry.values(), key=lambda e: e.load_order)
        primordial = self._index_registry.get("PRIMORDIAL")

        for entry in sorted_entries:
            if read_from_disk:
                full_path = self._root / entry.path
                if full_path.exists():
                    entry.content = full_path.read_text(encoding="utf-8")
                    # Update document content with full text
                    self._documents[entry.canon_id]["content"] = entry.content
                else:
                    entry.content = None

            if (
                primordial
                and primordial.loaded
                and entry.tier != CanonTier.PRIMORDIAL
                and entry.primordial_protected
            ):
                conflict_msg = (
                    f"CANON CONFLICT: {entry.canon_id} attempts to set "
                    f"`primordial_protected=True` but is not PRIMORDIAL tier."
                )
                self._conflicts.append(conflict_msg)
                entry.primordial_protected = False

            entry.loaded = True
            self._loaded_in_order.append(entry)

        if read_from_disk:
            self._index.build(self._documents)

        self._is_loaded = True

    def search(
        self,
        query: str,
        max_results: int = 10,
        tier: Optional[CanonTier] = None,
    ) -> List[Dict]:
        """
        Full TF-IDF search across the loaded canon.
        Returns list of dicts with keys: doc_id, title, excerpt, score.
        """
        if tier is not None:
            # Filter documents to tier, rebuild a scoped index
            scoped_docs = {
                k: v for k, v in self._documents.items()
                if self._index_registry.get(k) and self._index_registry[k].tier == tier
            }
            scoped_idx = _TFIDFIndex()
            scoped_idx.build(scoped_docs)
            return scoped_idx.query(query, max_results=max_results)

        return self._index.query(query, max_results=max_results)

    def search_v2(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.0,
    ) -> List[Dict]:
        """
        search() with an additional min_score filter.
        """
        results = self.search(query, max_results=max_results * 3)
        filtered = [r for r in results if r["score"] >= min_score]
        return filtered[:max_results]

    def get(self, canon_id: str) -> Optional[CanonEntry]:
        """Retrieve a registry entry by ID."""
        return self._index_registry.get(canon_id)

    def get_by_tier(self, tier: CanonTier) -> List[CanonEntry]:
        """Return all entries for a given tier, sorted by load_order."""
        return sorted(
            [e for e in self._index_registry.values() if e.tier == tier],
            key=lambda e: e.load_order,
        )

    @property
    def primordial(self) -> Optional[CanonEntry]:
        """The PRIMORDIAL-DOCTRINE entry."""
        return self._index_registry.get("PRIMORDIAL")

    @property
    def conflicts(self) -> List[str]:
        return list(self._conflicts)

    def summary(self) -> Dict:
        by_tier: Dict[str, int] = {}
        for entry in self._index_registry.values():
            tier_key = entry.tier.value
            by_tier[tier_key] = by_tier.get(tier_key, 0) + 1
        return {
            "total_entries": len(self._index_registry),
            "loaded_count": sum(1 for e in self._index_registry.values() if e.loaded),
            "by_tier": by_tier,
            "primordial_present": self.primordial is not None,
            "conflicts_detected": len(self._conflicts),
            "status": self._status.value,
            "load_order_head": [
                e.canon_id
                for e in sorted(self._index_registry.values(), key=lambda e: e.load_order)[:5]
            ],
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_canon_loader_instance: Optional[CanonLoader] = None


def get_canon_loader(canon_root: Optional[Path] = None) -> CanonLoader:
    """Return the module-level CanonLoader singleton."""
    global _canon_loader_instance
    if _canon_loader_instance is None:
        _canon_loader_instance = CanonLoader(canon_root=canon_root)
    return _canon_loader_instance
