"""
GAIA OS Interface — the universal OS layer.

This package defines the GAIA Operating System surface:
- System settings subsystems
- Release channel management
- Hardware abstraction interfaces
- OS-level connector bridges
"""
from core.os_interface.settings import SystemSettings
from core.os_interface.release_channel import ReleaseChannel, ReleaseChannelManager

__all__ = [
    "SystemSettings",
    "ReleaseChannel",
    "ReleaseChannelManager",
]
