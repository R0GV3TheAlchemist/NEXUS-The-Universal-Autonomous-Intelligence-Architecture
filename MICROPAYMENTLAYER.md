# MICROPAYMENT LAYER

**NEXUS — The Universal Autonomous Intelligence Architecture**
Copyright (c) 2026 R0GV3 The Alchemist

---

## Overview

The NEXUS Micropayment Layer enables **value exchange between
GAIA nodes, human contributors, and autonomous agents** at
arbitrary granularity — from sub-cent compute credits to
provenance-linked contribution rewards.

It is built on:
- **Lightning Network** — Bitcoin Layer-2 payment channels for
  near-instant, near-zero-fee micropayments
- **Stripe Connect** — fiat on/off-ramp for human-facing payments
- **Payment channel state machines** — deterministic, auditable
  value flow between GAIA agents
- **Provenance tracking** — every payment carries a cryptographic
  reference to the contribution or service that earned it

---

## Design Principles

1. **Atomic provenance** — every payment references a specific
   action, contribution, or service via its provenance hash.
   Payments cannot be detached from their origin.

2. **Sovereign control** — GAIAN_LAWS.md governs what payments
   an agent may authorise. Payments above threshold require
   GovernanceEngine approval.

3. **Graceful degradation** — if the payment network is
   unavailable, GAIA operates normally and queues payments
   for settlement when connectivity is restored.

4. **Human-readable audit** — all payment events are logged
   in plain language to the SovereignMemory provenance chain.

---

## Architecture

### Payment Channel State Machine

```
 OPEN  →  ACTIVE  →  SETTLING  →  CLOSED
              ↑           |
              └── DISPUTE ┘
```

Each channel transition produces an immutable `ChannelEvent`
stored in SovereignMemory. Disputes trigger GovernanceEngine
review with a defined resolution window.

### Lightning Network Integration

GAIA nodes that operate payment channels run an **LND
(Lightning Network Daemon)** or **Core Lightning** sidecar.
The `micropayment` module interfaces via gRPC:

| Operation | LND RPC Call |
|-----------|-------------|
| Create invoice | `lnrpc.AddInvoice` |
| Pay invoice | `routerrpc.SendPaymentV2` |
| Check balance | `lnrpc.WalletBalance` |
| List transactions | `lnrpc.ListPayments` |

### Provenance-Linked Payments

Every `PaymentEvent` includes:
```json
{
  "payment_id": "uuid4",
  "amount_sats": 100,
  "recipient": "dtn://gaia/node-alpha/",
  "provenance_hash": "sha256:abc123...",
  "service_description": "Quantum chemistry simulation — H2O ground state",
  "authorized_by": "governance:policy-uuid",
  "timestamp_utc": "2026-07-22T21:00:00Z"
}
```

---

## GAIA Integration Points

| GAIA Module | Micropayment Role |
|-------------|------------------|
| `governance` | Approves payments above sovereign threshold |
| `sovereignmemory` | Stores payment provenance chain |
| `twins` | Twin sync services may have per-operation costs |
| `telemetry` | Emits payment event metrics |
| `mesh` | Routes payment messages between GAIA nodes |

---

## Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| D | This document |
| E | `micropayment` module stub: PaymentEvent, ChannelStateMachine, PaymentRouter |
| F | LND gRPC client wrapper; provenance-hash linking |
| G | Stripe Connect fiat gateway; multi-currency settlement |

---

## References

- [Lightning Network Whitepaper](https://lightning.network/lightning-network-paper.pdf)
- [LND gRPC API Reference](https://api.lightning.community/)
- [Stripe Connect Documentation](https://stripe.com/docs/connect)
- [Payment Channels — Bitcoin Developer Guide](https://developer.bitcoin.org/devguide/payment_channels.html)
- [GAIAN_LAWS.md](GAIAN_LAWS.md)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-22 | Initial NEXUS Micropayment Layer specification |

---

*"Value without provenance is noise. Provenance without value is memory. Together they are wealth."*
*— R0GV3 The Alchemist*
