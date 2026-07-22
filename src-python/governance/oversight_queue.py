"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

oversight_queue.py — NEXUS Human Oversight Queue.

Actions deferred by REQUIRE_REVIEW ethics constraints are placed here
for human review before execution is permitted or denied.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import time


class OversightDecision(Enum):
    PENDING  = auto()
    APPROVE  = auto()
    DENY     = auto()
    ESCALATE = auto()


@dataclass
class OversightItem:
    """A deferred action awaiting human review."""
    item_id:         UUID              = field(default_factory=uuid4)
    action_id:       UUID              = field(default_factory=uuid4)
    actor_id:        UUID              = field(default_factory=uuid4)
    action_type:     str               = ""
    payload:         Dict[str, Any]    = field(default_factory=dict)
    constraint_name: str               = ""
    reason:          str               = ""
    decision:        OversightDecision = OversightDecision.PENDING
    reviewer_id:     Optional[UUID]    = None
    submitted_at:    float             = field(default_factory=time.time)
    decided_at:      Optional[float]   = None
    notes:           str               = ""


class OversightQueue:
    """
    Human oversight queue for actions deferred by REQUIRE_REVIEW
    ethics constraints. Reviewers claim, decide, and log each item.
    """

    def __init__(self) -> None:
        self._items: Dict[UUID, OversightItem] = {}

    def enqueue(self, item: OversightItem) -> None:
        self._items[item.item_id] = item

    def claim(self, item_id: UUID, reviewer_id: UUID) -> OversightItem:
        item = self._get(item_id)
        item.reviewer_id = reviewer_id
        return item

    def decide(self, item_id: UUID, decision: OversightDecision,
               notes: str = "") -> OversightItem:
        item = self._get(item_id)
        if item.decision != OversightDecision.PENDING:
            raise ValueError(
                f"Item {item_id} already decided: {item.decision.name}")
        item.decision   = decision
        item.decided_at = time.time()
        item.notes      = notes
        return item

    def pending(self) -> List[OversightItem]:
        return [i for i in self._items.values()
                if i.decision == OversightDecision.PENDING]

    def decided(self) -> List[OversightItem]:
        return [i for i in self._items.values()
                if i.decision != OversightDecision.PENDING]

    def _get(self, item_id: UUID) -> OversightItem:
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"OversightItem not found: {item_id}")
        return item

    def __len__(self) -> int:
        return len(self._items)
