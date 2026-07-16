"""
core/simulation/seed.py

SeedController — deterministic random number generation for reproducible simulations.

Ensures that any given seed produces identical behaviour across runs by
propagating the seed to Python's random, numpy (if available), and
the simulation's own PRNG instance.
"""

from __future__ import annotations

import hashlib
import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)


class SeedController:
    """
    Controls the PRNG seed for a simulation run.

    Usage:
        sc = SeedController()
        sc.set_seed(42)
        val = sc.random()        # deterministic float in [0, 1)
        idx = sc.randint(0, 10)  # deterministic int
        shuffled = sc.shuffle([1, 2, 3, 4])
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._seed: Optional[int] = None
        self._rng = random.Random()
        if seed is not None:
            self.set_seed(seed)

    # ------------------------------------------------------------------
    # Seed management
    # ------------------------------------------------------------------

    def set_seed(self, seed: int) -> None:
        """Set an integer seed and reinitialise the PRNG."""
        self._seed = seed
        self._rng.seed(seed)
        self._seed_numpy(seed)
        logger.debug("[SeedController] Seed set to %d", seed)

    def set_seed_from_string(self, value: str) -> None:
        """Derive a deterministic integer seed from an arbitrary string."""
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)  # first 32 bits
        self.set_seed(seed)

    @property
    def current_seed(self) -> Optional[int]:
        return self._seed

    # ------------------------------------------------------------------
    # PRNG helpers
    # ------------------------------------------------------------------

    def random(self) -> float:
        """Return a deterministic float in [0.0, 1.0)."""
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        """Return a deterministic int N such that a <= N <= b."""
        return self._rng.randint(a, b)

    def choice(self, seq):
        """Return a deterministic random element from a non-empty sequence."""
        return self._rng.choice(seq)

    def shuffle(self, lst: list) -> list:
        """Return a deterministically shuffled copy of a list."""
        copy = list(lst)
        self._rng.shuffle(copy)
        return copy

    def sample(self, population, k: int) -> list:
        """Return k unique deterministic elements from population."""
        return self._rng.sample(population, k)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _seed_numpy(seed: int) -> None:
        try:
            import numpy as np  # noqa: PLC0415
            np.random.seed(seed)
        except ImportError:
            pass  # numpy is optional
