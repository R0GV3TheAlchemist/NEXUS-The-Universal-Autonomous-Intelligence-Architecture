"""Connector lifecycle manager — connect, disconnect, health-poll, dispatch."""
from __future__ import annotations

from typing import Any, Dict, List

from core.connectors.base import BaseConnector
from core.connectors.model import ConnectorKind, ConnectorStatus
from core.connectors.registry import ConnectorRegistry


class ConnectorManager:
    def __init__(self, registry: ConnectorRegistry) -> None:
        self.registry = registry

    def register(self, connector: BaseConnector) -> None:
        self.registry.register(connector)

    def connect(self, connector_id: str, config: Dict[str, Any]) -> bool:
        connector = self.registry.require(connector_id)
        success = connector.connect(config)
        connector._status = ConnectorStatus.CONNECTED if success else ConnectorStatus.ERROR
        return success

    def disconnect(self, connector_id: str) -> None:
        connector = self.registry.require(connector_id)
        connector.disconnect()
        connector._status = ConnectorStatus.DISCONNECTED

    def health_check_all(self) -> Dict[str, ConnectorStatus]:
        results: Dict[str, ConnectorStatus] = {}
        for connector in self.registry.list_all():
            status = connector.health_check()
            connector._status = status
            results[connector.connector_id] = status
        return results

    def execute(self, connector_id: str, action: str, params: Dict[str, Any]) -> Any:
        connector = self.registry.require(connector_id)
        if connector.status not in (ConnectorStatus.CONNECTED, ConnectorStatus.DEGRADED):
            raise RuntimeError(
                f"Connector '{connector_id}' is {connector.status.value}, cannot execute."
            )
        return connector.execute(action, params)

    def list_by_kind(self, kind: ConnectorKind) -> List[BaseConnector]:
        return self.registry.list_by_kind(kind)

    def find_by_capability(self, capability: str) -> List[BaseConnector]:
        return self.registry.find_by_capability(capability)

    def connected_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "connector_id": c.connector_id,
                "name": c.manifest.name,
                "kind": c.manifest.kind.value,
                "status": c.status.value,
                "capabilities": c.list_capabilities(),
            }
            for c in self.registry.list_connected()
        ]
