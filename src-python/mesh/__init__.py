"""
mesh — GAIAN Mesh Network Router

Provides the GAIAN peer-to-peer mesh network layer, enabling sovereign
GAIAN nodes to communicate over LoRa, Wi-Fi, and IP backbones without
centralised routing.

Architecture reference:
  - NEXUS_UNIVERSAL_OS.md Domain 1.5 — Mesh Layer
  - GAIAN_LAWS.md Law IV — Mesh Sovereignty
HAL dependency: DeviceCapability.MESH_RADIO
"""
from __future__ import annotations

from mesh.router import mesh_router, init_mesh_router

__all__ = ["mesh_router", "init_mesh_router"]
