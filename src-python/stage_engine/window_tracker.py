"""
stage_engine.window_tracker — Sliding Window Stage History Tracker

Maintains a fixed-size circular buffer of StageState snapshots, enabling
time-windowed analysis of stage progression trends.

Reference: NEXUS_UNIVERSAL_OS.md Domain 2.8
"""
from __future__ import annotations

import logging
from collections import deque
from typing import Deque
from stage_engine.engine import StageState

logger = logging.getLogger("stage_engine.window_tracker")


class WindowTracker:
    """Fixed-size circular buffer of StageState snapshots.

    Args:
        window_size: Maximum number of snapshots retained.
    Reference: NEXUS_UNIVERSAL_OS.md Domain 2.8.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window: Deque[StageState] = deque(maxlen=window_size)
        self.window_size = window_size
        logger.info("WindowTracker initialised (window_size=%d)", window_size)

    def record(self, state: StageState) -> None:
        """Record a StageState snapshot to the window."""
        self._window.append(state)

    def snapshots(self) -> list[StageState]:
        """Return the current window as a list (oldest first)."""
        return list(self._window)

    def trend(self) -> float:
        """Return the mean progress value over the current window.

        Returns 0.0 if the window is empty.
        """
        if not self._window:
            return 0.0
        return sum(s.progress for s in self._window) / len(self._window)

    def __len__(self) -> int:
        return len(self._window)
