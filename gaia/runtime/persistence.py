"""
gaia.runtime.persistence
~~~~~~~~~~~~~~~~~~~~~~~~
PersistenceManager — writes GAIA runtime state to disk as JSON.

Design principles:
  - Zero external dependencies: only pathlib, json, logging, threading.
  - Atomic writes: data is written to a .tmp file then renamed, so a
    Ctrl-C mid-write never produces a corrupt record file.
  - Append-only fragment log: fragments are appended to a single
    newline-delimited JSON file (fragments.ndjson) so they survive
    partial reads and are easy to stream.
  - Human-readable layout: every file is pretty-printed JSON (indent=2)
    except fragments.ndjson which is one JSON object per line.

Directory layout under persistence_root/:
    identity.json          latest identity record (overwritten on each save)
    fragments.ndjson       append-only log, one fragment per line
    epochs/
        <epoch_id>.json    one file per closed epoch
    sessions/
        <session_id>.json  written when session ends
"""

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("gaia.runtime.persistence")


class PersistenceManager:
    """
    Persists GAIA runtime events to a local directory tree.

    Usage (direct)::

        manager = PersistenceManager(root="gaia_memory")
        manager.save_identity({"session_id": "...", "name": "GAIA-Prime", ...})

    Usage (via hooks registered by server/startup.py)::

        session.register("gaian_named", manager.on_gaian_named)
        session.register("fragment_written", manager.on_fragment_written)
        session.register("epoch_closed", manager.on_epoch_closed)
        session.register("session_ended", manager.on_session_ended)
    """

    def __init__(self, root: str | Path = "gaia_memory") -> None:
        self._root = Path(root)
        self._lock = threading.Lock()
        self._ensure_dirs()
        logger.info("[PersistenceManager] initialised  root=%s", self._root.resolve())

    # ------------------------------------------------------------------
    # Hook-compatible handlers (accept the raw event payload dict)
    # ------------------------------------------------------------------

    def on_gaian_born(self, payload: dict) -> None:
        """Handle gaian_born — seeds the identity file with birth metadata."""
        self.save_identity({
            "session_id": payload["session_id"],
            "name":       None,
            "born_at":    payload["born_at"],
            "status":     "born",
        })

    def on_gaian_named(self, payload: dict) -> None:  # gap-1 handler
        """Handle gaian_named — updates identity with the display name."""
        # Merge with existing identity so we keep born_at etc.
        existing = self._load_identity()
        existing.update({
            "name":     payload["name"],
            "named_at": payload["named_at"],
            "status":   "named",
        })
        self.save_identity(existing)

    def on_fragment_written(self, payload: dict) -> None:  # gap-2 handler
        """Handle fragment_written — appends one line to fragments.ndjson."""
        self.save_fragment(payload)

    def on_epoch_closed(self, payload: dict) -> None:  # gap-3 handler
        """Handle epoch_closed — writes epochs/<epoch_id>.json."""
        self.save_epoch(payload)

    def on_session_ended(self, payload: dict) -> None:
        """Handle session_ended — writes sessions/<session_id>.json."""
        self._atomic_write(
            self._root / "sessions" / f"{payload['session_id']}.json",
            payload,
        )
        logger.info(
            "[PersistenceManager] session saved  session_id=%s",
            payload["session_id"],
        )

    # ------------------------------------------------------------------
    # Public save methods (can be called directly, not just via hooks)
    # ------------------------------------------------------------------

    def save_identity(self, record: dict) -> None:
        """
        Overwrite identity.json with *record*.

        Adds a 'saved_at' timestamp automatically.
        """
        record = dict(record)  # don't mutate caller's dict
        record["saved_at"] = datetime.now(timezone.utc).isoformat()
        self._atomic_write(self._root / "identity.json", record)
        logger.debug("[PersistenceManager] identity saved")

    def save_fragment(self, record: dict) -> None:
        """
        Append *record* as one line to fragments.ndjson.

        Uses a file-level lock so concurrent writes don't interleave.
        """
        record = dict(record)
        record["saved_at"] = datetime.now(timezone.utc).isoformat()
        path = self._root / "fragments.ndjson"
        with self._lock:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.debug(
            "[PersistenceManager] fragment saved  fragment_id=%s",
            record.get("fragment_id", "?"),
        )

    def save_epoch(self, record: dict) -> None:
        """
        Write *record* to epochs/<epoch_id>.json.

        epoch_id must be present in *record*.
        """
        epoch_id = record.get("epoch_id")
        if not epoch_id:
            logger.warning("[PersistenceManager] save_epoch called without epoch_id")
            epoch_id = "unknown"
        record = dict(record)
        record["saved_at"] = datetime.now(timezone.utc).isoformat()
        self._atomic_write(self._root / "epochs" / f"{epoch_id}.json", record)
        logger.info("[PersistenceManager] epoch saved  epoch_id=%s", epoch_id)

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def load_identity(self) -> dict:
        """Return the current identity record, or {} if not yet written."""
        return self._load_identity()

    def load_fragments(self) -> list[dict]:
        """Return all fragment records as a list (reads full ndjson)."""
        path = self._root / "fragments.ndjson"
        if not path.exists():
            return []
        records = []
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        logger.warning(
                            "[PersistenceManager] bad fragment line: %s", exc
                        )
        return records

    def load_epochs(self) -> list[dict]:
        """Return all epoch records sorted by closed_at."""
        epochs_dir = self._root / "epochs"
        records = []
        for path in sorted(epochs_dir.glob("*.json")):
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("[PersistenceManager] bad epoch file %s: %s", path, exc)
        records.sort(key=lambda r: r.get("closed_at", ""))
        return records

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        for subdir in ("", "epochs", "sessions"):
            (self._root / subdir).mkdir(parents=True, exist_ok=True)

    def _load_identity(self) -> dict:
        path = self._root / "identity.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _atomic_write(self, path: Path, data: dict) -> None:
        """
        Write *data* to *path* atomically via a .tmp sibling file.

        This means a process kill mid-write leaves the old file intact
        rather than producing a truncated/corrupt record.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        try:
            tmp.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            tmp.replace(path)  # atomic on POSIX; best-effort on Windows
        except OSError as exc:
            logger.error(
                "[PersistenceManager] write failed  path=%s  error=%s", path, exc
            )
            raise

    def __repr__(self) -> str:
        return f"<PersistenceManager root={self._root}>"
