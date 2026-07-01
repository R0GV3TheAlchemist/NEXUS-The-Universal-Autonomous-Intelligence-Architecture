"""
core/storage/memory_backend.py
==============================
MemoryBackend — In-process, ephemeral StorageBackend implementation.

Use cases
---------
1. Unit tests — no disk I/O, fully isolated, instantaneous teardown.
2. Ephemeral mesh nodes — relay-only nodes that should not persist state.
3. Development REPL sessions where persistence is unwanted.

Thread safety: asyncio-safe (dict operations are GIL-protected in CPython).
Data is lost when the process exits.  Do NOT use for production Gaian
memories or audit ledgers.

Issue: #281
"""

from __future__ import annotations

import time


class MemoryBackend:
    """
    In-memory key-value store.  Implements the StorageBackend protocol.

    Supports TTL via an expiry dict.  Expired keys are pruned lazily on
    every get() and query() call.
    """

    def __init__(self) -> None:
        self._store:   dict[str, bytes] = {}
        self._expires: dict[str, float] = {}  # key → UNIX expiry timestamp

    def _is_expired(self, key: str) -> bool:
        exp = self._expires.get(key)
        return exp is not None and time.time() > exp

    def _prune_key(self, key: str) -> None:
        self._store.pop(key, None)
        self._expires.pop(key, None)

    async def put(
        self, key: str, value: bytes, ttl: int | None = None
    ) -> None:
        self._store[key] = value
        if ttl is not None:
            self._expires[key] = time.time() + ttl
        elif key in self._expires:
            del self._expires[key]  # clear any previous TTL

    async def get(self, key: str) -> bytes | None:
        if self._is_expired(key):
            self._prune_key(key)
            return None
        return self._store.get(key)

    async def query(
        self, prefix: str, limit: int = 100
    ) -> list[tuple[str, bytes]]:
        now = time.time()
        results = []
        for key in sorted(self._store.keys()):
            if not key.startswith(prefix):
                continue
            exp = self._expires.get(key)
            if exp is not None and now > exp:
                self._prune_key(key)
                continue
            results.append((key, self._store[key]))
            if len(results) >= limit:
                break
        return results

    async def delete(self, key: str) -> None:
        self._prune_key(key)

    async def close(self) -> None:
        self._store.clear()
        self._expires.clear()

    async def ping(self) -> bool:
        return True

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"MemoryBackend(keys={len(self._store)})"
