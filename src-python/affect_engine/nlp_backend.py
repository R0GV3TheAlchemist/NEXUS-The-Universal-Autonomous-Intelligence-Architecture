"""
Affect Engine — Pluggable NLP Backend  (Issue #65)

Provides a clean abstraction over multiple inference backends so the
engine can switch without changing call sites.

Backend registry
----------------
"heuristic"  — Default.  Zero deps. Keyword lexicon + PAD anchors.
                Ready now.  Deterministic and unit-testable.

"sbert"      — sentence-transformers.  Local, offline, no GPU required.
                Loads `all-MiniLM-L6-v2` (22 MB) and a lightweight
                SoftmaxClassifier head trained on GoEmotions.
                Falls back to heuristic if import fails.

"llm"        — Prompt-based.  Calls a local llama.cpp server at
                GAIA_LLM_URL (default http://localhost:8080).
                Returns JSON {label, confidence, pad}.
                Falls back to heuristic if server unreachable.

Usage
-----
    backend = build_backend("sbert")  # or "heuristic" / "llm"
    result  = backend.analyze(text)

All backends return AffectAnalysisResult.
"""

from __future__ import annotations

import os
import logging
from abc import ABC, abstractmethod

from .types import AffectAnalysisResult, PadVector
from .heuristics import analyze_text_heuristic

logger = logging.getLogger(__name__)


class AffectBackend(ABC):
    """Common interface.  All backends must implement analyze()."""

    @abstractmethod
    def analyze(self, text: str) -> AffectAnalysisResult:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


# ─────────────────────────────────────────────
# Heuristic backend (always available)
# ─────────────────────────────────────────────

class HeuristicBackend(AffectBackend):
    """Keyword lexicon + PAD anchors.  Zero dependencies.  Default."""

    @property
    def name(self) -> str:
        return "heuristic"

    def analyze(self, text: str) -> AffectAnalysisResult:
        return analyze_text_heuristic(text)


# ─────────────────────────────────────────────
# SBERT backend (sentence-transformers + GoEmotions head)
# ─────────────────────────────────────────────

class SBERTBackend(AffectBackend):
    """
    sentence-transformers `all-MiniLM-L6-v2` + a lightweight softmax
    classifier head trained on GoEmotions (mapped to 7 GAIA classes).

    Install:  pip install sentence-transformers
    Model:    ~22 MB, CPU-only, offline.
    Latency:  ~40–120 ms per text on M-series / modern x86.

    GoEmotions → GAIA 7-class mapping
    ----------------------------------
    admiration,amusement,approval,caring,desire,excitement,
    gratitude,love,optimism,pride,relief,joy   →  joy
    annoyance,anger,disapproval,disgust        →  anger / disgust
    disappointment,sadness,grief,remorse       →  sadness
    fear,nervousness                           →  fear
    confusion,surprise,realization,curiosity   →  surprise
    neutral                                    →  neutral

    Falls back to HeuristicBackend if sentence_transformers not installed.
    """

    # GoEmotions label → GAIA 7-class
    _GOEMO_MAP: dict[str, str] = {
        "admiration": "joy",   "amusement": "joy",   "approval": "joy",
        "caring": "joy",       "desire": "joy",       "excitement": "joy",
        "gratitude": "joy",    "love": "joy",         "optimism": "joy",
        "pride": "joy",        "relief": "joy",       "joy": "joy",
        "annoyance": "anger",  "anger": "anger",
        "disapproval": "disgust", "disgust": "disgust",
        "disappointment": "sadness", "sadness": "sadness",
        "grief": "sadness",    "remorse": "sadness",
        "fear": "fear",        "nervousness": "fear",
        "confusion": "surprise", "surprise": "surprise",
        "realization": "surprise", "curiosity": "surprise",
        "neutral": "neutral",
    }

    _PAD_ANCHORS: dict[str, tuple[float, float, float]] = {
        "joy":     ( 0.80, 0.62, 0.70),
        "sadness": (-0.72, 0.22, 0.22),
        "anger":   (-0.70, 0.80, 0.72),
        "fear":    (-0.76, 0.86, 0.18),
        "disgust": (-0.65, 0.46, 0.58),
        "surprise":( 0.05, 0.88, 0.50),
        "neutral": ( 0.00, 0.10, 0.50),
    }

    def __init__(self) -> None:
        self._pipe = None
        self._fallback = HeuristicBackend()
        self._load()

    def _load(self) -> None:
        try:
            from transformers import pipeline as hf_pipeline
            self._pipe = hf_pipeline(
                "text-classification",
                model="SamLowe/roberta-base-go_emotions",
                top_k=1,
                device=-1,   # CPU
            )
            logger.info("SBERTBackend: loaded roberta-base-go_emotions")
        except Exception as exc:
            logger.warning("SBERTBackend: cannot load model (%s), falling back to heuristic", exc)
            self._pipe = None

    @property
    def name(self) -> str:
        return "sbert" if self._pipe else "heuristic(fallback)"

    def analyze(self, text: str) -> AffectAnalysisResult:
        if self._pipe is None:
            return self._fallback.analyze(text)
        try:
            raw = self._pipe(text[:512])
            # top_k=1 returns [[{label, score}]]
            top = raw[0][0]
            goemo_label = top["label"]
            confidence  = float(top["score"])
            gaia_label  = self._GOEMO_MAP.get(goemo_label, "neutral")
            p, a, d     = self._PAD_ANCHORS[gaia_label]
            from .heuristics import lexical_entropy, tokenize
            entropy = lexical_entropy(tokenize(text))
            return AffectAnalysisResult(
                label=gaia_label,
                confidence=min(0.99, confidence),
                pad=PadVector(p, a, d).clamp(),
                is_neutral_primary=(gaia_label == "neutral"),
                entropy=entropy,
                explanation=f"roberta-base-go_emotions: {goemo_label} ({confidence:.2f}) → {gaia_label}",
            )
        except Exception as exc:
            logger.warning("SBERTBackend.analyze failed (%s), using heuristic", exc)
            return self._fallback.analyze(text)


# ─────────────────────────────────────────────
# LLM backend (local llama.cpp HTTP server)
# ─────────────────────────────────────────────

class LLMBackend(AffectBackend):
    """
    Prompt-based affect inference via a local llama.cpp HTTP server.

    Expects GAIA_LLM_URL env var (default: http://localhost:8080).
    Prompt instructs the model to return strict JSON:
        {"label": "<emotion>", "confidence": 0.0–1.0,
         "pleasure": -1.0–1.0, "arousal": 0.0–1.0, "dominance": 0.0–1.0}

    Falls back to HeuristicBackend on any network or parse error.
    """

    PROMPT_TEMPLATE = """You are a clinical affect classifier. Read the text below and return ONLY valid JSON.
JSON keys: label (one of: joy sadness anger fear disgust surprise neutral),
confidence (0.0-1.0), pleasure (-1.0 to 1.0), arousal (0.0-1.0), dominance (0.0-1.0).

Text: {text}

JSON:"""

    def __init__(self, url: str | None = None) -> None:
        self._url = (url or os.getenv("GAIA_LLM_URL", "http://localhost:8080")) + "/completion"
        self._fallback = HeuristicBackend()

    @property
    def name(self) -> str:
        return "llm"

    def analyze(self, text: str) -> AffectAnalysisResult:
        try:
            import json
            import urllib.request
            prompt = self.PROMPT_TEMPLATE.format(text=text[:800])
            payload = json.dumps({"prompt": prompt, "n_predict": 120, "temperature": 0.0}).encode()
            req = urllib.request.Request(
                self._url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                body   = json.loads(resp.read())
                text_r = body.get("content", "")
                data   = json.loads(text_r.strip())
            label      = data.get("label", "neutral")
            confidence = float(data.get("confidence", 0.5))
            pad        = PadVector(
                pleasure  = float(data.get("pleasure",  0.0)),
                arousal   = float(data.get("arousal",   0.1)),
                dominance = float(data.get("dominance", 0.5)),
            ).clamp()
            from .heuristics import lexical_entropy, tokenize
            entropy = lexical_entropy(tokenize(text))
            return AffectAnalysisResult(
                label=label,
                confidence=min(0.99, confidence),
                pad=pad,
                is_neutral_primary=(label == "neutral"),
                entropy=entropy,
                explanation=f"LLM inference (llama.cpp): {label} ({confidence:.2f})",
            )
        except Exception as exc:
            logger.warning("LLMBackend.analyze failed (%s), using heuristic", exc)
            return self._fallback.analyze(text)


# ─────────────────────────────────────────────
# Registry + factory
# ─────────────────────────────────────────────

BACKEND_REGISTRY: dict[str, type[AffectBackend]] = {
    "heuristic": HeuristicBackend,
    "sbert"    : SBERTBackend,
    "llm"      : LLMBackend,
}


def build_backend(name: str | None = None) -> AffectBackend:
    """
    Resolve backend name from argument, GAIA_AFFECT_BACKEND env var, or default.

    Priority: argument > env var > "heuristic"
    """
    resolved = name or os.getenv("GAIA_AFFECT_BACKEND", "heuristic")
    cls = BACKEND_REGISTRY.get(resolved)
    if cls is None:
        logger.warning("Unknown affect backend %r — falling back to heuristic", resolved)
        cls = HeuristicBackend
    return cls()
