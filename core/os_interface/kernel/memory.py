"""
GAIA Kernel Memory Manager.

Tracks physical and virtual memory regions, ownership, protection flags,
and mapping state. Provides the interface for the kernel to allocate,
map, and release pages.

Prior art:
  seL4  — capability-based memory management, untyped memory objects,
           no kernel-managed heap (all memory explicitly delegated)
  XNU   — Mach VM, vm_map, named memory entries, copy-on-write
  Linux — page allocator, slab/slub, VMA tracking per process

GAIA adds an INTELLIGENCE region kind: memory permanently reserved for
the AI runtime heap, never swappable, pinned at boot.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from typing import Dict, List, Optional


class MemoryRegionKind(str, Enum):
    FIRMWARE = "firmware"
    KERNEL = "kernel"
    KERNEL_STACK = "kernel_stack"
    USER = "user"
    DRIVER = "driver"
    DEVICE_MMIO = "device_mmio"
    FRAMEBUFFER = "framebuffer"
    ACPI = "acpi"
    PERSISTENT = "persistent"
    INTELLIGENCE = "intelligence"  # AI runtime heap — pinned, never swapped
    FREE = "free"
    RESERVED = "reserved"


class MemoryProtection(Flag):
    NONE = 0
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    READ_WRITE = READ | WRITE
    READ_EXECUTE = READ | EXECUTE


@dataclass
class MemoryRegion:
    start_addr: int
    size_bytes: int
    kind: MemoryRegionKind = MemoryRegionKind.FREE
    protection: MemoryProtection = MemoryProtection.READ_WRITE
    owner_pid: str = ""
    mapped: bool = False
    pinned: bool = False
    numa_node: int = 0

    @property
    def end_addr(self) -> int:
        return self.start_addr + self.size_bytes

    @property
    def size_pages(self, page_size: int = 4096) -> int:
        return (self.size_bytes + page_size - 1) // page_size

    def overlaps(self, other: "MemoryRegion") -> bool:
        return self.start_addr < other.end_addr and other.start_addr < self.end_addr


@dataclass
class MemoryMap:
    total_bytes: int = 0
    regions: List[MemoryRegion] = field(default_factory=list)

    def add_region(self, region: MemoryRegion) -> None:
        self.regions.append(region)
        self.regions.sort(key=lambda r: r.start_addr)

    def free_regions(self) -> List[MemoryRegion]:
        return [r for r in self.regions if r.kind == MemoryRegionKind.FREE]

    def used_bytes(self) -> int:
        return sum(r.size_bytes for r in self.regions if r.kind != MemoryRegionKind.FREE)

    def free_bytes(self) -> int:
        return sum(r.size_bytes for r in self.free_regions())

    def find_for_pid(self, pid: str) -> List[MemoryRegion]:
        return [r for r in self.regions if r.owner_pid == pid]

    def find_by_kind(self, kind: MemoryRegionKind) -> List[MemoryRegion]:
        return [r for r in self.regions if r.kind == kind]

    def allocate(
        self,
        size_bytes: int,
        kind: MemoryRegionKind = MemoryRegionKind.USER,
        owner_pid: str = "",
        protection: MemoryProtection = MemoryProtection.READ_WRITE,
    ) -> Optional[MemoryRegion]:
        for region in self.free_regions():
            if region.size_bytes >= size_bytes:
                allocated = MemoryRegion(
                    start_addr=region.start_addr,
                    size_bytes=size_bytes,
                    kind=kind,
                    protection=protection,
                    owner_pid=owner_pid,
                    mapped=True,
                )
                remainder_size = region.size_bytes - size_bytes
                self.regions.remove(region)
                self.regions.append(allocated)
                if remainder_size > 0:
                    self.regions.append(MemoryRegion(
                        start_addr=region.start_addr + size_bytes,
                        size_bytes=remainder_size,
                        kind=MemoryRegionKind.FREE,
                    ))
                self.regions.sort(key=lambda r: r.start_addr)
                return allocated
        return None

    def release(self, start_addr: int) -> bool:
        for region in self.regions:
            if region.start_addr == start_addr and region.kind != MemoryRegionKind.FREE:
                region.kind = MemoryRegionKind.FREE
                region.owner_pid = ""
                region.mapped = False
                return True
        return False

    def summary(self) -> Dict[str, int]:
        return {
            "total_bytes": self.total_bytes,
            "used_bytes": self.used_bytes(),
            "free_bytes": self.free_bytes(),
            "region_count": len(self.regions),
        }
