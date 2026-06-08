"""
core/routers/room.py

Home Twin room persistence endpoints:
  POST /room/save       — save panorama data URL
  GET  /room/load       — load panorama data URL
  POST /room/placement  — save GAIA placement
  GET  /room/placement  — load GAIA placement

Data is stored in ~/.local/share/GAIA/ (XDG-aware).
Panoramas are stored as JPEG files (decoded from data URL) to keep
memory.json clean and enable future streaming.

Canon Ref: C20 (Home Twin — Spatial Presence)
"""

from __future__ import annotations

import base64
import json
import os
import pathlib
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/room", tags=["room"])


# ---------------------------------------------------------------------------
# Storage paths
# ---------------------------------------------------------------------------

def _gaia_data_dir() -> pathlib.Path:
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home() / "AppData" / "Roaming"))
    else:
        base = pathlib.Path(os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local" / "share"))
    d = base / "GAIA"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class SaveRoomRequest(BaseModel):
    panorama: Optional[str] = None   # data URL or null to clear
    captured_at: Optional[str] = None


class PlacementRequest(BaseModel):
    surfaceId: Optional[str] = None
    surfaceLabel: Optional[str] = None
    yPercent: Optional[float] = None
    placedAt: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/save")
def room_save(req: SaveRoomRequest):
    """Persist room panorama. Accepts a data URL; stores as room.jpg."""
    data_dir = _gaia_data_dir()
    meta_path = data_dir / "room_meta.json"
    img_path  = data_dir / "room.jpg"

    if not req.panorama:
        # Clear
        img_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)
        return {"status": "cleared"}

    # Decode data URL → JPEG bytes
    try:
        header, b64 = req.panorama.split(",", 1)
        img_bytes = base64.b64decode(b64)
        img_path.write_bytes(img_bytes)
    except Exception:
        # If it's not a data URL, store raw (shouldn't happen)
        img_path.write_text(req.panorama, encoding="utf-8")

    # Write metadata
    meta = {"captured_at": req.captured_at or "", "img_path": str(img_path)}
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    return {"status": "saved", "size_bytes": img_path.stat().st_size}


@router.get("/load")
def room_load():
    """Load room panorama as a data URL."""
    data_dir  = _gaia_data_dir()
    img_path  = data_dir / "room.jpg"
    meta_path = data_dir / "room_meta.json"

    if not img_path.exists():
        return {"panorama": None, "captured_at": None}

    captured_at = ""
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            captured_at = meta.get("captured_at", "")
        except Exception:
            pass

    img_bytes = img_path.read_bytes()
    b64 = base64.b64encode(img_bytes).decode("ascii")
    data_url = f"data:image/jpeg;base64,{b64}"

    return {"panorama": data_url, "captured_at": captured_at}


@router.post("/placement")
def placement_save(req: PlacementRequest):
    """Persist GAIA placement on a detected surface."""
    data_dir = _gaia_data_dir()
    path = data_dir / "room_placement.json"
    path.write_text(json.dumps(req.dict()), encoding="utf-8")
    return {"status": "saved"}


@router.get("/placement")
def placement_load():
    """Load persisted GAIA placement."""
    path = (_gaia_data_dir() / "room_placement.json")
    if not path.exists():
        return {"surface_id": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"surface_id": None}
