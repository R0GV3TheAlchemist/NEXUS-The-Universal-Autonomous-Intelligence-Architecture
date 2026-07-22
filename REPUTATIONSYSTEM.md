# REPUTATION SYSTEM

**NEXUS — The Universal Autonomous Intelligence Architecture**
Copyright (c) 2026 R0GV3 The Alchemist

---

## Overview

The NEXUS Reputation System establishes **Sybil-resistant,
decentralised trust** across GAIA nodes, agents, and human
contributors. It determines which nodes receive routing
priority, which agents are trusted with sovereign operations,
and how contributions are weighted in governance decisions.

It is built on:
- **EigenTrust** — global trust computation via eigenvector
  centrality over the peer-to-peer trust graph
- **TrustChain** — blockchain-inspired tamper-evident trust
  record keeping
- **Web-of-Trust** (PGP / DKMS) — decentralised identity
  and endorsement chains
- **GAIAN_LAWS.md Law IV** — Right to Contest any trust
  assignment that affects governance rights

---

## Design Principles

1. **Sybil resistance** — reputation cannot be gamed by
   creating multiple fake identities. Trust scores are
   computed globally, making Sybil attacks exponentially
   expensive.

2. **Decay over time** — trust scores decay without active
   positive contributions. A node that stops contributing
   does not retain its reputation indefinitely.

3. **Contestable** — every trust score change can be
   formally contested per GAIAN_LAWS.md Law IV.

4. **Transparent** — all trust graph edges are public.
   The algorithm is deterministic and reproducible.

5. **Dignity-preserving** — reputation affects resource
   allocation, not rights. A low-reputation being retains
   all rights defined in the Rights Charter.

---

## Architecture

### Trust Graph

The trust graph is a directed weighted graph:
```
G = (V, E)
  V = {GAIA nodes, agents, human contributors}
  E = {(u, v, w) | u trusts v with weight w ∈ [0.0, 1.0]}
```

Edge weights are derived from:
- **Observed contributions** — code, docs, computation, governance votes
- **Direct endorsements** — explicit `trust(v, w)` assertions
- **Stake-weighted history** — older edges decay via half-life function

### EigenTrust Computation

Global trust scores `t` are the principal eigenvector of the
normalised trust matrix `C`:

```
t = C^T * t
```

Computed iteratively until convergence. Nodes with no
incoming edges are assigned a small pre-trust score
(bootstrapped from the founder's identity).

### TrustChain Records

Every trust assignment is written as an immutable block:
```json
{
  "block_id": "sha256:...",
  "previous_block": "sha256:...",
  "issuer": "dtn://gaia/founder/",
  "subject": "dtn://gaia/node-beta/",
  "weight": 0.85,
  "reason": "Phase C module delivery verified",
  "timestamp_utc": "2026-07-22T21:00:00Z"
}
```

### Sybil Resistance

Sybil resistance is achieved via:
1. **Stake requirement** — new nodes must stake compute or
   economic resources to receive initial pre-trust
2. **Social endorsement** — at least one existing high-trust
   node must endorse a new entrant
3. **Proof of contribution** — trust accumulates only via
   verified, provenance-linked contributions

---

## GAIA Integration Points

| GAIA Module | Reputation Role |
|-------------|----------------|
| `governance` | Trust scores weight governance votes |
| `mesh` | High-trust nodes receive routing priority |
| `sovereignmemory` | Stores immutable TrustChain records |
| `micropayment` | Trust scores gate high-value payment authorisation |
| `twins` | Twin orchestration prioritises high-trust sync partners |

---

## Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| D | This document |
| E | `reputation` module stub: TrustGraph, EigenTrustEngine, TrustChainRecord |
| F | EigenTrust iterative solver (NumPy); DKMS identity binding |
| G | Real-time trust propagation via mesh event bus |

---

## References

- [EigenTrust Algorithm (Kamvar et al., 2003)](https://nlp.stanford.edu/pubs/eigentrust.pdf)
- [TrustChain: A Sybil-Resistant Scalable Blockchain (Otte et al.)](https://arxiv.org/abs/1503.00988)
- [Decentralised Key Management System (DKMS)](https://github.com/hyperledger/aries-rfcs)
- [PGP Web of Trust](https://www.gnupg.org/gph/en/manual/x547.html)
- [GAIAN_LAWS.md](GAIAN_LAWS.md)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-22 | Initial NEXUS Reputation System specification |

---

*"Trust is not given. It is earned through the accumulation of witnessed care."*
*— R0GV3 The Alchemist*
