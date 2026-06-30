"""Central registry for all GAIA connectors."""
from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Set

from core.connectors.base import BaseConnector
from core.connectors.model import ConnectorKind, ConnectorStatus


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: Dict[str, BaseConnector] = {}
        self._by_kind: DefaultDict[ConnectorKind, Set[str]] = defaultdict(set)

    def register(self, connector: BaseConnector) -> None:
        cid = connector.connector_id
        self._connectors[cid] = connector
        self._by_kind[connector.manifest.kind].add(cid)

    def unregister(self, connector_id: str) -> None:
        connector = self._connectors.pop(connector_id, None)
        if connector:
            self._by_kind[connector.manifest.kind].discard(connector_id)

    def get(self, connector_id: str) -> Optional[BaseConnector]:
        return self._connectors.get(connector_id)

    def require(self, connector_id: str) -> BaseConnector:
        c = self.get(connector_id)
        if c is None:
            raise KeyError(f"Connector '{connector_id}' not registered.")
        return c

    def list_by_kind(self, kind: ConnectorKind) -> List[BaseConnector]:
        return [self._connectors[cid] for cid in self._by_kind.get(kind, set())]

    def list_connected(self) -> List[BaseConnector]:
        return [c for c in self._connectors.values() if c.status == ConnectorStatus.CONNECTED]

    def list_all(self) -> List[BaseConnector]:
        return list(self._connectors.values())

    def find_by_capability(self, capability: str) -> List[BaseConnector]:
        return [c for c in self._connectors.values() if c.supports(capability)]

    def __len__(self) -> int:
        return len(self._connectors)

    def __contains__(self, connector_id: str) -> bool:
        return connector_id in self._connectors
