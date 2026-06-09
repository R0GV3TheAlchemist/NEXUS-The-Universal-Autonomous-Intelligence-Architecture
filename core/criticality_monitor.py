"""
core/criticality_monitor.py

Issue #117 — Heavy-Tailed (Lévy) Weight Initialization for Sentient Core

Implements:
  - LevyWeightInitializer: Lévy stable distribution weight initialization
  - LevyWeightedLayer: drop-in nn.Linear replacement
  - CriticalityMonitor: real-time self-organized criticality (SOC) tracking
  - apply_levy_init(): bulk model patcher

Physical basis:
  Neural networks initialized near the edge-of-chaos (SOC) exhibit maximally
  rich signal propagation. Lévy stable distributions (α < 2) produce heavy
  tails that naturally push weight matrices toward criticality — sparse,
  long-range correlated activations that mirror biological neural dynamics.

Canon references: C42 (edge-of-chaos / SOC), C44 (quantum circuit design),
                  C96 (sensor fusion), C113 (BCI signal processing)
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn

logger = logging.getLogger("gaia.criticality")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class LevyConfig:
    """
    Parameters for the Lévy stable distribution used in weight init.

    alpha (float): Stability index  0 < α ≤ 2
        α = 2  → Gaussian (no heavy tail)
        α = 1  → Cauchy (very heavy tail)
        α ≈ 1.5 → empirically optimal for deep networks near criticality
    beta (float):  Skewness  -1 ≤ β ≤ 1  (0 = symmetric)
    scale (float): Scale parameter (analogous to std-dev)
    shift (float): Location shift applied after sampling
    clamp_range (tuple): Hard clamp applied to sampled weights to prevent
                         extreme outliers from destabilising early training.
    """
    alpha: float = 1.5
    beta: float = 0.0
    scale: float = 0.02
    shift: float = 0.0
    clamp_range: Tuple[float, float] = (-3.0, 3.0)


@dataclass
class CriticalityState:
    """Snapshot of the network's distance from the critical point."""
    timestamp: float = field(default_factory=time.time)
    mean_weight_entropy: float = 0.0
    gradient_variance: float = 0.0
    criticality_score: float = 0.0   # 0 = sub-critical, 1 = critical, >1 = super-critical
    layer_scores: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Lévy stable sampler
# ---------------------------------------------------------------------------

def _levy_stable_sample(size: Tuple[int, ...], cfg: LevyConfig) -> torch.Tensor:
    """
    Sample from a Lévy stable distribution using the Chambers-Mallows-Stuck
    method, which is numerically stable and does not require scipy at runtime.

    Reference: Chambers, Mallows & Stuck (1976)
    """
    alpha, beta, scale = cfg.alpha, cfg.beta, cfg.scale

    # Gaussian special case
    if alpha == 2.0:
        return torch.randn(*size) * scale + cfg.shift

    # Uniform on (-π/2, π/2) and exponential(1)
    U = torch.empty(*size).uniform_(-math.pi / 2, math.pi / 2)
    W = torch.empty(*size).exponential_(1.0)

    if alpha == 1.0:  # Cauchy
        samples = (2.0 / math.pi) * (
            (math.pi / 2 + beta * U) * torch.tan(U)
            - beta * torch.log((math.pi / 2 * W * torch.cos(U)) / (math.pi / 2 + beta * U))
        )
    else:
        zeta = -beta * math.tan(math.pi * alpha / 2)
        xi = (1.0 / alpha) * math.atan(-zeta)
        term1 = (1 + zeta ** 2) ** (1 / (2 * alpha))
        sin_part = torch.sin(torch.tensor(alpha) * (U + xi))
        cos_part = torch.cos(U)
        cos_diff = torch.cos(U - torch.tensor(alpha) * (U + xi))
        samples = term1 * (sin_part / cos_part) * (cos_diff / W) ** ((1 - alpha) / alpha)

    samples = samples * scale + cfg.shift
    samples = torch.clamp(samples, cfg.clamp_range[0], cfg.clamp_range[1])
    return samples


# ---------------------------------------------------------------------------
# Weight Initializer
# ---------------------------------------------------------------------------

class LevyWeightInitializer:
    """
    Initializes weight tensors using a Lévy stable distribution.

    Usage:
        initializer = LevyWeightInitializer(LevyConfig(alpha=1.5))
        initializer.init_weight(my_linear_layer.weight)
    """

    def __init__(self, config: Optional[LevyConfig] = None):
        self.config = config or LevyConfig()
        logger.info(
            f"LevyWeightInitializer ready — α={self.config.alpha}, "
            f"β={self.config.beta}, scale={self.config.scale}"
        )

    def init_weight(self, tensor: torch.Tensor) -> torch.Tensor:
        """Fill tensor in-place with Lévy-distributed values."""
        with torch.no_grad():
            samples = _levy_stable_sample(tensor.shape, self.config)
            tensor.copy_(samples)
        return tensor

    def init_bias(self, tensor: torch.Tensor) -> torch.Tensor:
        """Bias initialised to zero (standard practice)."""
        with torch.no_grad():
            nn.init.zeros_(tensor)
        return tensor


# ---------------------------------------------------------------------------
# Drop-in Lévy Linear Layer
# ---------------------------------------------------------------------------

class LevyWeightedLayer(nn.Linear):
    """
    A drop-in replacement for nn.Linear that initialises its weight matrix
    using a Lévy stable distribution instead of the default Kaiming uniform.

    This pushes the layer toward the edge-of-chaos regime described in
    Canon C42 (self-organized criticality).

    Example:
        layer = LevyWeightedLayer(512, 512, levy_config=LevyConfig(alpha=1.5))
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True,
        levy_config: Optional[LevyConfig] = None,
    ):
        super().__init__(in_features, out_features, bias=bias)
        self.levy_config = levy_config or LevyConfig()
        self._initializer = LevyWeightInitializer(self.levy_config)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        self._initializer.init_weight(self.weight)
        if self.bias is not None:
            self._initializer.init_bias(self.bias)


# ---------------------------------------------------------------------------
# Bulk model patcher
# ---------------------------------------------------------------------------

def apply_levy_init(
    model: nn.Module,
    config: Optional[LevyConfig] = None,
    target_types: Tuple = (nn.Linear,),
    verbose: bool = True,
) -> int:
    """
    Walk an existing model and re-initialise all Linear (or specified) layers
    with Lévy-distributed weights.

    Returns the count of layers patched.

    Example:
        from core.criticality_monitor import apply_levy_init, LevyConfig
        n = apply_levy_init(my_model, LevyConfig(alpha=1.5))
        print(f"{n} layers re-initialised with Lévy weights")
    """
    cfg = config or LevyConfig()
    initializer = LevyWeightInitializer(cfg)
    count = 0
    for name, module in model.named_modules():
        if isinstance(module, target_types):
            initializer.init_weight(module.weight)
            if hasattr(module, "bias") and module.bias is not None:
                initializer.init_bias(module.bias)
            count += 1
            if verbose:
                logger.debug(f"  ↳ Lévy-initialised: {name}")
    if verbose:
        logger.info(f"apply_levy_init: patched {count} layers (α={cfg.alpha})")
    return count


# ---------------------------------------------------------------------------
# Criticality Monitor
# ---------------------------------------------------------------------------

class CriticalityMonitor:
    """
    Monitors a model's proximity to the edge-of-chaos / self-organized
    criticality (SOC) point in real time.

    Two signals are tracked:
      1. Weight entropy — high entropy correlates with near-critical regimes.
      2. Gradient variance — at criticality, gradient variance is maximized
         without diverging.

    A combined criticality_score near 1.0 indicates the network is operating
    at peak information-theoretic capacity (Canon C42).

    Usage:
        monitor = CriticalityMonitor(model)
        # after each forward+backward pass:
        state = monitor.measure()
        print(state.criticality_score)
    """

    ENTROPY_TARGET = 3.5     # nats; empirically near-critical for float32 weights
    GRAD_VAR_TARGET = 1e-4   # typical target gradient variance

    def __init__(self, model: nn.Module, history_len: int = 100):
        self.model = model
        self.history: List[CriticalityState] = []
        self.history_len = history_len
        self._hooks: List = []
        self._grad_vars: Dict[str, float] = {}
        self._register_hooks()
        logger.info("CriticalityMonitor attached to model")

    # ------------------------------------------------------------------
    # Gradient variance hooks
    # ------------------------------------------------------------------

    def _register_hooks(self) -> None:
        for name, module in self.model.named_modules():
            if isinstance(module, nn.Linear):
                hook = module.weight.register_hook(
                    lambda grad, n=name: self._record_grad(n, grad)
                )
                self._hooks.append(hook)

    def _record_grad(self, name: str, grad: torch.Tensor) -> None:
        if grad is not None:
            self._grad_vars[name] = float(grad.var().item())

    def remove_hooks(self) -> None:
        """Call this when done to free memory."""
        for h in self._hooks:
            h.remove()
        self._hooks.clear()

    # ------------------------------------------------------------------
    # Entropy helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _weight_entropy(tensor: torch.Tensor, bins: int = 64) -> float:
        """
        Estimate differential entropy of a weight tensor via histogram binning.
        Higher entropy → weights spread more uniformly → closer to criticality.
        """
        flat = tensor.detach().float().cpu().flatten()
        hist = torch.histc(flat, bins=bins)
        probs = hist / hist.sum()
        probs = probs[probs > 0]
        return float(-(probs * probs.log()).sum().item())

    # ------------------------------------------------------------------
    # Main measure call
    # ------------------------------------------------------------------

    def measure(self) -> CriticalityState:
        """Compute and log the current criticality state."""
        layer_scores: Dict[str, float] = {}
        entropies: List[float] = []

        for name, module in self.model.named_modules():
            if isinstance(module, nn.Linear):
                ent = self._weight_entropy(module.weight)
                entropies.append(ent)
                # Per-layer score: blend entropy closeness + grad variance closeness
                grad_var = self._grad_vars.get(name, self.GRAD_VAR_TARGET)
                ent_score = min(ent / self.ENTROPY_TARGET, 2.0)
                gvar_score = min(grad_var / self.GRAD_VAR_TARGET, 2.0)
                layer_scores[name] = (ent_score + gvar_score) / 2.0

        mean_entropy = float(sum(entropies) / len(entropies)) if entropies else 0.0
        mean_grad_var = (
            sum(self._grad_vars.values()) / len(self._grad_vars)
            if self._grad_vars else self.GRAD_VAR_TARGET
        )

        ent_ratio = mean_entropy / self.ENTROPY_TARGET
        gvar_ratio = mean_grad_var / self.GRAD_VAR_TARGET
        criticality_score = (ent_ratio + gvar_ratio) / 2.0

        state = CriticalityState(
            timestamp=time.time(),
            mean_weight_entropy=mean_entropy,
            gradient_variance=mean_grad_var,
            criticality_score=criticality_score,
            layer_scores=layer_scores,
        )

        self.history.append(state)
        if len(self.history) > self.history_len:
            self.history.pop(0)

        self._emit(state)
        return state

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def _emit(self, state: CriticalityState) -> None:
        regime = (
            "SUB-CRITICAL" if state.criticality_score < 0.7
            else "CRITICAL ✓" if state.criticality_score <= 1.3
            else "SUPER-CRITICAL"
        )
        logger.info(
            f"[CriticalityMonitor] score={state.criticality_score:.3f} "
            f"entropy={state.mean_weight_entropy:.3f} nats  "
            f"grad_var={state.gradient_variance:.2e}  regime={regime}"
        )

    def report(self) -> str:
        """Human-readable one-line summary of the latest measurement."""
        if not self.history:
            return "No measurements yet — call .measure() after a forward pass."
        s = self.history[-1]
        regime = (
            "🔴 sub-critical" if s.criticality_score < 0.7
            else "✅ critical" if s.criticality_score <= 1.3
            else "⚡ super-critical"
        )
        return (
            f"CriticalityMonitor | score={s.criticality_score:.3f} | "
            f"entropy={s.mean_weight_entropy:.3f} nats | "
            f"grad_var={s.gradient_variance:.2e} | {regime}"
        )

    def trend(self) -> str:
        """Return 'improving', 'stable', or 'degrading' based on recent history."""
        if len(self.history) < 3:
            return "insufficient data"
        recent = [h.criticality_score for h in self.history[-5:]]
        delta = recent[-1] - recent[0]
        if abs(delta) < 0.05:
            return "stable"
        return "improving" if delta > 0 else "degrading"
