"""
GAIA Connectors — the universal integration layer.

Connectors bridge GAIA to the external world: calendars, communications,
IoT devices, data streams, cloud services, operating system interfaces,
hardware buses, and cross-platform OS integration.

Each connector is a typed adapter that follows the BaseConnector contract.
Connectors register with the ConnectorRegistry so the Agentic Loop and
Workflow engine can discover and invoke them by capability.
"""
from core.connectors.model import (
    ConnectorKind,
    ConnectorStatus,
    ConnectorManifest,
    ConnectorEvent,
)
from core.connectors.registry import ConnectorRegistry
from core.connectors.base import BaseConnector
from core.connectors.manager import ConnectorManager

__all__ = [
    "ConnectorKind",
    "ConnectorStatus",
    "ConnectorManifest",
    "ConnectorEvent",
    "ConnectorRegistry",
    "BaseConnector",
    "ConnectorManager",
]
