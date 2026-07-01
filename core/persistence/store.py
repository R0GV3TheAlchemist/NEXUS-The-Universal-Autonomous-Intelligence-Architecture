"""
PersistenceStore — atomic JSON file I/O.

All persistence in GAIA OS is built on two primitives:
  write(path, data) — atomically write a JSON-serialisable dict
  read(path)        — read and parse a JSON file, return None if missing

Atomicity guarantee:
  write() always writes to <path>.tmp, then os.replace() to <path>.
  os.replace() is atomic on POSIX and atomic-enough on Windows (Vista+).
  A crash at any point leaves either the old file intact or the new
  file fully written — never a partial write.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class PersistenceStore:
    """
    Thin atomic JSON file I/O layer.

    All paths are relative to `root`. The store creates
    subdirectories as needed.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core primitives
    # ------------------------------------------------------------------

    def write(self, rel_path: str, data: Dict[str, Any]) -> Path:
        """
        Atomically write `data` as JSON to `root / rel_path`.
        Creates parent directories as needed.
        Returns the absolute path written.
        """
        target = self.root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        payload = json.dumps(data, indent=2, default=self._serialise)
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, target)
        return target

    def read(self, rel_path: str) -> Optional[Dict[str, Any]]:
        """
        Read and parse the JSON file at `root / rel_path`.
        Returns None if the file does not exist or is malformed.
        """
        target = self.root / rel_path
        if not target.exists():
            return None
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def exists(self, rel_path: str) -> bool:
        return (self.root / rel_path).exists()

    def delete(self, rel_path: str) -> None:
        target = self.root / rel_path
        if target.exists():
            target.unlink()

    def list_dir(self, rel_dir: str) -> list[str]:
        """List filenames (not paths) in a subdirectory."""
        d = self.root / rel_dir
        if not d.is_dir():
            return []
        return [p.name for p in sorted(d.iterdir()) if p.is_file()]

    def list_subdirs(self, rel_dir: str) -> list[str]:
        """List immediate subdirectory names under rel_dir."""
        d = self.root / rel_dir
        if not d.is_dir():
            return []
        return [p.name for p in sorted(d.iterdir()) if p.is_dir()]

    # ------------------------------------------------------------------
    # JSON serialisation helper
    # ------------------------------------------------------------------

    @staticmethod
    def _serialise(obj: Any) -> Any:
        """Fallback serialiser for types json.dumps doesn\'t handle."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        if hasattr(obj, "value"):          # Enum
            return obj.value
        return str(obj)
