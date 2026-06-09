"""
core/canon_loader.py — Backward-compatibility shim.

CanonLoader and its private helpers were moved to core.rag.canon_loader
as part of the RAG module reorganisation.  This shim re-exports everything
so that any legacy import paths (e.g. `from core.canon_loader import CanonLoader`)
continue to work without changes.

Do not add new logic here — use core.rag.canon_loader directly.
"""
from core.rag.canon_loader import (  # noqa: F401  (re-export)
    CanonLoader,
    _tokenize,
    _term_freq,
    _chunk_text,
    _best_excerpt,
)

__all__ = ["CanonLoader", "_tokenize", "_term_freq", "_chunk_text", "_best_excerpt"]
