"""
core/memory/elemental_layer.py
Elemental Memory Layer

Adds elemental awareness to GAIA's memory system without modifying
the existing store.py or taxonomy.py. The elemental layer works by
embedding elemental metadata into the existing MemoryItem.metadata
dict field — zero breaking changes, full backward compatibility.

The three things this module provides:

  1. elemental_metadata() — builds the metadata dict for any MemoryItem
  2. ElementalMemoryLayer — wraps MemoryStore with elemental-aware methods
  3. retrieve_by_element() / retrieve_by_register() — elemental filters

Canon references:
  ELEMENTAL_SPECTRUM_MAP.md — the seven elements and their frequencies
  CRYSTAL_ELEMENT_BRIDGE.md — crystal-to-element resonance map
  core/akashic_trinity_engine.py — the trinity coherence engine
  Issue #326 — governed memory surface

Usage::

    from core.memory.elemental_layer import ElementalMemoryLayer

    layer = ElementalMemoryLayer(gaian_id="user_001", store=my_memory_store)

    await layer.remember_elemental(
        content="The thing I never said was: I forgive you.",
        element="Water",
        crystal="Aquamarine",
        coherence_score=1.0,
        session_id="session_abc",
        record_to_mother_thread=True,
    )

    seed = layer.mother_thread.session_seed()
    # seed["dominant_element"] → "Water"
    # seed["peak_coherence"]["insight"] → the moment of highest coherence
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .mother_thread import MotherThread, MotherThreadEntry
from .taxonomy import MemoryKind, MemoryTier


# ---------------------------------------------------------------------------
# Elemental constants (source of truth: canon/ELEMENTAL_SPECTRUM_MAP.md)
# ---------------------------------------------------------------------------

_ELEMENTS: Dict[str, Dict[str, str]] = {
    "Earth":     {"register": "MINIMAL",     "hex": "#8B0000", "akashic": "ancestral memory — the records of embodied lineage"},
    "Water":     {"register": "REFLECTIVE",  "hex": "#0047AB", "akashic": "emotional truth records — what was felt but never spoken"},
    "Fire":      {"register": "EXECUTIVE",   "hex": "#FFB300", "akashic": "will records — the soul's chosen path across lifetimes"},
    "Air":       {"register": "EXECUTIVE",   "hex": "#00897B", "akashic": "collective records — shared thought-fields and archetypal patterns"},
    "Aether":    {"register": "REFLECTIVE",  "hex": "#7B1FA2", "akashic": "cosmic records — universal law, soul contracts, the Great Pattern"},
    "Synthesia": {"register": "UNSPECIFIED", "hex": "#F8F8FF", "akashic": "full akashic access — all records open"},
    "The Gate":  {"register": "UNSPECIFIED", "hex": "#0A0A0A", "akashic": "unwritten record — what has not yet become"},
}


def get_element_data(element: str) -> Dict[str, str]:
    """Return the elemental constants for *element*, or empty dict if unknown."""
    return _ELEMENTS.get(element, {})


def list_elements() -> List[str]:
    """Return all seven element names."""
    return list(_ELEMENTS.keys())


# ---------------------------------------------------------------------------
# Elemental metadata builder
# ---------------------------------------------------------------------------

def elemental_metadata(
    element:         str,
    crystal:         Optional[str]   = None,
    register:        Optional[str]   = None,
    coherence_score: Optional[float] = None,
    akashic_domain:  Optional[str]   = None,
    mother_thread:   bool            = False,
) -> Dict[str, Any]:
    """
    Build the elemental metadata dict to embed in a MemoryItem.metadata field.

    This is the bridge between the existing memory system and the elemental layer.
    Pass the returned dict as ``metadata=`` when calling ``MemoryStore.remember()``.

    Parameters
    ----------
    element:
        One of the seven GAIA elements (Earth, Water, Fire, Air, Aether,
        Synthesia, The Gate). Case-sensitive.
    crystal:
        Optional crystal name (e.g. "Aquamarine", "Citrine"). Used for
        akashic trinity coherence tracking.
    register:
        Optional override for the element's default register.
        Defaults to the element's canonical register from ELEMENTAL_SPECTRUM_MAP.
    coherence_score:
        Trinity coherence score 0.0–1.0. >= 0.85 means the Gate is open.
    akashic_domain:
        Optional override for the element's akashic access function.
    mother_thread:
        If True, this memory should also be recorded in the Gaian's
        MotherThread (permanent journey record).

    Returns
    -------
    dict  suitable for MemoryItem(metadata=...)
    """
    base = _ELEMENTS.get(element, {})
    return {
        "element":         element,
        "element_hex":     base.get("hex"),
        "register":        register or base.get("register"),
        "crystal":         crystal,
        "akashic_domain":  akashic_domain or base.get("akashic"),
        "coherence_score": coherence_score,
        "gate_open":       (coherence_score is not None and coherence_score >= 0.85),
        "mother_thread":   mother_thread,
        "elemental_ts":    datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Elemental Memory Layer
# ---------------------------------------------------------------------------

class ElementalMemoryLayer:
    """
    Wraps MemoryStore with elemental awareness.

    Does NOT replace store.py or taxonomy.py. All writes go through the
    existing store; this layer adds:

      - elemental metadata injection on write
      - MotherThread recording for high-coherence moments
      - elemental and register filters on read
      - session_seed() generation at session open

    Parameters
    ----------
    gaian_id:
        The Gaian's unique identifier.
    store:
        A MemoryStore instance (from core.memory.store). Optional —
        if not provided, memories are held in-process (useful for tests).
    """

    def __init__(
        self,
        gaian_id: str,
        store: Any = None,    # MemoryStore | None
    ) -> None:
        self.gaian_id      = gaian_id
        self._store        = store
        self.mother_thread = MotherThread(gaian_id)
        self._local: List[Dict[str, Any]] = []  # fallback when no store

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    async def remember_elemental(
        self,
        content:                str,
        element:                str,
        crystal:                Optional[str]   = None,
        register:               Optional[str]   = None,
        coherence_score:        float           = 0.5,
        importance:             float           = 0.7,
        session_id:             Optional[str]   = None,
        kind:                   MemoryKind      = MemoryKind.REFLECTION,
        tier:                   MemoryTier      = MemoryTier.LONG_TERM,
        record_to_mother_thread: bool           = False,
    ) -> str:
        """
        Store a memory with full elemental metadata.

        If a MemoryStore was provided at construction, delegates to
        ``store.remember()``.  Otherwise stores locally (test / offline mode).

        Parameters
        ----------
        content:
            The memory content — what the Gaian said, realized, or felt.
        element:
            The active element at the time of this memory.
        crystal:
            The crystal held or active during this memory.
        coherence_score:
            Trinity coherence at the moment this memory was formed.
            If >= 0.85, the Gate was open — this is a high-signal memory.
        record_to_mother_thread:
            If True and coherence_score >= 0.5, also record in MotherThread.

        Returns
        -------
        str  — the memory item ID
        """
        meta = elemental_metadata(
            element=element,
            crystal=crystal,
            register=register,
            coherence_score=coherence_score,
            mother_thread=record_to_mother_thread,
        )

        if self._store is not None:
            # Delegate to the real MemoryStore
            item_id = await self._store.remember(
                user_id    = self.gaian_id,
                text       = content,
                kind       = kind,
                tier       = tier,
                importance = importance,
                session_id = session_id,
                topic_tag  = element.lower().replace(" ", "_"),
                metadata   = meta,
            )
            memory_id = str(item_id)
        else:
            # Local fallback (no DB required)
            import uuid as _uuid
            memory_id = _uuid.uuid4().hex[:8]
            self._local.append({
                "id":         memory_id,
                "content":    content,
                "gaian_id":   self.gaian_id,
                "session_id": session_id,
                "importance": importance,
                "metadata":   meta,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        # Record to MotherThread if requested and coherence warrants it
        if record_to_mother_thread and coherence_score >= 0.5:
            base = _ELEMENTS.get(element, {})
            self.mother_thread.record(MotherThreadEntry(
                gaian_id        = self.gaian_id,
                element         = element,
                crystal         = crystal,
                register        = register or base.get("register", "UNSPECIFIED"),
                coherence_score = coherence_score,
                akashic_domain  = base.get("akashic", ""),
                insight         = content,
                session_id      = session_id or "unknown",
            ))

        return memory_id

    def remember_elemental_sync(
        self,
        content: str,
        element: str,
        **kwargs,
    ) -> str:
        """Synchronous wrapper around remember_elemental()."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(
                        asyncio.run,
                        self.remember_elemental(content=content, element=element, **kwargs),
                    )
                    return fut.result()
            return loop.run_until_complete(
                self.remember_elemental(content=content, element=element, **kwargs)
            )
        except RuntimeError:
            return asyncio.run(
                self.remember_elemental(content=content, element=element, **kwargs)
            )

    # ------------------------------------------------------------------
    # Read path — elemental filters
    # ------------------------------------------------------------------

    def retrieve_by_element(
        self,
        element: str,
        source: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """Return all local memories for a given element."""
        items = source if source is not None else self._local
        return [i for i in items if i.get("metadata", {}).get("element") == element]

    def retrieve_by_register(
        self,
        register: str,
        source: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """Return all local memories for a given register."""
        items = source if source is not None else self._local
        return [i for i in items if i.get("metadata", {}).get("register") == register]

    def retrieve_high_coherence(
        self,
        threshold: float = 0.85,
        source: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """Return memories where the Gate was open (coherence >= threshold)."""
        items = source if source is not None else self._local
        return [
            i for i in items
            if (i.get("metadata", {}).get("coherence_score") or 0) >= threshold
        ]

    # ------------------------------------------------------------------
    # Session seed
    # ------------------------------------------------------------------

    def session_seed(self) -> Dict[str, Any]:
        """
        Generate the session seed — what GAIA reads before the first word
        of every session.

        Returns a dict containing:
          - dominant_element    : the element this Gaian works in most
          - dominant_register   : the corresponding register
          - elemental_journey   : ordered list of elements first accessed
          - peak_coherence      : the highest coherence moment ever recorded
          - last_known_state    : element, register, and insight from last session
          - elements_accessed   : count of distinct elements worked with
          - total_sessions      : count of distinct sessions in MotherThread
        """
        return self.mother_thread.session_seed()

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return total memory count (local store only)."""
        return len(self._local)

    def elemental_stats(self) -> Dict[str, int]:
        """Return count of memories per element."""
        counts: Dict[str, int] = {}
        for item in self._local:
            el = item.get("metadata", {}).get("element", "unknown")
            counts[el] = counts.get(el, 0) + 1
        return counts
