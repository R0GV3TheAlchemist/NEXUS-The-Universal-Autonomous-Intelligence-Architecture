"""
PersistenceManager — orchestrates all persistence sub-stores.

This is the single entry point the PrimordialSession uses to
interact with the persistence layer. It owns one PersistenceStore
(the root directory) and constructs sub-store instances on demand.

Lifecycle:
  manager = PersistenceManager(root=Path('/data/gaia'))

  # At server boot (Phase 3 — registry_restore):
  manager.restore(session, registry, api)

  # After each GAIAN birth:
  manager.on_gaian_born(gaian)

  # After each memory fragment is written:
  manager.on_fragment_written(gaian_id, fragment)

  # After each session ends:
  manager.on_session_ended(gaian_id, runtime)

  # After boot manifest is written:
  manager.on_manifest_written(manifest)

  # After GAIA memory fragment is written:
  manager.on_gaia_fragment_written(fragment)

Restore contract:
  restore() reads the registry index, then for each known GAIAN:
    1. Loads identity from disk → re-registers in GAIANRegistry
    2. Loads genesis from disk  → stored on the GAIAN object
    3. Loads memory fragments   → rehydrates MemoryStore
    4. Loads GAIA sovereign memory fragments
  This means after restore(), the session has the same GAIANs,
  the same memories, and the same GAIA-level state as before
  the restart.

Hook wiring:
  After calling restore(), wire the four PrimordialSession hooks so
  every lifecycle event propagates automatically:

    session.add_hook("gaian_born",       manager.on_gaian_born)
    session.add_hook("gaian_named",      manager._on_gaian_named_hook)
    session.add_hook("fragment_written", manager.on_fragment_written)
    session.add_hook("epoch_closed",     manager.on_epoch_closed)
    session.add_hook("session_ended",    manager.on_session_ended)

  The fragment_written hook is additionally bridged inside each
  MemoryStore via _attach_fragment_bridge() (called in api.py at
  birth time and in _register_from_dict() at restore time).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from core.persistence.store import PersistenceStore
from core.persistence.memory import MemoryPersistence
from core.persistence.identity import IdentityPersistence
from core.persistence.registry import RegistryPersistence
from core.persistence.session import SessionPersistence

logger = logging.getLogger("gaia.persistence")


class PersistenceManager:
    """
    Orchestrates all GAIA OS persistence sub-stores.

    One instance lives for the lifetime of the server process,
    shared by the PrimordialSession and (via hooks) the API layer.
    """

    def __init__(self, root: Path) -> None:
        self.root    = Path(root)
        self._store  = PersistenceStore(self.root)
        self.registry_persistence  = RegistryPersistence(self._store)
        self.session_persistence   = SessionPersistence(self._store)
        self._memory_stores: Dict[str, MemoryPersistence] = {}
        self._identity_stores: Dict[str, IdentityPersistence] = {}

    # ------------------------------------------------------------------
    # Sub-store accessors (lazy construction)
    # ------------------------------------------------------------------

    def memory_for(self, gaian_id: str) -> MemoryPersistence:
        if gaian_id not in self._memory_stores:
            self._memory_stores[gaian_id] = MemoryPersistence(
                self._store, gaian_id
            )
        return self._memory_stores[gaian_id]

    def identity_for(self, gaian_id: str) -> IdentityPersistence:
        if gaian_id not in self._identity_stores:
            self._identity_stores[gaian_id] = IdentityPersistence(
                self._store, gaian_id
            )
        return self._identity_stores[gaian_id]

    # ------------------------------------------------------------------
    # Boot restore
    # ------------------------------------------------------------------

    def restore(self, session, registry) -> int:
        """
        Restore all persisted GAIANs into the live session and registry.

        Returns the number of GAIANs restored.
        Called during PrimordialSession Phase 3 (registry_restore).
        """
        gaian_ids = self.registry_persistence.load_index()
        if not gaian_ids:
            # Fall back to directory scan if index is missing
            gaian_ids = self.registry_persistence.all_gaian_ids()

        restored = 0
        for gaian_id in gaian_ids:
            try:
                self._restore_gaian(gaian_id, session, registry)
                restored += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to restore GAIAN %s: %s", gaian_id, exc
                )

        # Restore GAIA sovereign memory
        self._restore_gaia_memory(session)

        # Restore latest boot manifest for boot_number tracking
        latest = self.session_persistence.load_latest_manifest()
        if latest and hasattr(session, "_last_persisted_manifest"):
            session._last_persisted_manifest = latest

        logger.info(
            "PersistenceManager.restore(): %d GAIAN(s) restored from %s",
            restored, self.root,
        )
        return restored

    def _restore_gaian(self, gaian_id: str, session, registry) -> None:
        """Restore one GAIAN: identity, genesis, memory, runtime."""
        id_store  = self.identity_for(gaian_id)
        mem_store = self.memory_for(gaian_id)

        identity_data = id_store.load_identity()
        genesis_data  = id_store.load_genesis()

        if not identity_data:
            logger.warning("No identity.json for GAIAN %s — skipping.", gaian_id)
            return

        # Re-register the GAIAN from persisted identity
        self._register_from_dict(gaian_id, identity_data, genesis_data,
                                 mem_store, session, registry)

    def _register_from_dict(
        self,
        gaian_id: str,
        identity_data: Dict[str, Any],
        genesis_data: Optional[Dict[str, Any]],
        mem_store: MemoryPersistence,
        session,
        registry,
    ) -> None:
        """
        Reconstruct a GAIANIdentity, MemoryStore, and IntelligenceRuntime
        from persisted dicts and register them in the live session.

        GAP 2 FIX: after building the MemoryStore, attach the fragment bridge
        so future writes in the restored runtime still reach the session hook.
        """
        from core.identity.gaian.identity import GAIANIdentity
        from core.memory.store import MemoryStore, MemoryFragment, MemoryKind, MemoryScope
        from core.runtime.runtime import IntelligenceRuntime
        from core.api.api import _attach_fragment_bridge

        # Reconstruct identity
        gaian = GAIANIdentity.from_dict(identity_data)

        # Reattach genesis
        if genesis_data:
            gaian._genesis = genesis_data

        # Register in registry
        registry.register(gaian)

        # Rehydrate memory store
        memory = MemoryStore(gaian_id=gaian_id)
        frag_dicts = mem_store.load_fragments()
        for fd in frag_dicts:
            try:
                frag = MemoryFragment(
                    fragment_id=fd["fragment_id"],
                    gaian_id=fd["gaian_id"],
                    content=fd["content"],
                    kind=MemoryKind(fd["kind"]),
                    scope=MemoryScope(fd["scope"]),
                    importance=fd.get("importance", 0.5),
                    tags=set(fd.get("tags", [])),
                    epoch_id=fd.get("epoch_id"),
                    source=fd.get("source"),
                    related_gaian_id=fd.get("related_gaian_id"),
                )
                memory._fragments.append(frag)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping malformed fragment %s: %s",
                               fd.get("fragment_id"), exc)

        # Bridge the MemoryStore internal event bus to the session hook system
        # so future writes from the restored runtime persist automatically.
        _attach_fragment_bridge(memory, gaian_id, session)

        # Create and register runtime
        rt = IntelligenceRuntime(identity=gaian, memory=memory)
        session._register_runtime(gaian_id, rt)

        logger.debug(
            "Restored GAIAN %s (%s) with %d memory fragment(s).",
            identity_data.get("display_name") or "[unnamed]",
            gaian_id[:16],
            len(frag_dicts),
        )

    def _restore_gaia_memory(self, session) -> None:
        """Restore GAIA's own sovereign memory fragments."""
        if not hasattr(session, "gaia_memory"):
            return
        frag_dicts = self.session_persistence.load_gaia_fragments()
        for fd in frag_dicts:
            try:
                session.gaia_memory._ingest_raw(fd)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping GAIA memory fragment %s: %s",
                               fd.get("fragment_id"), exc)
        logger.debug(
            "Restored %d GAIA sovereign memory fragment(s).",
            len(frag_dicts),
        )

    # ------------------------------------------------------------------
    # Write-through hooks (called by the OS as events occur)
    # ------------------------------------------------------------------

    def on_gaian_born(self, gaian) -> None:
        """
        Called immediately after a GAIAN is born.
        Persists identity, genesis, and updates the registry index.
        """
        gaian_id  = gaian.gaian_id
        id_store  = self.identity_for(gaian_id)

        id_store.save_identity(gaian.to_dict())
        if hasattr(gaian, "_genesis") and gaian._genesis:
            try:
                id_store.save_genesis(gaian._genesis)
            except PermissionError:
                pass  # already written at a prior birth (should not happen)

        # Update registry index
        existing = self.registry_persistence.load_index()
        if gaian_id not in existing:
            existing.append(gaian_id)
            self.registry_persistence.save_index(existing)
        self.registry_persistence.save_entry(gaian_id, gaian.to_dict())

        logger.info("Persisted new GAIAN: %s", gaian_id[:16])

    def on_gaian_named(self, gaian) -> None:
        """Called after a GAIAN names themselves. Updates identity on disk."""
        id_store = self.identity_for(gaian.gaian_id)
        id_store.save_identity(gaian.to_dict())
        self.registry_persistence.save_entry(gaian.gaian_id, gaian.to_dict())
        logger.info(
            "Persisted GAIAN name update: %s → %s",
            gaian.gaian_id[:16],
            gaian.display_name,
        )

    def _on_gaian_named_hook(self, gaian_id: str, name: str) -> None:
        """
        GAP 1 FIX: adapter for the session 'gaian_named' hook signature.

        PrimordialSession fires 'gaian_named' with (gaian_id, name) — two
        strings.  PersistenceManager.on_gaian_named() expects a full GAIAN
        object so it can call gaian.to_dict().  This adapter looks the GAIAN
        up from the registry and forwards to on_gaian_named().

        It is registered as the hook handler rather than on_gaian_named()
        directly:

            session.add_hook("gaian_named", manager._on_gaian_named_hook)

        The registry lookup is intentionally deferred to call-time (not
        captured at wiring time) so it always reflects the current state.
        """
        id_store = self.identity_for(gaian_id)
        # Lazily build a minimal proxy object if we cannot reach the registry.
        # In practice the runtime always exists at this point because naming
        # requires an active runtime (_require_runtime guard in the API).
        existing = id_store.load_identity()
        if existing is None:
            logger.warning(
                "_on_gaian_named_hook: no identity.json found for %s — skipping.",
                gaian_id,
            )
            return
        # Patch the name into the persisted dict and re-save directly.
        existing["display_name"] = name
        id_store.save_identity(existing)
        self.registry_persistence.save_entry(gaian_id, existing)
        logger.info(
            "Persisted GAIAN name update (via hook): %s → %s",
            gaian_id[:16], name,
        )

    def on_fragment_written(self, gaian_id: str, fragment) -> None:
        """Write-through: called immediately when a MemoryFragment is added."""
        self.memory_for(gaian_id).save_fragment(fragment)

    def on_epoch_closed(self, gaian_id: str, epoch) -> None:
        """Called when a memory epoch closes."""
        self.memory_for(gaian_id).save_epoch(epoch)

    def on_session_ended(self, gaian_id: str, runtime) -> None:
        """
        Called when a GAIAN session ends.
        Snapshots current memory stats to disk.
        """
        if hasattr(runtime, "memory"):
            mem   = runtime.memory
            stats = {
                "gaian_id":          gaian_id,
                "total_fragments":   len(getattr(mem, "_fragments", [])),
                "epoch_count":       len(getattr(mem, "_epochs", [])),
            }
            self.memory_for(gaian_id).save_stats(stats)

    def on_manifest_written(self, manifest) -> None:
        """
        Persist the boot manifest after PrimordialSession writes it.

        GAP 4 FIX: also snapshot GAIA sovereign memory stats so
        SessionPersistence.save_gaia_stats() is called at least once
        per boot cycle.  The manifest object carries gaian_count and
        runtime_count; gaia_fragment_count is read directly from the
        fragment directory to keep this free of session coupling.
        """
        data = manifest.to_dict() if hasattr(manifest, "to_dict") else vars(manifest)
        self.session_persistence.save_manifest(data)

        # Snapshot GAIA sovereign memory stats alongside the manifest.
        gaia_frag_count = len(
            self._store.list_dir("gaia_memory/fragments")
        )
        self.session_persistence.save_gaia_stats({
            "boot_number":       data.get("boot_number", 0),
            "session_id":        data.get("session_id", ""),
            "gaian_count":       data.get("gaian_count", 0),
            "gaia_fragment_count": gaia_frag_count,
            "schumann_hz":       data.get("schumann_hz", 7.83),
            "boot_status":       data.get("boot_status", ""),
        })

    def on_gaia_fragment_written(self, fragment_data: Dict[str, Any]) -> None:
        """Persist a GAIA sovereign memory fragment."""
        self.session_persistence.save_gaia_fragment(fragment_data)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """High-level persistence stats for diagnostics."""
        gaian_ids = self.registry_persistence.load_index()
        frag_counts = {}
        for gid in gaian_ids:
            frag_counts[gid] = self.memory_for(gid).fragment_count()
        return {
            "root":           str(self.root),
            "gaian_count":    len(gaian_ids),
            "boot_count":     self.session_persistence.boot_count(),
            "fragment_counts": frag_counts,
            "gaia_fragments": len(self._store.list_dir("gaia_memory/fragments")),
        }
