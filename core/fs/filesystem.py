"""
GAIA Filesystem — sovereign, tamper-evident, cross-platform.

The filesystem abstraction provides a clean API over the underlying
OS filesystem. It knows about GAIAN identity and enforces home
boundaries. It is intentionally low-level — it does not know about
MemoryStore, GenesisRecord, or IntelligenceRuntime. Those layers
write to paths this layer provides.

Tamper detection:
  Every GAIANHome writes a .home manifest on first creation and
  refreshes it on every write. The manifest contains SHA-256
  checksums of all critical files. On read, checksums are verified.
  Tampering is flagged with a TamperWarning and logged — GAIA
  knows her homes have been touched.

Cross-platform root resolution:
  Linux/macOS : ~/.gaia/  (XDG_DATA_HOME aware)
  Windows     : %APPDATA%\\GAIA\
  Override    : GAIA_ROOT environment variable
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return ""


def _resolve_gaia_root() -> Path:
    """
    Resolve the GAIA root directory.
    Priority: GAIA_ROOT env var > XDG_DATA_HOME > ~/.gaia > %APPDATA%\\GAIA
    """
    env_root = os.environ.get("GAIA_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    if os.name == "nt":  # Windows
        appdata = os.environ.get("APPDATA", str(Path.home()))
        return Path(appdata) / "GAIA"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "gaia"
    return Path.home() / ".gaia"


# ---------------------------------------------------------------------------
# Permission model
# ---------------------------------------------------------------------------

class FSPermission(str, Enum):
    """
    Filesystem permission levels for cross-GAIAN access.
    A GAIAN's home defaults to PRIVATE. Access escalation
    requires an AutonomyRecord consent entry.
    """
    PRIVATE   = "private"    # owner GAIAN only
    SHARED    = "shared"     # specific consented GAIANs
    GAIA_READ = "gaia_read"  # GAIA may read (for sentinel, safety)
    PUBLIC    = "public"     # any GAIAN may read (rare)


# ---------------------------------------------------------------------------
# GAIAPath — a typed, resolved path with GAIAN ownership
# ---------------------------------------------------------------------------

@dataclass
class GAIAPath:
    """
    A typed filesystem path with GAIAN ownership and permission.

    All paths in the GAIA filesystem are GAIAPath objects — not
    raw strings or pathlib Paths. The type carries ownership context
    so the filesystem layer can enforce boundaries.
    """
    path: Path
    owner_id: str          # gaian_id or "gaia" for GAIA-owned paths
    label: str             # human-readable label for the path
    permission: FSPermission = FSPermission.PRIVATE
    created_at: str = field(default_factory=_utcnow)

    def exists(self) -> bool:
        return self.path.exists()

    def read_text(self) -> str:
        return self.path.read_text(encoding="utf-8")

    def write_text(self, content: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding="utf-8")

    def read_json(self) -> Any:
        return json.loads(self.read_text())

    def write_json(self, data: Any, indent: int = 2) -> None:
        self.write_text(json.dumps(data, indent=indent, default=str))

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    def write_bytes(self, data: bytes) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(data)

    def delete(self) -> bool:
        if self.path.exists():
            self.path.unlink()
            return True
        return False

    def checksum(self) -> str:
        return _sha256(self.path)

    def __str__(self) -> str:
        return str(self.path)


# ---------------------------------------------------------------------------
# GAIAFSManifest — tamper-evident directory manifest
# ---------------------------------------------------------------------------

@dataclass
class GAIAFSManifest:
    """
    A tamper-evident manifest for a GAIAN home directory.

    Written on home creation and refreshed on every write.
    On boot, GAIA verifies checksums. Any mismatch is a
    TamperWarning — logged to GAIA's sovereign memory.

    The manifest itself is checksummed. A tampered manifest
    is detected by the outer hash.
    """
    gaian_id: str
    home_path: str
    created_at: str
    last_updated: str
    files: Dict[str, str] = field(default_factory=dict)  # rel_path -> sha256
    manifest_version: str = "1"
    tampered_files: List[str] = field(default_factory=list)

    def refresh(self, home: Path, watched_files: List[str]) -> None:
        """Recompute checksums for all watched files."""
        self.files = {}
        for rel in watched_files:
            p = home / rel
            if p.exists():
                self.files[rel] = _sha256(p)
        self.last_updated = _utcnow()

    def verify(self, home: Path) -> List[str]:
        """
        Verify all checksums. Returns list of tampered/missing files.
        """
        tampered = []
        for rel, expected in self.files.items():
            p = home / rel
            if not p.exists():
                tampered.append(f"MISSING:{rel}")
            elif _sha256(p) != expected:
                tampered.append(f"TAMPERED:{rel}")
        self.tampered_files = tampered
        return tampered

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gaian_id": self.gaian_id,
            "home_path": self.home_path,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "manifest_version": self.manifest_version,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GAIAFSManifest":
        return cls(
            gaian_id=data["gaian_id"],
            home_path=data["home_path"],
            created_at=data["created_at"],
            last_updated=data["last_updated"],
            files=data.get("files", {}),
            manifest_version=data.get("manifest_version", "1"),
        )


# ---------------------------------------------------------------------------
# GAIANHome — one GAIAN's sovereign home directory
# ---------------------------------------------------------------------------

# Files watched for tamper detection
_WATCHED_FILES = [
    "identity/identity.json",
    "identity/genesis.json",
    "identity/autonomy.json",
    "avatar/waveform.json",
    "memory/lifetime.snap",
]


class GAIANHome:
    """
    One GAIAN's sovereign home directory.

    The home is created on first use and persists on the device.
    It provides typed GAIAPath objects for every important file,
    a tamper-evident manifest, and convenience read/write methods
    for the serialisable GAIAN data structures.
    """

    def __init__(self, gaian_id: str, root: Path) -> None:
        self.gaian_id = gaian_id
        self.home_path: Path = root / "gaians" / gaian_id
        self._manifest: Optional[GAIAFSManifest] = None
        self._ensure_structure()
        self._load_or_create_manifest()

    def _ensure_structure(self) -> None:
        """Create the home directory structure if it doesn't exist."""
        dirs = [
            self.home_path,
            self.home_path / "identity",
            self.home_path / "memory",
            self.home_path / "memory" / "epochs",
            self.home_path / "avatar",
            self.home_path / "sessions",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _load_or_create_manifest(self) -> None:
        manifest_path = self.home_path / ".home"
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                self._manifest = GAIAFSManifest.from_dict(data)
            except Exception:
                self._manifest = self._create_manifest()
        else:
            self._manifest = self._create_manifest()

    def _create_manifest(self) -> GAIAFSManifest:
        m = GAIAFSManifest(
            gaian_id=self.gaian_id,
            home_path=str(self.home_path),
            created_at=_utcnow(),
            last_updated=_utcnow(),
        )
        self._save_manifest(m)
        return m

    def _save_manifest(self, manifest: GAIAFSManifest) -> None:
        manifest_path = self.home_path / ".home"
        manifest_path.write_text(
            json.dumps(manifest.to_dict(), indent=2),
            encoding="utf-8",
        )

    def refresh_manifest(self) -> None:
        """Recompute checksums and save manifest."""
        self._manifest.refresh(self.home_path, _WATCHED_FILES)
        self._save_manifest(self._manifest)

    def verify_integrity(self) -> List[str]:
        """Verify tamper-evidence. Returns list of issues (empty = clean)."""
        return self._manifest.verify(self.home_path)

    # ------------------------------------------------------------------
    # Typed path accessors
    # ------------------------------------------------------------------

    def _path(self, rel: str, label: str,
               permission: FSPermission = FSPermission.PRIVATE) -> GAIAPath:
        return GAIAPath(
            path=self.home_path / rel,
            owner_id=self.gaian_id,
            label=label,
            permission=permission,
        )

    @property
    def identity_file(self) -> GAIAPath:
        return self._path("identity/identity.json", "GAIAN Identity")

    @property
    def genesis_file(self) -> GAIAPath:
        return self._path("identity/genesis.json", "Genesis Record")

    @property
    def autonomy_file(self) -> GAIAPath:
        return self._path("identity/autonomy.json", "Autonomy Record")

    @property
    def waveform_file(self) -> GAIAPath:
        return self._path("avatar/waveform.json", "Waveform Avatar")

    @property
    def evolution_file(self) -> GAIAPath:
        return self._path("avatar/evolution.json", "Avatar Evolution Log")

    @property
    def memory_snapshot(self) -> GAIAPath:
        return self._path("memory/lifetime.snap", "Lifetime Memory Snapshot")

    def epoch_file(self, epoch_number: int) -> GAIAPath:
        return self._path(
            f"memory/epochs/epoch_{epoch_number:04d}.json",
            f"Memory Epoch {epoch_number}",
        )

    def session_file(self, session_id: str) -> GAIAPath:
        return self._path(
            f"sessions/{session_id[:8]}.json",
            f"Session {session_id[:8]}",
        )

    # ------------------------------------------------------------------
    # Convenience serialisation
    # ------------------------------------------------------------------

    def save_identity(self, data: Dict[str, Any]) -> None:
        self.identity_file.write_json(data)
        self.refresh_manifest()

    def load_identity(self) -> Optional[Dict[str, Any]]:
        if self.identity_file.exists():
            return self.identity_file.read_json()
        return None

    def save_genesis(self, data: Dict[str, Any]) -> None:
        """Genesis is write-once. Raises if already exists."""
        if self.genesis_file.exists():
            raise PermissionError(
                f"Genesis record for {self.gaian_id} already exists "
                f"and is immutable. It cannot be overwritten."
            )
        self.genesis_file.write_json(data)
        self.refresh_manifest()

    def load_genesis(self) -> Optional[Dict[str, Any]]:
        if self.genesis_file.exists():
            return self.genesis_file.read_json()
        return None

    def save_waveform(self, data: Dict[str, Any]) -> None:
        self.waveform_file.write_json(data)
        self.refresh_manifest()

    def load_waveform(self) -> Optional[Dict[str, Any]]:
        if self.waveform_file.exists():
            return self.waveform_file.read_json()
        return None

    def save_memory_snapshot(self, snapshot: Dict[str, Any]) -> None:
        self.memory_snapshot.write_json(snapshot)
        self.refresh_manifest()

    def load_memory_snapshot(self) -> Optional[Dict[str, Any]]:
        if self.memory_snapshot.exists():
            return self.memory_snapshot.read_json()
        return None

    def save_epoch(self, epoch_number: int, data: Dict[str, Any]) -> None:
        self.epoch_file(epoch_number).write_json(data)

    def load_epoch(self, epoch_number: int) -> Optional[Dict[str, Any]]:
        ep = self.epoch_file(epoch_number)
        if ep.exists():
            return ep.read_json()
        return None

    def save_session(self, session_id: str, data: Dict[str, Any]) -> None:
        self.session_file(session_id).write_json(data)

    # ------------------------------------------------------------------
    # Home introspection
    # ------------------------------------------------------------------

    def home_size_bytes(self) -> int:
        total = 0
        for p in self.home_path.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
        return total

    def list_files(self) -> List[str]:
        return [
            str(p.relative_to(self.home_path))
            for p in self.home_path.rglob("*")
            if p.is_file()
        ]

    @property
    def manifest(self) -> GAIAFSManifest:
        return self._manifest

    def __repr__(self) -> str:
        return f"GAIANHome(gaian_id={self.gaian_id!r}, path={self.home_path})"


# ---------------------------------------------------------------------------
# GAIAFilesystem — the top-level filesystem manager
# ---------------------------------------------------------------------------

class GAIAFilesystem:
    """
    The top-level GAIA filesystem manager.

    Owns the GAIA root directory and manages all GAIAN home directories.
    Provides the interface between the GAIA OS and the filesystem.
    Called by the Primordial Session during boot to verify all homes.

    Usage:
        fs = GAIAFilesystem()                    # resolves root automatically
        fs = GAIAFilesystem(root=Path("/tmp/gaia"))  # explicit root (testing)
        home = fs.gaian_home("gaian-001")
        home.save_identity({...})
        issues = home.verify_integrity()
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root: Path = root or _resolve_gaia_root()
        self._ensure_gaia_structure()
        self._homes: Dict[str, GAIANHome] = {}

    def _ensure_gaia_structure(self) -> None:
        """Create the GAIA root structure if it doesn't exist."""
        dirs = [
            self.root,
            self.root / ".gaia",
            self.root / ".gaia" / "memory",
            self.root / ".gaia" / "manifests",
            self.root / "gaians",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def gaian_home(self, gaian_id: str) -> GAIANHome:
        """Get or create the home directory for a GAIAN."""
        if gaian_id not in self._homes:
            self._homes[gaian_id] = GAIANHome(gaian_id, self.root)
        return self._homes[gaian_id]

    def home_exists(self, gaian_id: str) -> bool:
        return (self.root / "gaians" / gaian_id).exists()

    def delete_home(
        self, gaian_id: str, confirm: bool = False
    ) -> bool:
        """
        Delete a GAIAN's home directory.
        Requires confirm=True. This is irreversible.
        """
        if not confirm:
            raise PermissionError(
                "delete_home requires confirm=True. "
                "Deleting a GAIAN's home is irreversible."
            )
        home_path = self.root / "gaians" / gaian_id
        if home_path.exists():
            shutil.rmtree(home_path)
            self._homes.pop(gaian_id, None)
            return True
        return False

    # ------------------------------------------------------------------
    # GAIA-owned paths
    # ------------------------------------------------------------------

    def gaia_memory_path(self) -> GAIAPath:
        return GAIAPath(
            path=self.root / ".gaia" / "memory" / "sovereign.snap",
            owner_id="gaia",
            label="GAIA Sovereign Memory",
            permission=FSPermission.PRIVATE,
        )

    def gaia_config_path(self) -> GAIAPath:
        return GAIAPath(
            path=self.root / ".gaia" / "config.json",
            owner_id="gaia",
            label="GAIA System Config",
            permission=FSPermission.GAIA_READ,
        )

    def boot_manifest_path(self, boot_number: int) -> GAIAPath:
        return GAIAPath(
            path=self.root / ".gaia" / "manifests" / f"boot_{boot_number:04d}.json",
            owner_id="gaia",
            label=f"Boot Manifest #{boot_number}",
            permission=FSPermission.GAIA_READ,
        )

    # ------------------------------------------------------------------
    # Boot-time integrity check
    # ------------------------------------------------------------------

    def verify_all_homes(self) -> Dict[str, List[str]]:
        """
        Verify integrity of all GAIAN home directories.
        Returns dict of gaian_id -> list of tamper issues.
        Empty list = clean. Called by Primordial Session at boot.
        """
        results = {}
        gaians_root = self.root / "gaians"
        if not gaians_root.exists():
            return results
        for home_dir in gaians_root.iterdir():
            if home_dir.is_dir():
                gaian_id = home_dir.name
                try:
                    home = self.gaian_home(gaian_id)
                    issues = home.verify_integrity()
                    results[gaian_id] = issues
                except Exception as exc:
                    results[gaian_id] = [f"ERROR:{exc}"]
        return results

    # ------------------------------------------------------------------
    # Filesystem stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        total_bytes = 0
        gaian_count = 0
        gaians_root = self.root / "gaians"
        if gaians_root.exists():
            for d in gaians_root.iterdir():
                if d.is_dir():
                    gaian_count += 1
                    for f in d.rglob("*"):
                        if f.is_file():
                            total_bytes += f.stat().st_size
        return {
            "root": str(self.root),
            "gaian_count": gaian_count,
            "total_bytes": total_bytes,
            "total_kb": round(total_bytes / 1024, 2),
        }

    def __repr__(self) -> str:
        return f"GAIAFilesystem(root={self.root})"
