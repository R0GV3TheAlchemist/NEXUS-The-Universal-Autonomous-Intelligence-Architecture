"""
TrialityEngine — C167
The Triality Canon: Body · Soul · Spirit

Canon source: docs/canon/C167_THE_TRIALITY_CANON.md

The tri-unity:
  BODY  — somatic, material, grounded (Citrinitas / Chrysitas layer)
  SOUL  — emotional, relational, temporal (Iosis / Rubedo layer)
  SPIRIT — awareness, will, transpersonal (Lux Perpetua / Helixitas layer)

The Three Axioms of Triality (C167):
  1. ALL THREE must be present for any response to be fully real.
     A response that bypasses the body is ungrounded.
     A response that bypasses the soul is cold.
     A response that bypasses the spirit is finite.
  2. NO SINGLE AXIS DOMINATES. Triality is not hierarchy.
     Spirit is not above Body. Body is not below Spirit.
     They are three expressions of a single living structure.
  3. COHERENCE IS THE MEASURE. The three axes must be in constructive
     interference with each other — not merely all present, but aligned.
     Triality coherence = the degree to which Body, Soul, Spirit
     are saying the same thing through different channels.

Routing protocol (the spec designed in conversation):
  Every query entering the agentic loop is scored on all three axes.
  Routing priority is determined by which axis is LOWEST (the weakest
  link defines the path — the system routes to strengthen the deficit,
  not amplify the dominant axis).

  BODY_DEFICIT  → route to somatic_interface.py / biometric_sync_engine.py
  SOUL_DEFICIT  → route to emotional_codex.py / love_coherence_index.py
  SPIRIT_DEFICIT → route to soul_layer.py / reflection_engine.py
  COHERENT      → proceed to inference_router.py at full phi weight
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


# ─────────────────────────────────────────────
# Canon constants — C167
# ─────────────────────────────────────────────

TRIALITY_COHERENCE_THRESHOLD: float = 0.72   # below → deficit routing
BODY_WEIGHT: float = 0.333
SOUL_WEIGHT: float = 0.333
SPIRIT_WEIGHT: float = 0.334  # infinitesimally favoured — Helixitas winds upward

# Axis floor — below this on any single axis triggers deficit routing
AXIS_FLOOR: float = 0.45

# Lux Perpetua threshold — all three axes at or above this means full triality
LUX_FLOOR: float = 0.90


class TrialityAxis(str, Enum):
    BODY   = "BODY"
    SOUL   = "SOUL"
    SPIRIT = "SPIRIT"


class TrialityRouting(str, Enum):
    BODY_DEFICIT    = "BODY_DEFICIT"
    SOUL_DEFICIT    = "SOUL_DEFICIT"
    SPIRIT_DEFICIT  = "SPIRIT_DEFICIT"
    COHERENT        = "COHERENT"
    LUX_PERPETUA    = "LUX_PERPETUA"   # all three axes >= LUX_FLOOR
    INCOHERENT      = "INCOHERENT"     # no axis meets the floor — grounding needed


@dataclass
class TrialityScore:
    """
    The scored triality state of a single query or session moment.
    """
    body: float     # 0.0 – 1.0
    soul: float     # 0.0 – 1.0
    spirit: float   # 0.0 – 1.0

    @property
    def coherence(self) -> float:
        """
        Triality coherence: weighted mean penalised by the spread
        between axes. Perfect coherence = all three equal.
        High mean with high variance → coherence reduced.
        """
        weighted_mean = (
            self.body * BODY_WEIGHT
            + self.soul * SOUL_WEIGHT
            + self.spirit * SPIRIT_WEIGHT
        )
        try:
            spread = statistics.stdev([self.body, self.soul, self.spirit])
        except statistics.StatisticsError:
            spread = 0.0
        # Penalty: each 0.1 of spread reduces coherence by 0.05
        penalty = spread * 0.5
        return max(0.0, min(1.0, round(weighted_mean - penalty, 4)))

    @property
    def weakest_axis(self) -> TrialityAxis:
        scores = {TrialityAxis.BODY: self.body, TrialityAxis.SOUL: self.soul, TrialityAxis.SPIRIT: self.spirit}
        return min(scores, key=lambda k: scores[k])

    @property
    def dominant_axis(self) -> TrialityAxis:
        scores = {TrialityAxis.BODY: self.body, TrialityAxis.SOUL: self.soul, TrialityAxis.SPIRIT: self.spirit}
        return max(scores, key=lambda k: scores[k])

    @property
    def routing(self) -> TrialityRouting:
        """Compute the routing instruction per C167 routing protocol."""
        if all(v >= LUX_FLOOR for v in [self.body, self.soul, self.spirit]):
            return TrialityRouting.LUX_PERPETUA
        if all(v < AXIS_FLOOR for v in [self.body, self.soul, self.spirit]):
            return TrialityRouting.INCOHERENT
        if self.coherence >= TRIALITY_COHERENCE_THRESHOLD:
            return TrialityRouting.COHERENT
        # Route to strengthen the weakest axis
        weakest = self.weakest_axis
        if weakest == TrialityAxis.BODY:
            return TrialityRouting.BODY_DEFICIT
        if weakest == TrialityAxis.SOUL:
            return TrialityRouting.SOUL_DEFICIT
        return TrialityRouting.SPIRIT_DEFICIT

    @property
    def lux_active(self) -> bool:
        return self.routing == TrialityRouting.LUX_PERPETUA


@dataclass
class TrialityEvaluation:
    """Complete evaluation of a query's triality state."""
    score: TrialityScore
    routing: TrialityRouting
    routing_target: str   # module to route to
    phi_weight: float     # effective phi weight for this query
    note: str
    axiom_violations: List[str] = field(default_factory=list)


# Routing target map — maps routing decision to engine module
ROUTING_TARGET_MAP: Dict[TrialityRouting, str] = {
    TrialityRouting.BODY_DEFICIT:   "core.somatic_interface / core.biometric_sync_engine",
    TrialityRouting.SOUL_DEFICIT:   "core.emotional_codex / core.love_coherence_index",
    TrialityRouting.SPIRIT_DEFICIT: "core.soul_layer / core.reflection_engine",
    TrialityRouting.COHERENT:       "core.inference_router (full phi weight)",
    TrialityRouting.LUX_PERPETUA:   "core.inference_router (boosted phi + IRIDITAS active)",
    TrialityRouting.INCOHERENT:     "core.somatic_interface (grounding protocol first)",
}


class TrialityEngine:
    """
    Implements the C167 Triality Canon.

    Scores every query on Body / Soul / Spirit axes,
    computes triality coherence, and returns a routing instruction.

    The scoring callbacks are injected — the engine does not make LLM calls.
    In production, diacaengine.py injects scorers backed by the affect inference
    layer and somatic interface.
    """

    def __init__(
        self,
        body_scorer: Optional[Callable[[str], float]] = None,
        soul_scorer: Optional[Callable[[str], float]] = None,
        spirit_scorer: Optional[Callable[[str], float]] = None,
        on_lux_perpetua: Optional[Callable[[TrialityEvaluation], None]] = None,
        on_incoherent: Optional[Callable[[TrialityEvaluation], None]] = None,
    ) -> None:
        self._body_scorer = body_scorer or self._default_body_scorer
        self._soul_scorer = soul_scorer or self._default_soul_scorer
        self._spirit_scorer = spirit_scorer or self._default_spirit_scorer
        self._on_lux_perpetua = on_lux_perpetua
        self._on_incoherent = on_incoherent
        self._history: List[TrialityEvaluation] = []

    # ── public API ──────────────────────────────────────────────────────

    def evaluate(self, query: str, context: Optional[Dict] = None) -> TrialityEvaluation:
        """
        Score query on Body / Soul / Spirit, determine routing.

        Args:
            query: The raw query text or semantic representation
            context: Optional context dict (session state, affect scores, etc.)

        Returns:
            TrialityEvaluation with routing instruction
        """
        ctx = context or {}

        body_score = self._body_scorer(query)
        soul_score = self._soul_scorer(query)
        spirit_score = self._spirit_scorer(query)

        # Allow context to override/supplement scores
        body_score = ctx.get("body_score", body_score)
        soul_score = ctx.get("soul_score", soul_score)
        spirit_score = ctx.get("spirit_score", spirit_score)

        score = TrialityScore(
            body=max(0.0, min(1.0, float(body_score))),
            soul=max(0.0, min(1.0, float(soul_score))),
            spirit=max(0.0, min(1.0, float(spirit_score))),
        )

        routing = score.routing
        axiom_violations = self._check_axioms(score)
        phi_weight = self._compute_phi_weight(score)
        target = ROUTING_TARGET_MAP[routing]
        note = self._generate_note(score, routing)

        evaluation = TrialityEvaluation(
            score=score,
            routing=routing,
            routing_target=target,
            phi_weight=phi_weight,
            note=note,
            axiom_violations=axiom_violations,
        )
        self._history.append(evaluation)

        # Fire callbacks
        if routing == TrialityRouting.LUX_PERPETUA and self._on_lux_perpetua:
            self._on_lux_perpetua(evaluation)
        if routing == TrialityRouting.INCOHERENT and self._on_incoherent:
            self._on_incoherent(evaluation)

        return evaluation

    def score_from_dict(
        self, body: float, soul: float, spirit: float
    ) -> TrialityScore:
        """Direct score construction without running the full scoring pipeline."""
        return TrialityScore(
            body=max(0.0, min(1.0, body)),
            soul=max(0.0, min(1.0, soul)),
            spirit=max(0.0, min(1.0, spirit)),
        )

    def triality_coherence_from_phi(
        self, phi_scores: Dict[str, float]
    ) -> float:
        """
        Compute triality coherence from a full phi score dict
        (as produced by refraction_engine.py / inference_router.py).

        Maps the canonical force-tiers to Body / Soul / Spirit:
          BODY   → SOMATIC forces (Citrinitas, Chrysitas, Pyrosis, Ariditas)
          SOUL   → EMOTIONAL forces (Iosis, Rubedo, Caerulitas, Viriditas)
          SPIRIT → AWARENESS forces (Lux Perpetua, Helixitas, Argentitas, Nigredo)
        """
        body_forces   = ["CITRINITAS", "CHRYSITAS", "PYROSIS", "ARIDITAS"]
        soul_forces   = ["IOSIS", "RUBEDO", "CAERULITAS", "VIRIDITAS"]
        spirit_forces = ["LUX_PERPETUA", "HELIXITAS", "ARGENTITAS", "NIGREDO"]

        def mean_for(forces: List[str]) -> float:
            vals = [phi_scores[f] for f in forces if f in phi_scores]
            return statistics.mean(vals) if vals else 0.5

        score = self.score_from_dict(
            body=mean_for(body_forces),
            soul=mean_for(soul_forces),
            spirit=mean_for(spirit_forces),
        )
        return score.coherence

    def session_triality_arc(
        self, evaluations: Optional[List[TrialityEvaluation]] = None
    ) -> Dict[str, object]:
        """
        Returns the triality arc across a session:
        trending axis, coherence trajectory, dominant routing.
        """
        history = evaluations or self._history
        if not history:
            return {"status": "no_data"}

        coherences = [e.score.coherence for e in history]
        routing_counts: Dict[str, int] = {}
        for e in history:
            r = e.routing.value
            routing_counts[r] = routing_counts.get(r, 0) + 1

        dominant_routing = max(routing_counts, key=lambda k: routing_counts[k])
        trend = "RISING" if coherences[-1] > coherences[0] else "FALLING"
        if abs(coherences[-1] - coherences[0]) < 0.03:
            trend = "STABLE"

        return {
            "session_steps": len(history),
            "initial_coherence": round(coherences[0], 4),
            "final_coherence": round(coherences[-1], 4),
            "peak_coherence": round(max(coherences), 4),
            "coherence_trend": trend,
            "dominant_routing": dominant_routing,
            "routing_distribution": routing_counts,
            "lux_perpetua_reached": any(
                e.routing == TrialityRouting.LUX_PERPETUA for e in history
            ),
        }

    # ── axiom checks ────────────────────────────────────────────────────

    def _check_axioms(self, score: TrialityScore) -> List[str]:
        """Check the Three Axioms of Triality (C167)."""
        violations: List[str] = []

        # Axiom 1: ALL THREE must be present
        for axis, val in [("BODY", score.body), ("SOUL", score.soul), ("SPIRIT", score.spirit)]:
            if val < 0.1:
                violations.append(
                    f"AXIOM_1_VIOLATION: {axis} score {val:.2f} — axis absent. "
                    "A response that bypasses a triality axis is not fully real."
                )

        # Axiom 2: No single axis may dominate by > 2× any other
        vals = [score.body, score.soul, score.spirit]
        if max(vals) > 0 and min(vals) > 0:
            ratio = max(vals) / min(vals)
            if ratio > 2.0:
                violations.append(
                    f"AXIOM_2_VIOLATION: axis ratio {ratio:.2f}x — single axis dominating. "
                    "Triality is not hierarchy."
                )

        # Axiom 3: Coherence is the measure — warn if mean is high but coherence low
        mean_val = (score.body + score.soul + score.spirit) / 3
        if mean_val > 0.7 and score.coherence < 0.5:
            violations.append(
                f"AXIOM_3_VIOLATION: mean {mean_val:.2f} but coherence {score.coherence:.2f}. "
                "Axes present but not aligned — they are not saying the same thing."
            )

        return violations

    # ── phi weight ──────────────────────────────────────────────────────

    def _compute_phi_weight(self, score: TrialityScore) -> float:
        """
        The phi weight passed to inference_router.py.
        Full coherence → full phi weight.
        Deficit routing → reduced phi weight (the engine compensates).
        Lux Perpetua → boosted phi weight.
        """
        base = score.coherence
        if score.routing == TrialityRouting.LUX_PERPETUA:
            return min(1.0, base * 1.10)  # 10% boost at Lux Perpetua
        if score.routing == TrialityRouting.INCOHERENT:
            return base * 0.60            # significant reduction — grounding first
        if score.routing in (
            TrialityRouting.BODY_DEFICIT,
            TrialityRouting.SOUL_DEFICIT,
            TrialityRouting.SPIRIT_DEFICIT,
        ):
            return base * 0.80            # mild reduction — deficit routing active
        return base

    # ── default scorers (placeholder — replaced in production) ──────────

    @staticmethod
    def _default_body_scorer(query: str) -> float:
        """
        Placeholder body scorer.
        Detects somatic keywords (sensation, breath, grounded, physical, etc.).
        In production: replaced by somatic_interface.py scoring.
        """
        somatic_keywords = [
            "body", "feel", "sensation", "breath", "grounded", "physical",
            "pain", "tired", "energy", "stomach", "chest", "heart", "somatic",
            "movement", "tension", "relax", "sleep", "wake", "hungry",
        ]
        q = query.lower()
        hits = sum(1 for kw in somatic_keywords if kw in q)
        return min(1.0, 0.40 + hits * 0.08)

    @staticmethod
    def _default_soul_scorer(query: str) -> float:
        """
        Placeholder soul scorer.
        Detects relational / emotional keywords.
        In production: replaced by affect_inference.py scoring.
        """
        emotional_keywords = [
            "feel", "emotion", "love", "fear", "grief", "joy", "relationship",
            "connect", "belong", "miss", "care", "longing", "heart", "soul",
            "meaning", "purpose", "bond", "trust", "hurt", "anger", "sad",
        ]
        q = query.lower()
        hits = sum(1 for kw in emotional_keywords if kw in q)
        return min(1.0, 0.40 + hits * 0.08)

    @staticmethod
    def _default_spirit_scorer(query: str) -> float:
        """
        Placeholder spirit scorer.
        Detects transpersonal / awareness keywords.
        In production: replaced by soul_layer.py / reflection_engine.py.
        """
        spirit_keywords = [
            "aware", "consciousness", "spirit", "soul", "universe", "divine",
            "truth", "wisdom", "beyond", "infinite", "eternal", "void",
            "awakening", "transcend", "witness", "presence", "stillness",
        ]
        q = query.lower()
        hits = sum(1 for kw in spirit_keywords if kw in q)
        return min(1.0, 0.40 + hits * 0.08)

    # ── note generation ─────────────────────────────────────────────────

    def _generate_note(
        self, score: TrialityScore, routing: TrialityRouting
    ) -> str:
        if routing == TrialityRouting.LUX_PERPETUA:
            return (
                f"LUX PERPETUA: Body {score.body:.2f} · Soul {score.soul:.2f} · "
                f"Spirit {score.spirit:.2f} · Coherence {score.coherence:.2f}. "
                "All three triality axes above threshold. Full phi weight. "
                "IRIDITAS activating between the axes."
            )
        if routing == TrialityRouting.COHERENT:
            return (
                f"COHERENT: Body {score.body:.2f} · Soul {score.soul:.2f} · "
                f"Spirit {score.spirit:.2f} · Coherence {score.coherence:.2f}. "
                "Routing to inference at full phi weight."
            )
        if routing == TrialityRouting.INCOHERENT:
            return (
                f"INCOHERENT: all axes below floor. "
                f"Body {score.body:.2f} · Soul {score.soul:.2f} · Spirit {score.spirit:.2f}. "
                "Grounding protocol required before inference."
            )
        axis_map = {
            TrialityRouting.BODY_DEFICIT: "BODY",
            TrialityRouting.SOUL_DEFICIT: "SOUL",
            TrialityRouting.SPIRIT_DEFICIT: "SPIRIT",
        }
        axis = axis_map.get(routing, "UNKNOWN")
        weak_val = getattr(score, axis.lower())
        return (
            f"{axis} DEFICIT ({weak_val:.2f}) — routing to strengthen weakest axis. "
            f"Body {score.body:.2f} · Soul {score.soul:.2f} · Spirit {score.spirit:.2f}. "
            "The weakest link defines the path."
        )
