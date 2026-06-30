from __future__ import annotations

from typing import Any, Dict

import pytest

from core.connectors.base import BaseConnector
from core.connectors.manager import ConnectorManager
from core.connectors.model import ConnectorKind, ConnectorManifest, ConnectorStatus
from core.connectors.registry import ConnectorRegistry


class FakeConnector(BaseConnector):
    def __init__(self, kind: ConnectorKind = ConnectorKind.CUSTOM, capabilities=None):
        manifest = ConnectorManifest(
            name="fake",
            kind=kind,
            capabilities=capabilities or ["read", "write"],
        )
        super().__init__(manifest)
        self._connected = False

    def connect(self, config: Dict[str, Any]) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def health_check(self) -> ConnectorStatus:
        return ConnectorStatus.CONNECTED if self._connected else ConnectorStatus.DISCONNECTED

    def execute(self, action: str, params: Dict[str, Any]) -> Any:
        return {"action": action, "params": params}


class TestConnectorFlow:
    def test_register_and_get(self):
        reg = ConnectorRegistry()
        c = FakeConnector()
        reg.register(c)
        assert reg.get(c.connector_id) is c

    def test_connect_sets_status(self):
        reg = ConnectorRegistry()
        mgr = ConnectorManager(reg)
        c = FakeConnector()
        reg.register(c)
        mgr.connect(c.connector_id, {})
        assert c.status == ConnectorStatus.CONNECTED

    def test_disconnect_sets_status(self):
        reg = ConnectorRegistry()
        mgr = ConnectorManager(reg)
        c = FakeConnector()
        reg.register(c)
        mgr.connect(c.connector_id, {})
        mgr.disconnect(c.connector_id)
        assert c.status == ConnectorStatus.DISCONNECTED

    def test_execute_dispatches_action(self):
        reg = ConnectorRegistry()
        mgr = ConnectorManager(reg)
        c = FakeConnector()
        reg.register(c)
        mgr.connect(c.connector_id, {})
        result = mgr.execute(c.connector_id, "ping", {"msg": "hi"})
        assert result["action"] == "ping"

    def test_execute_raises_if_not_connected(self):
        reg = ConnectorRegistry()
        mgr = ConnectorManager(reg)
        c = FakeConnector()
        reg.register(c)
        with pytest.raises(RuntimeError):
            mgr.execute(c.connector_id, "ping", {})

    def test_list_by_kind(self):
        reg = ConnectorRegistry()
        mgr = ConnectorManager(reg)
        c1 = FakeConnector(kind=ConnectorKind.CALENDAR)
        c2 = FakeConnector(kind=ConnectorKind.CALENDAR)
        c3 = FakeConnector(kind=ConnectorKind.NETWORK)
        reg.register(c1); reg.register(c2); reg.register(c3)
        assert len(mgr.list_by_kind(ConnectorKind.CALENDAR)) == 2

    def test_find_by_capability(self):
        reg = ConnectorRegistry()
        mgr = ConnectorManager(reg)
        c1 = FakeConnector(capabilities=["bluetooth", "pair"])
        c2 = FakeConnector(capabilities=["read"])
        reg.register(c1); reg.register(c2)
        results = mgr.find_by_capability("bluetooth")
        assert len(results) == 1

    def test_health_check_all(self):
        reg = ConnectorRegistry()
        mgr = ConnectorManager(reg)
        c = FakeConnector()
        reg.register(c)
        mgr.connect(c.connector_id, {})
        statuses = mgr.health_check_all()
        assert statuses[c.connector_id] == ConnectorStatus.CONNECTED

    def test_emit_event(self):
        c = FakeConnector()
        event = c.emit_event("data_received", {"bytes": 128})
        assert event.event_type == "data_received"
        assert event.connector_id == c.connector_id

    def test_unregister(self):
        reg = ConnectorRegistry()
        c = FakeConnector()
        reg.register(c)
        reg.unregister(c.connector_id)
        assert c.connector_id not in reg

    def test_connected_summary(self):
        reg = ConnectorRegistry()
        mgr = ConnectorManager(reg)
        c = FakeConnector(kind=ConnectorKind.BLUETOOTH)
        reg.register(c)
        mgr.connect(c.connector_id, {})
        summary = mgr.connected_summary()
        assert summary[0]["kind"] == "bluetooth"
