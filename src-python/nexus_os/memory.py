"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

memory.py — NEXUS Capability-Based Memory Manager.

MemoryBroker issues MemoryRegion grants tied to CapabilityTokens.
No process accesses memory outside its granted regions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class MemoryRegion:
    """A contiguous memory region with permission bits."""
    region_id:    UUID = field(default_factory=uuid4)
    base_address: int  = 0
    size_bytes:   int  = 0
    owner_id:     UUID = field(default_factory=uuid4)
    readable:     bool = True
    writable:     bool = False
    executable:   bool = False
    delegatable:  bool = False

    @property
    def end_address(self) -> int:
        return self.base_address + self.size_bytes

    def contains(self, address: int) -> bool:
        return self.base_address <= address < self.end_address


class MemoryBroker:
    """
    Issues and tracks MemoryRegion grants for all NEXUS processes.

    Enforces that no process reads, writes, or executes outside its
    granted regions. Supports delegation to child processes.
    """

    def __init__(self, total_bytes: int = 2 ** 40) -> None:  # default 1 TB
        self.total_bytes = total_bytes
        self._regions: Dict[UUID, MemoryRegion] = {}
        self._allocator_cursor: int = 0

    def allocate(self, owner_id: UUID, size_bytes: int,
                 readable: bool = True, writable: bool = True,
                 executable: bool = False) -> MemoryRegion:
        """Allocate a new region and bind it to owner_id."""
        if self._allocator_cursor + size_bytes > self.total_bytes:
            raise MemoryError("NEXUS memory broker: out of address space")
        region = MemoryRegion(
            base_address=self._allocator_cursor,
            size_bytes=size_bytes,
            owner_id=owner_id,
            readable=readable,
            writable=writable,
            executable=executable,
        )
        self._regions[region.region_id] = region
        self._allocator_cursor += size_bytes
        return region

    def free(self, region_id: UUID) -> None:
        self._regions.pop(region_id, None)

    def get_regions(self, owner_id: UUID) -> List[MemoryRegion]:
        return [r for r in self._regions.values() if r.owner_id == owner_id]

    def check_access(self, owner_id: UUID, address: int,
                     write: bool = False) -> bool:
        """Return True if owner_id has appropriate access to address."""
        for region in self.get_regions(owner_id):
            if region.contains(address):
                return region.writable if write else region.readable
        return False

    def delegate(self, region_id: UUID, new_owner_id: UUID) -> Optional[MemoryRegion]:
        """Delegate a delegatable region to a child process."""
        region = self._regions.get(region_id)
        if region and region.delegatable:
            child = MemoryRegion(
                base_address=region.base_address,
                size_bytes=region.size_bytes,
                owner_id=new_owner_id,
                readable=region.readable,
                writable=region.writable,
                executable=region.executable,
                delegatable=False,
            )
            self._regions[child.region_id] = child
            return child
        return None
