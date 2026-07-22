# AMBIENT UI

**NEXUS — The Universal Autonomous Intelligence Architecture**
Copyright (c) 2026 R0GV3 The Alchemist

---

## Overview

NEXUS's Ambient UI layer enables **spatial, zero-install,
and environment-integrated interfaces** for GAIA — from
holographic overlays on physical spaces to progressive web
apps that feel native on any device, anywhere on Earth or
in orbit.

The architecture is built on:
- **OpenXR** — open standard for XR hardware abstraction
  (headsets, AR glasses, haptic devices)
- **WebXR Device API** — browser-native XR for zero-install
  deployment
- **Holographic rendering pipelines** — depth-composited
  spatial overlays for GAIA cognitive state visualisation
- **Progressive Web Apps (PWA)** — offline-capable,
  installable, zero-friction access to GAIA interfaces

---

## Design Philosophy

GAIA's UI is **ambient** — it is present in the environment
without demanding attention. It surfaces information when
it is relevant, retreats when it is not, and adapts to the
physical and cognitive context of the human it serves.

- **No forced interaction** — GAIA never interrupts unless
  the governance layer has determined intervention is
  warranted
- **Consent-gated rendering** — spatial overlays require
  explicit `TwinConsent` from the environment's owner
- **Affect-responsive** — the UI's visual and haptic
  language responds to `affectengine.AffectState`
- **Stage-aware** — interface complexity scales with the
  being's current Ascendence stage

---

## Interface Layers

### Layer 1 — Glanceable (always present)
- GAIA node health status (colour-coded ring)
- Affect state indicator (valence/arousal visualisation)
- Active alerts (CRITICAL signals from EmrysEngine)

### Layer 2 — Interactive (on attention)
- Stage transition notifications
- Governance decision requests
- SovereignMemory recall prompts

### Layer 3 — Immersive (on explicit entry)
- Full GAIA cognitive map (knowledge graph spatial view)
- Digital twin environment overlays
- Quantum chemistry / crystal resonance visualisations

---

## WebXR Integration

```javascript
// Phase E implementation target
navigator.xr.requestSession('immersive-ar').then(session => {
  // Render GAIA affect state as a spatial overlay
  const affectOverlay = new GAIAAffectRenderer(session);
  affectOverlay.bindAffectStream(gaiaNode.affectEngine);
  affectOverlay.start();
});
```

All WebXR sessions require:
1. Explicit user gesture to enter XR
2. `TwinConsent` record granting `read` on environment twin
3. GovernanceEngine check for spatial rendering policy

---

## Progressive Web App (PWA)

The NEXUS PWA is the **primary zero-install interface**:
- Served from GAIA node's API layer
- Service Worker caches critical UI for offline operation
- Background sync with GAIA state via WebSocket
- Push notifications for CRITICAL health signals
  (user-consent gated, GAIAN_LAWS.md Law III)

---

## GAIA Integration Points

| GAIA Module | UI Role |
|-------------|--------|
| `affectengine` | Drives affect-responsive UI colour and haptics |
| `stageengine` | Determines interface complexity tier |
| `twins` | Consent gate for environment spatial overlays |
| `governance` | Policy check for all rendering decisions |
| `telemetry` | UI interaction events emitted as telemetry |
| `timeservice` | Timestamps all UI events for provenance |

---

## Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| D | This document |
| E | PWA scaffold (React + Vite + Service Worker) |
| F | WebXR affect overlay prototype |
| G | OpenXR native client for headset platforms |

---

## References

- [OpenXR Specification — Khronos Group](https://www.khronos.org/openxr/)
- [WebXR Device API — W3C](https://www.w3.org/TR/webxr/)
- [Progressive Web Apps — web.dev](https://web.dev/progressive-web-apps/)
- [NEXUS DIGITALTWINS.md](DIGITALTWINS.md)
- [NEXUS affectengine](src-python/affectengine/)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-22 | Initial NEXUS Ambient UI specification |

---

*"The best interface is the one that disappears into the moment it serves."*
*— R0GV3 The Alchemist*
