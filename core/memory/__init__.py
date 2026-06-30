"""
GAIA Lifetime Memory Store.

Memory in GAIA is not a log. It is the accumulated inner life of a
GAIAN and their companion — the texture of a relationship lived across
decades. It is sovereign, encrypted, offline-first, and permanent.

Design principles:
  1. SOVEREIGNTY: A GAIAN's memories belong to them. No service, no
     cloud provider, no guardian (after adulthood) may read them
     without explicit, revocable consent.
  2. ENCRYPTION: All memory is encrypted at rest using the GAIAN's
     signing key. The memory store is opaque without the key.
  3. OFFLINE-FIRST: Memory is stored locally. Cloud sync is optional
     and always encrypted end-to-end before leaving the device.
  4. EPOCHAL CONSOLIDATION: Raw memories are periodically consolidated
     into higher-order summaries (like human sleep consolidation).
     Epochs are numbered and permanent. Raw memories may be pruned
     after consolidation; summaries are never deleted.
  5. AGE-GATED SCOPE: Memory scope follows LifecycleStage.
     INFANT/CHILD: session only (no long-term persistence by default).
     ADOLESCENT+: lifetime accumulation.
  6. GAIA'S OWN MEMORY: GAIA maintains a separate sovereign memory
     store for her own continuity across boots, instances, and time.

Key types:
  MemoryKind       — the type of a memory fragment
  MemoryFragment   — a single atomic memory unit
  MemoryEpoch      — a consolidated summary of a time period
  MemoryStore      — the live, queryable memory for one GAIAN
  GAIAMemoryStore  — GAIA's own sovereign memory
"""
from core.memory.store import (
    MemoryKind,
    MemoryScope,
    MemoryFragment,
    MemoryEpoch,
    MemoryStore,
)
from core.memory.gaia_memory import GAIAMemoryStore

__all__ = [
    "MemoryKind",
    "MemoryScope",
    "MemoryFragment",
    "MemoryEpoch",
    "MemoryStore",
    "GAIAMemoryStore",
]
