"""tests/test_timeservice.py

Test scaffold for src-python/timeservice

Covers: TimeService, TimeSyncConfig, TimeProvider, SyncProtocol
"""
import pytest
from datetime import timezone

from timeservice import TimeService, TimeSyncConfig, TimeProvider


class TestTimeProvider:

    def test_now_returns_utc(self):
        provider = TimeProvider()
        dt = provider.now()
        assert dt.tzinfo is not None
        assert dt.tzinfo == timezone.utc


class TestTimeService:

    def test_initialises_with_default_config(self):
        svc = TimeService()
        assert svc.config is not None
        assert svc.last_sync is None  # No sync yet

    def test_now_returns_datetime(self):
        from datetime import datetime
        svc = TimeService()
        dt = svc.now()
        assert isinstance(dt, datetime)

    def test_sync_raises_not_implemented(self):
        svc = TimeService()
        with pytest.raises(NotImplementedError):
            svc.sync()

    def test_custom_config(self):
        from timeservice.engine import SyncProtocol
        config = TimeSyncConfig(
            protocol=SyncProtocol.PTP,
            sync_interval=30.0,
            max_drift_ms=1.0,
        )
        svc = TimeService(config=config)
        assert svc.config.sync_interval == pytest.approx(30.0)
