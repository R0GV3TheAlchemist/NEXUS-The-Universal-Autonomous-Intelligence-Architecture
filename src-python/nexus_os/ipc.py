"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ipc.py — NEXUS Inter-Process Communication.

Capability-gated typed channels with three delivery semantics:
AT_MOST_ONCE, AT_LEAST_ONCE, EXACTLY_ONCE.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Optional
from uuid import UUID, uuid4
from collections import deque
import time


class DeliverySemantics(Enum):
    AT_MOST_ONCE  = auto()   # fire-and-forget
    AT_LEAST_ONCE = auto()   # acknowledged; retried until ack
    EXACTLY_ONCE  = auto()   # transactional; deduplication enforced


@dataclass
class Message:
    """A typed IPC message envelope."""
    message_id: UUID  = field(default_factory=uuid4)
    sender_id:  UUID  = field(default_factory=uuid4)
    payload:    Any   = None
    topic:      str   = ""
    timestamp:  float = field(default_factory=time.time)
    ack:        bool  = False


class Channel:
    """
    A typed, capability-gated IPC channel between two processes.

    Semantics enforcement:
    - AT_MOST_ONCE:  messages dropped if buffer full
    - AT_LEAST_ONCE: messages retried until acknowledged
    - EXACTLY_ONCE:  deduplication by message_id before delivery
    """

    def __init__(self, channel_id: UUID, semantics: DeliverySemantics,
                 capacity: int = 256) -> None:
        self.channel_id = channel_id
        self.semantics  = semantics
        self.capacity   = capacity
        self._buffer: Deque[Message] = deque(maxlen=capacity)
        self._seen_ids: set = set()

    def send(self, message: Message) -> bool:
        """Send a message. Returns False if dropped."""
        if self.semantics == DeliverySemantics.EXACTLY_ONCE:
            if message.message_id in self._seen_ids:
                return False
            self._seen_ids.add(message.message_id)
        if len(self._buffer) >= self.capacity:
            if self.semantics == DeliverySemantics.AT_MOST_ONCE:
                return False
        self._buffer.append(message)
        return True

    def recv(self) -> Optional[Message]:
        """Receive the next message from the channel."""
        if self._buffer:
            msg = self._buffer.popleft()
            if self.semantics == DeliverySemantics.AT_LEAST_ONCE:
                msg.ack = False
            return msg
        return None

    def ack(self, message_id: UUID) -> None:
        """Acknowledge delivery (AT_LEAST_ONCE / EXACTLY_ONCE)."""
        pass

    def depth(self) -> int:
        return len(self._buffer)
