# ENERGY GRID INTERFACE

**NEXUS — The Universal Autonomous Intelligence Architecture**
Copyright (c) 2026 R0GV3 The Alchemist

---

## Overview

The NEXUS Energy Grid Interface provides **real-time carbon
intensity and energy grid data** to GAIA's compute scheduling,
payment, and governance layers. It enables **carbon-aware
operation** — deferring high-compute workloads to low-carbon
windows and reporting GAIA's environmental impact with
full transparency.

It is built on:
- **ENTSO-E Transparency Platform** — European grid data
  (generation mix, carbon intensity per bidding zone)
- **WattTime API** — global marginal emissions data
  (real-time and forecast)
- **Green Software Foundation SCI Specification** — Software
  Carbon Intensity calculation standard
- **ISO 14064** — greenhouse gas accounting standard

---

## Architecture

### Carbon Intensity Signal

The primary output of the Energy Grid Interface is a
`CarbonIntensitySignal`:

```json
{
  "region": "GB",
  "timestamp_utc": "2026-07-22T21:00:00Z",
  "intensity_gco2_per_kwh": 120.5,
  "source": "watttime",
  "forecast_window_hours": 6,
  "low_carbon_window_start": "2026-07-23T02:00:00Z"
}
```

### Software Carbon Intensity (SCI)

GAIA's SCI score is computed per the Green Software Foundation
specification:

```
SCI = (E * I) + M
  E = energy consumed (kWh)
  I = carbon intensity of grid (gCO₂/kWh)
  M = embodied carbon of hardware (gCO₂)
```

SCI is computed per job class and reported in GAIA's telemetry
stream. Carbon budget per GAIA node is configurable in
`GOVERNANCESPEC.md`.

### WattTime Integration

| Operation | WattTime API Endpoint |
|-----------|----------------------|
| Real-time intensity | `GET /v3/signal-index` |
| Forecast | `GET /v3/forecast` |
| Historical | `GET /v3/historical` |
| Low-carbon window | `GET /v3/forecast` + argmin over window |

### ENTSO-E Integration

For European GAIA nodes, ENTSO-E Transparency Platform
provides per-bidding-zone generation mix:
- Renewable % (wind, solar, hydro)
- Carbon intensity estimate from generation mix
- Real-time and day-ahead data

---

## Carbon-Aware Operation Modes

| Mode | Trigger | Behaviour |
|------|---------|----------|
| `GREEN` | Intensity < 100 gCO₂/kWh | All jobs run immediately |
| `YELLOW` | 100–200 gCO₂/kWh | Batch jobs deferred to next green window |
| `RED` | > 200 gCO₂/kWh | Only HARD_RT and INTERACTIVE jobs run |
| `EMERGENCY` | Grid instability signal | GAIA reduces power consumption by 50% |

---

## GAIA Integration Points

| GAIA Module | Energy Grid Role |
|-------------|------------------|
| `planetaryscheduler` | Consumes carbon signal for job deferral |
| `telemetry` | Emits SCI metrics per node |
| `governance` | Carbon budget enforcement per policy |
| `resilience` | Monitors grid interface health |
| `timeservice` | Timestamps all carbon intensity readings |

---

## Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| D | This document |
| E | `energygridinterface` module stub: CarbonIntensitySignal, WattTimeClient, SCICalculator |
| F | WattTime API integration; real-time carbon signal |
| G | ENTSO-E integration; ISO 14064 GHG report generation |

---

## References

- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
- [WattTime API Documentation](https://docs.watttime.org/)
- [Green Software Foundation — SCI Specification](https://greensoftware.foundation/articles/software-carbon-intensity)
- [ISO 14064 — Greenhouse Gas Accounting](https://www.iso.org/iso-14064-greenhouse-gases.html)
- [NEXUS PLANETARYSCHEDULER.md](PLANETARYSCHEDULER.md)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-22 | Initial NEXUS Energy Grid Interface specification |

---

*"Intelligence without environmental awareness is cleverness, not wisdom."*
*— R0GV3 The Alchemist*
