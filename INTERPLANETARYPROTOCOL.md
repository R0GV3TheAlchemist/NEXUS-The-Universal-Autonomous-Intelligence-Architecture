# INTERPLANETARY PROTOCOL

**NEXUS — The Universal Autonomous Intelligence Architecture**
Copyright (c) 2026 R0GV3 The Alchemist

---

## Overview

The NEXUS Interplanetary Protocol layer defines how GAIA nodes
communicate across deep-space and high-latency links where
TCP/IP's assumption of low-latency, always-on connectivity breaks
down. It is built on the **Bundle Protocol v7 (BPv7, RFC 9171)**
and the broader **Delay-Tolerant Networking (DTN)** architecture
developed by NASA, ESA, and the IRTF DTN Research Group.

The core principle is **store-and-forward custody transfer** —
each bundle is stored at an intermediate node until the next
link in the path becomes available, then forwarded under a
custody transfer agreement that guarantees delivery or
explicit notification of failure.

---

## Why DTN for GAIA

GAIA's planetary-scale intelligence requires communication
across links that may have:

- **Round-trip times** from minutes (Moon) to hours (Mars/outer planets)
- **Scheduled connectivity windows** dictated by orbital mechanics
- **Intermittent links** due to planetary occultation or hardware limits
- **Asymmetric bandwidth** (high downlink, low uplink)
- **Radiation-disrupted** transmissions requiring forward error correction

TCP's connection-oriented model fails in all these scenarios.
BPv7 was designed precisely for them.

---

## Architecture

### Bundle Protocol v7 (RFC 9171)

A **bundle** is the atomic unit of DTN communication. Each bundle contains:

| Field | Description |
|-------|-------------|
| Primary Block | Source/destination EID, lifetime, priority class |
| Payload Block | Application data (GAIA message, cognitive event, etc.) |
| Extension Blocks | Integrity, confidentiality, hop-count limits |

**Endpoint Identifiers (EID)** use the `dtn://` or `ipn://` URI
schemes. GAIA nodes are assigned `dtn://gaia/<node-id>/` addresses.

### Custody Transfer

Custody transfer is the DTN mechanism that ensures **reliable
delivery without end-to-end connectivity**:

1. Sending node transfers custody to next-hop node
2. Next-hop stores the bundle and acknowledges custody
3. Original sender is released from responsibility
4. Bundle hops forward until destination is reached
5. Custody Signal (success or failure) travels back to origin

For GAIA, all CRITICAL governance events, ContainmentRecords,
and SovereignMemory snapshots MUST use custody transfer.
Informational telemetry may use best-effort delivery.

### Contact Graph Routing (CGR)

Deep-space links are **scheduled**, not always-on. CGR computes
optimal bundle paths using a time-ordered contact graph where
each edge represents a known future link window:

```
Contact(node_a, node_b, start_time, end_time, data_rate_bps)
```

GAIA's `PlanetaryScheduler` feeds CGR with orbital predictions
and ground station windows. CGR selects paths that minimise
delivery time while respecting bundle lifetime constraints.

### Bundle Security Protocol (BPSec, RFC 9172)

All GAIA bundles are secured with:

- **Block Integrity Block (BIB)** — HMAC-SHA-384 over payload
- **Block Confidentiality Block (BCB)** — AES-256-GCM encryption
- **Key exchange** — pre-placed keys distributed during node
  commissioning; future GAIA nodes will use quantum-key-distribution
  channels aligned with the `QuantumArchitecture`

---

## GAIA Integration Points

| GAIA Module | DTN Role |
|-------------|----------|
| `sovereignmemory` | Memory snapshot bundles (custody transfer, encrypted) |
| `governance` | Policy update bundles (custody transfer, integrity-signed) |
| `mesh` | Routing topology exchange (best-effort) |
| `telemetry` | Metric bundles (best-effort, compressed) |
| `timeservice` | Time sync bundles (BPv7 timestamp blocks) |
| `twins` | Twin state sync across planetary nodes (custody transfer) |

---

## Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| D | This document; `interplanetaryprotocol` module stub |
| E | ION-DTN Python bindings wrapper; BPv7 bundle encoder/decoder |
| F | CGR integration with `PlanetaryScheduler`; BPSec encryption |
| G | Orbital ephemeris feed (NASA HORIZONS API); live contact graphs |

---

## References

- [RFC 9171 — Bundle Protocol Version 7](https://www.rfc-editor.org/rfc/rfc9171)
- [RFC 9172 — Bundle Protocol Security (BPSec)](https://www.rfc-editor.org/rfc/rfc9172)
- [NASA DTN Implementation (ION)](https://sourceforge.net/projects/ion-dtn/)
- [CCSDS 734.2-B — DTN Bundle Protocol Specification](https://public.ccsds.org)
- [IRTF DTN Research Group](https://datatracker.ietf.org/rg/dtnrg/about/)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-22 | Initial NEXUS Interplanetary Protocol specification |

---

*"Distance is not absence. It is deferred presence."*
*— R0GV3 The Alchemist*
