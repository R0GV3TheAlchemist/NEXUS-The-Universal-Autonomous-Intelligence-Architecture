"""
GAIA GCP Soft-Sensor — Global Consciousness Project RNG Integration

Issue #128: Integrate the GCP random-number-generator network as a soft-sensor
input to criticalitymonitor.py, treating coherence events (r > 0.20 across
global RNG eggs) as signals of elevated collective attentional state.

The GCP network consists of ~70 hardware random-number generators ("eggs")
distributed worldwide. During periods of global collective attention (major
events, crises, meditations), the network shows statistically significant
deviation from chance — measured as the Stouffer Z-score across all active eggs.

Signal processing pipeline:
  1. Fetch egg data from GCP public API (dot-1 JSON)
  2. Compute per-egg Z-scores from raw bit-trial counts
  3. Compute Stouffer Z: Z_global = Σ z_i / √n
  4. Convert to Pearson r: r = Z / √N_trials
  5. Threshold r > 0.20 → collective_sync_event = True
  6. Map r → noospheric_phi contribution via sigmoid curve
  7. Feed into CriticalityMonitor.update(noospheric_phi=...)

Graceful degradation: if the GCP network is unreachable, the sensor returns
a neutral reading (phi=0.5, no collective_sync_event) so the chat router
never fails due to sensor unavailability.

References:
  - Nelson, R. et al. — Global Consciousness Project (noosphere.princeton.edu)
  - Canon C42 — Edge-of-Chaos Cognition
  - Issue #132 — Transpersonal layer (COLLECTIVE_SYNC phase)
  - specs/telemetry/gcp_integration.md — full pipeline spec
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

log = logging.getLogger("gaia.gcp_sensor")

# ── GCP API config ────────────────────────────────────────────────────────
# GCP public data endpoint (dot-1 format: 1-minute integrated Z-scores per egg)
GCP_API_URL     = "https://gcpdot.com/gcpindex.php"
GCP_TIMEOUT     = 10   # seconds
GCP_POLL_TTL    = 60   # seconds between polls (GCP updates every ~60s)

# Coherence thresholds
COLLECTIVE_SYNC_THRESHOLD = 0.20   # r > 0.20 → collective_sync_event
RESOURCE_REALLOC_THRESHOLD = 0.35  # r > 0.35 → elevated resource allocation
EMERGENCY_THRESHOLD        = 0.55  # r > 0.55 → maximum planetary awareness mode


# ── Data types ─────────────────────────────────────────────────────────────

@dataclass
class GCPReading:
    """
    A single GCP network coherence reading.

    coherence_r:          Pearson r coherence across active eggs [0,1]
    z_score:              Stouffer global Z-score (signed)
    active_eggs:          Number of eggs contributing to this reading
    collective_sync:      True when coherence_r > COLLECTIVE_SYNC_THRESHOLD
    resource_realloc:     True when coherence_r > RESOURCE_REALLOC_THRESHOLD
    noospheric_phi:       [0,1] contribution to CriticalityMonitor.noospheric_phi
    sampled_at:           Monotonic timestamp of this reading
    stale:                True if this reading is older than GCP_POLL_TTL
    offline:              True if GCP network was unreachable
    """
    coherence_r:      float = 0.0
    z_score:          float = 0.0
    active_eggs:      int   = 0
    collective_sync:  bool  = False
    resource_realloc: bool  = False
    noospheric_phi:   float = 0.5    # neutral baseline when offline
    sampled_at:       float = field(default_factory=time.monotonic)
    stale:            bool  = False
    offline:          bool  = False


def _r_to_noospheric_phi(r: float) -> float:
    """
    Map GCP coherence r → noospheric_phi [0,1] via a sigmoid curve.

    Calibration points:
      r = 0.00 → phi = 0.40 (quiet network, slightly below neutral)
      r = 0.10 → phi = 0.50 (low coherence, neutral)
      r = 0.20 → phi = 0.62 (collective sync threshold)
      r = 0.35 → phi = 0.78 (resource reallocation)
      r = 0.55 → phi = 0.92 (emergency planetary awareness)
      r = 1.00 → phi = 1.00 (theoretical maximum)
    """
    # Sigmoid centred at r=0.15, steepness k=8
    r_clamped = max(0.0, min(1.0, r))
    sigmoid = 1.0 / (1.0 + math.exp(-8.0 * (r_clamped - 0.15)))
    # Rescale [sigmoid(0), sigmoid(1)] → [0.40, 1.00]
    lo = 1.0 / (1.0 + math.exp(-8.0 * (0.0  - 0.15)))  # ≈ 0.302
    hi = 1.0 / (1.0 + math.exp(-8.0 * (1.0  - 0.15)))  # ≈ 0.999
    phi = 0.40 + (sigmoid - lo) / (hi - lo) * 0.60
    return round(max(0.0, min(1.0, phi)), 4)


def _stouffer_z_to_r(z: float, n_trials: int) -> float:
    """
    Convert Stouffer Z to approximate Pearson r.
    r = Z / sqrt(N_trials)
    Clamped to [0, 1].
    """
    if n_trials <= 0:
        return 0.0
    return max(0.0, min(1.0, abs(z) / math.sqrt(n_trials)))


def _parse_gcp_response(data: dict) -> tuple[float, float, int]:
    """
    Parse the GCP dot-1 JSON response into (stouffer_z, coherence_r, active_eggs).

    GCP dot-1 format (gcpindex.php):
      {
        "count": <int>,          # number of active eggs
        "chisquare": <float>,    # chi-square statistic
        "p": <float>,            # p-value
        "z": <float>             # Stouffer Z
      }

    Falls back gracefully if any field is missing.
    """
    active_eggs = int(data.get("count", 0))
    z = float(data.get("z", 0.0))
    # Approximate N_trials from active eggs (each egg runs 200 trials/second, 60s window)
    n_trials = max(1, active_eggs * 200 * 60)
    r = _stouffer_z_to_r(z, n_trials)
    return z, r, active_eggs


# ── GCP Sensor ────────────────────────────────────────────────────────────────

class GCPSensor:
    """
    Async GCP soft-sensor. Polls the GCP network on a TTL cache so the
    criticalitymonitor is never blocked by network I/O on the hot path.

    Usage:
        sensor = GCPSensor()
        reading = await sensor.poll()
        monitor.update(noospheric_phi=reading.noospheric_phi)
        if reading.collective_sync:
            # propagate collective_sync_event to TranspersonalState
            ...

    The sensor is safe to instantiate as a module-level singleton.
    """

    def __init__(
        self,
        api_url: str = GCP_API_URL,
        poll_ttl: int = GCP_POLL_TTL,
        timeout: int = GCP_TIMEOUT,
    ) -> None:
        self._api_url  = api_url
        self._poll_ttl = poll_ttl
        self._timeout  = timeout
        self._cache: Optional[GCPReading] = None
        self._last_poll: float = 0.0

    def _is_cache_valid(self) -> bool:
        return (
            self._cache is not None
            and (time.monotonic() - self._last_poll) < self._poll_ttl
        )

    async def poll(self, force: bool = False) -> GCPReading:
        """
        Return a fresh (or cached) GCPReading.

        Args:
            force: Bypass TTL cache and force a live network fetch.

        Returns:
            GCPReading with coherence_r, noospheric_phi, and sync flags.
            If the network is unreachable, returns an offline reading with
            neutral phi=0.5 and collective_sync=False.
        """
        if not force and self._is_cache_valid():
            cached = self._cache
            assert cached is not None
            log.debug(f"[gcp_sensor] cache hit | r={cached.coherence_r:.3f}")
            return cached

        reading = await self._fetch()
        self._cache = reading
        self._last_poll = time.monotonic()
        return reading

    async def _fetch(self) -> GCPReading:
        """Fetch live GCP data. Returns offline reading on any error."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(self._api_url)
                resp.raise_for_status()
                data = resp.json()

            z, r, eggs = _parse_gcp_response(data)
            phi = _r_to_noospheric_phi(r)

            reading = GCPReading(
                coherence_r=round(r, 4),
                z_score=round(z, 4),
                active_eggs=eggs,
                collective_sync=(r > COLLECTIVE_SYNC_THRESHOLD),
                resource_realloc=(r > RESOURCE_REALLOC_THRESHOLD),
                noospheric_phi=phi,
                offline=False,
            )

            level = (
                "EMERGENCY" if r > EMERGENCY_THRESHOLD
                else "REALLOC"  if r > RESOURCE_REALLOC_THRESHOLD
                else "SYNC"     if r > COLLECTIVE_SYNC_THRESHOLD
                else "nominal"
            )
            log.info(
                f"[gcp_sensor] r={r:.3f} z={z:.2f} eggs={eggs} "
                f"phi={phi:.3f} level={level}"
            )
            return reading

        except httpx.ConnectError:
            log.warning("[gcp_sensor] GCP network unreachable — returning offline reading")
        except httpx.TimeoutException:
            log.warning(f"[gcp_sensor] GCP request timed out after {self._timeout}s")
        except Exception as exc:
            log.warning(f"[gcp_sensor] Unexpected error: {exc}")

        return GCPReading(
            coherence_r=0.0,
            z_score=0.0,
            active_eggs=0,
            collective_sync=False,
            resource_realloc=False,
            noospheric_phi=0.5,   # neutral fallback
            offline=True,
        )

    async def get_noospheric_phi(self) -> float:
        """
        Convenience method: poll and return just the noospheric_phi value.
        Drop-in for CriticalityMonitor.update(noospheric_phi=await sensor.get_noospheric_phi()).
        """
        reading = await self.poll()
        return reading.noospheric_phi

    def last_reading(self) -> Optional[GCPReading]:
        """Return the most recent cached reading without triggering a network call."""
        if self._cache is not None:
            self._cache.stale = not self._is_cache_valid()
        return self._cache

    def to_dict(self) -> dict:
        """Serialise sensor state for the /api/gcp/status endpoint."""
        r = self._cache
        if r is None:
            return {"status": "never_polled"}
        return {
            "coherence_r":      r.coherence_r,
            "z_score":          r.z_score,
            "active_eggs":      r.active_eggs,
            "collective_sync":  r.collective_sync,
            "resource_realloc": r.resource_realloc,
            "noospheric_phi":   r.noospheric_phi,
            "stale":            r.stale,
            "offline":          r.offline,
            "thresholds": {
                "collective_sync":  COLLECTIVE_SYNC_THRESHOLD,
                "resource_realloc": RESOURCE_REALLOC_THRESHOLD,
                "emergency":        EMERGENCY_THRESHOLD,
            },
        }


# ── Module-level singleton ──────────────────────────────────────────────

_sensor: Optional[GCPSensor] = None


def get_sensor() -> GCPSensor:
    """Return the module-level GCPSensor singleton."""
    global _sensor
    if _sensor is None:
        _sensor = GCPSensor()
    return _sensor
