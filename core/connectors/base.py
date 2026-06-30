"""Abstract base class every GAIA connector must implement."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.connectors.model import ConnectorEvent, ConnectorManifest, ConnectorStatus


class BaseConnector(ABC):
    def __init__(self, manifest: ConnectorManifest) -> None:
        self.manifest = manifest
        self._status: ConnectorStatus = ConnectorStatus.REGISTERED

    @property
    def connector_id(self) -> str:
        return self.manifest.connector_id

    @property
    def status(self) -> ConnectorStatus:
        return self._status

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """Establish connection. Return True on success."""

    @abstractmethod
    def disconnect(self) -> None:
        """Gracefully tear down the connection."""

    @abstractmethod
    def health_check(self) -> ConnectorStatus:
        """Return current health status."""

    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """Dispatch a named action with params and return its result."""

    def emit_event(self, event_type: str, payload: Dict[str, Any]) -> ConnectorEvent:
        event = ConnectorEvent(
            connector_id=self.connector_id,
            event_type=event_type,
            payload=payload,
            source=self.manifest.name,
        )
        return event

    def list_capabilities(self) -> List[str]:
        return list(self.manifest.capabilities)

    def supports(self, capability: str) -> bool:
        return capability in self.manifest.capabilities
