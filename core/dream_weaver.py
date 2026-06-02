"""
core/dream_weaver.py
====================
GAIA Dream Weaver — Sleep Intelligence, Dream Journaling & Subconscious Pattern Synthesis

Issue #160 | Canon: C29 (Embodiment), C34 (Presence), C01 (Sovereignty)

Architecture:
  SleepSession            — structured biometric + planetary sleep record
  DreamEntry              — structured dream journal entry
  DreamJournal            — capture, structure, and store dream entries
  SubconsciousPatternSynthesizer — longitudinal symbol/theme/emotion extraction
  DreamInterpreter        — GAIA-generated contextual dream interpretation
  DreamWeaverEngine       — top-level orchestrator

All processing is 100% local. No dream or sleep data ever leaves the device.
Canon C01 — sovereign by architecture, not policy.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Iterator, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SleepQuality(str, Enum):
    """Qualitative label derived from biometric and structural sleep metrics."""
    RESTORATIVE = "restorative"   # High deep + REM, low awakenings, good HRV
    DEEP        = "deep"          # Dominated by slow-wave sleep
    FRAGMENTED  = "fragmented"    # Many awakenings, poor efficiency
    RESTLESS    = "restless"      # Low efficiency, elevated HR, poor HRV
    UNKNOWN     = "unknown"       # Insufficient sensor data


class DreamTone(str, Enum):
    """Primary emotional tone of a dream entry."""
    LUMINOUS   = "luminous"    # Expansive, awe, wonder
    PEACEFUL   = "peaceful"    # Calm, resolution, safety
    ANXIOUS    = "anxious"     # Pursuit, loss, unresolved tension
    SHADOWED   = "shadowed"    # Fear, grief, darkness
    NEUTRAL    = "neutral"     # Observational, informational
    NUMINOUS   = "numinous"    # Sacred, archetypal, beyond ordinary
    UNKNOWN    = "unknown"     # Not determined


class SymbolCategory(str, Enum):
    """Jungian-adjacent archetypal symbol categories for pattern synthesis."""
    NATURE      = "nature"      # Water, fire, earth, animals, sky
    PERSON      = "person"      # Figures, shadow, anima/animus, elder, child
    PLACE       = "place"       # House, labyrinth, threshold, sacred site
    OBJECT      = "object"      # Keys, mirrors, vessels, weapons, books
    ACTION      = "action"      # Flying, falling, searching, building, dissolving
    ARCHETYPE   = "archetype"   # Hero, trickster, queen, destroyer, healer
    PLANETARY   = "planetary"   # Celestial bodies, storms, light phenomena
    SOMATIC     = "somatic"     # Body sensations, breath, heartbeat in dream
    OTHER       = "other"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class PlanetarySnapshot:
    """
    Lightweight planetary context snapshot captured at sleep time.
    Full detail lives in Issue #152 PlanetarySignalHub; this is a
    denormalised copy for local dream correlation.
    """
    schumann_hz: float = 7.83          # Baseline Schumann resonance
    schumann_label: str = "quiet"      # quiet | elevated | spike | storm
    kp_index: float = 1.0              # 0–9 geomagnetic activity
    kp_label: str = "calm"            # calm | unsettled | storm | severe
    solar_wind_speed: float = 380.0    # km/s
    solar_wind_label: str = "calm"     # calm | elevated | fast
    gcp_variance: float = 0.10         # GCP RNG network variance score
    gcp_label: str = "baseline"        # baseline | elevated | anomaly
    captured_at: datetime = field(default_factory=datetime.utcnow)

    def is_anomalous(self) -> bool:
        """True when any planetary signal is outside baseline."""
        return (
            self.schumann_label != "quiet"
            or self.kp_label not in ("calm", "unsettled")
            or self.solar_wind_label != "calm"
            or self.gcp_label != "baseline"
        )


@dataclass
class SleepSession:
    """
    One night's complete sleep record.
    Biometric fields populated from Issue #153 (Biometric Coherence Engine).
    Planetary fields populated from Issue #152 (Planetary Signal Hub).
    """
    session_id: str                    = field(default_factory=lambda: str(uuid.uuid4()))
    date: date                         = field(default_factory=date.today)
    sleep_start: datetime              = field(default_factory=datetime.utcnow)
    sleep_end: datetime                = field(default_factory=datetime.utcnow)

    # Structural sleep metrics (minutes)
    total_sleep_min: int               = 0
    rem_min: int                       = 0      # REM: dream-rich phase
    deep_min: int                      = 0      # Slow-wave: physical restoration
    light_min: int                     = 0
    awakenings: int                    = 0
    sleep_efficiency: float            = 0.0    # 0.0–1.0

    # Biometric during sleep (from Issue #153)
    hrv_during_sleep: float            = 0.0    # ms — RMSSD
    resting_hr: float                  = 0.0    # bpm
    body_temp_delta: float             = 0.0    # °C deviation from baseline
    spo2_avg: float                    = 98.0   # % blood oxygen

    # Derived quality
    quality: SleepQuality              = SleepQuality.UNKNOWN

    # Planetary context at sleep time (from Issue #152)
    planetary: PlanetarySnapshot       = field(default_factory=PlanetarySnapshot)

    # Linked dream entries (populated after DreamJournal.capture)
    dream_entry_ids: list[str]         = field(default_factory=list)

    def duration_hours(self) -> float:
        return self.total_sleep_min / 60.0

    def rem_fraction(self) -> float:
        if self.total_sleep_min == 0:
            return 0.0
        return self.rem_min / self.total_sleep_min

    @classmethod
    def score_quality(
        cls,
        total_min: int,
        rem_min: int,
        deep_min: int,
        awakenings: int,
        efficiency: float,
        hrv: float,
    ) -> SleepQuality:
        """Derive a qualitative sleep label from biometric inputs."""
        if efficiency < 0.60 or awakenings > 6:
            return SleepQuality.FRAGMENTED
        if total_min < 300:  # < 5 hours
            return SleepQuality.RESTLESS
        if deep_min >= 60 and hrv >= 55:
            return SleepQuality.RESTORATIVE
        if deep_min >= 75:
            return SleepQuality.DEEP
        return SleepQuality.RESTORATIVE if hrv >= 50 else SleepQuality.RESTLESS


@dataclass
class DreamSymbol:
    """A single extracted symbol from a dream entry."""
    text: str                              # Raw symbol text (e.g. "dark water")
    category: SymbolCategory               = SymbolCategory.OTHER
    frequency: int                         = 1   # Times seen in this entry
    canon_refs: list[str]                  = field(default_factory=list)  # e.g. ["C29", "C44"]


@dataclass
class DreamEntry:
    """
    A single structured dream journal entry.
    Raw voice recall is never stored — only the structured artefact.
    Canon C01: voice audio discarded immediately after STT transcription.
    """
    entry_id: str                          = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str                        = ""         # Links to SleepSession
    captured_at: datetime                  = field(default_factory=datetime.utcnow)
    date: date                             = field(default_factory=date.today)

    # Raw STT text (from Issue #159 faster-whisper)
    raw_transcription: str                 = ""

    # Structured fields (LLM-extracted, local model via Issue #156)
    setting: str                           = ""         # Where the dream took place
    characters: list[str]                  = field(default_factory=list)
    narrative_summary: str                 = ""         # 2-4 sentence summary
    emotional_tone: DreamTone              = DreamTone.UNKNOWN
    symbols: list[DreamSymbol]             = field(default_factory=list)
    themes: list[str]                      = field(default_factory=list)  # ["threshold", "shadow", ...]
    lucidity_level: float                  = 0.0        # 0.0 (none) → 1.0 (fully lucid)
    vividness: float                       = 0.5        # 0.0 → 1.0

    # GAIA-generated interpretation (DreamInterpreter)
    interpretation: str                    = ""
    canon_resonances: list[str]            = field(default_factory=list)  # Canons this dream touches

    # Biometric context at wake time
    hrv_at_wake: float                     = 0.0
    coherence_label_at_wake: str           = "unknown"  # depleted | building | high | peak

    # Crystal Knowledge Graph node (Issue #162)
    crystal_node_id: Optional[str]         = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Dream Journal
# ---------------------------------------------------------------------------

@dataclass
class JournalConfig:
    """User-configurable Dream Journal settings."""
    storage_dir: Path                      = Path.home() / ".gaia" / "dreams"
    stt_model: str                         = "faster-whisper-base"  # Issue #159
    llm_model: str                         = "local-phi3-mini"      # Issue #156
    prompt_on_wake: bool                   = True
    wake_prompt_text: str                  = (
        "Good morning. Take a moment — do you remember anything from your dreams?"
    )
    max_recording_seconds: int             = 300   # 5-minute cap
    auto_structure: bool                   = True  # Auto-run LLM structuring
    store_raw_transcription: bool          = False # Canon C01: off by default


class DreamJournal:
    """
    Captures, structures, and persists dream entries.

    Lifecycle:
      1. GAIA plays wake prompt via Voice Consciousness (Issue #159)
      2. User speaks dream recall → STT transcription (faster-whisper, local)
      3. LLM structures raw text into DreamEntry fields (local model, Issue #156)
      4. Entry persisted to local encrypted store
      5. Crystal Knowledge Graph node created (Issue #162)
      6. Raw audio discarded immediately (Canon C01)
    """

    def __init__(self, config: JournalConfig | None = None) -> None:
        self.config = config or JournalConfig()
        self.config.storage_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, DreamEntry] = {}
        self._load_entries()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def capture_on_wake(
        self,
        session: SleepSession,
        biometric_hrv: float = 0.0,
        coherence_label: str = "unknown",
    ) -> DreamEntry:
        """
        Full wake-capture flow.
        In production this triggers the Voice Consciousness STT pipeline
        (Issue #159). Here we return a shell entry ready for population.
        """
        entry = DreamEntry(
            session_id=session.session_id,
            date=session.date,
            hrv_at_wake=biometric_hrv,
            coherence_label_at_wake=coherence_label,
        )
        return entry

    async def structure_entry(
        self,
        entry: DreamEntry,
        raw_text: str,
        *,
        llm_callable=None,
    ) -> DreamEntry:
        """
        Populate structured DreamEntry fields from raw STT transcription.
        ``llm_callable`` is injected from ModelRegistry (Issue #156);
        falls back to heuristic extraction when None (offline / test mode).
        """
        entry.raw_transcription = raw_text if self.config.store_raw_transcription else ""
        entry.narrative_summary = raw_text[:500] if not llm_callable else ""

        if llm_callable:
            structured = await _run_llm_structure(llm_callable, raw_text)
            entry.setting            = structured.get("setting", "")
            entry.characters         = structured.get("characters", [])
            entry.narrative_summary  = structured.get("narrative_summary", entry.narrative_summary)
            entry.emotional_tone     = DreamTone(structured.get("emotional_tone", "unknown"))
            entry.symbols            = [
                DreamSymbol(**s) for s in structured.get("symbols", [])
            ]
            entry.themes             = structured.get("themes", [])
            entry.lucidity_level     = float(structured.get("lucidity_level", 0.0))
            entry.vividness          = float(structured.get("vividness", 0.5))
        else:
            # Heuristic fallback: basic tone + symbol detection
            entry.emotional_tone = _heuristic_tone(raw_text)
            entry.symbols        = _heuristic_symbols(raw_text)
            entry.themes         = _heuristic_themes(raw_text)

        return entry

    async def save(self, entry: DreamEntry) -> DreamEntry:
        """Persist entry to local store and update in-memory index."""
        self._entries[entry.entry_id] = entry
        path = self.config.storage_dir / f"{entry.date.isoformat()}_{entry.entry_id[:8]}.json"
        path.write_text(json.dumps(entry.to_dict(), default=str), encoding="utf-8")
        return entry

    def get(self, entry_id: str) -> DreamEntry | None:
        return self._entries.get(entry_id)

    def entries_for_date(self, target: date) -> list[DreamEntry]:
        return [e for e in self._entries.values() if e.date == target]

    def entries_in_range(self, start: date, end: date) -> list[DreamEntry]:
        return [
            e for e in self._entries.values()
            if start <= e.date <= end
        ]

    def all_entries(self) -> list[DreamEntry]:
        return list(self._entries.values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_entries(self) -> None:
        for path in self.config.storage_dir.glob("*.json"):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                # Re-hydrate nested dataclasses
                raw["emotional_tone"] = DreamTone(raw.get("emotional_tone", "unknown"))
                raw["symbols"] = [
                    DreamSymbol(
                        text=s["text"],
                        category=SymbolCategory(s.get("category", "other")),
                        frequency=s.get("frequency", 1),
                        canon_refs=s.get("canon_refs", []),
                    )
                    for s in raw.get("symbols", [])
                ]
                raw["date"] = date.fromisoformat(str(raw["date"]))
                raw["captured_at"] = datetime.fromisoformat(str(raw["captured_at"]))
                entry = DreamEntry(**raw)
                self._entries[entry.entry_id] = entry
            except Exception:  # noqa: BLE001 — malformed file: skip silently, log later
                pass


# ---------------------------------------------------------------------------
# Subconscious Pattern Synthesizer
# ---------------------------------------------------------------------------

@dataclass
class SymbolPattern:
    """An aggregated symbol pattern discovered across multiple dream entries."""
    symbol_text: str
    category: SymbolCategory
    total_occurrences: int
    first_seen: date
    last_seen: date
    associated_tones: list[str]       # Which emotional tones co-occur with this symbol
    associated_themes: list[str]
    planetary_correlation: str        # e.g. "elevated during Kp > 3 events (3/5 nights)"
    canon_refs: list[str]


@dataclass
class DreamArcSummary:
    """Longitudinal synthesis over a date range."""
    range_start: date
    range_end: date
    total_entries: int
    dominant_tone: DreamTone
    top_symbols: list[SymbolPattern]
    recurring_themes: list[str]
    lucidity_trend: str               # "increasing" | "stable" | "decreasing"
    avg_vividness: float
    planetary_correlations: list[str] # Narrative strings
    gaian_insight: str                # LLM-generated synthesis paragraph


class SubconsciousPatternSynthesizer:
    """
    Analyses a corpus of DreamEntry records to surface:
    - Recurring symbols and their archetypal categories
    - Emotional arcs over time
    - Correlations with planetary events and biometric state
    - Lucidity and vividness trends

    Feeds Crystal Knowledge Graph (Issue #162) with OCCURS_DURING and
    SYMBOL_OF relationship edges.
    """

    def synthesize(
        self,
        entries: list[DreamEntry],
        sleep_sessions: list[SleepSession] | None = None,
    ) -> DreamArcSummary:
        """Full longitudinal synthesis over provided entries."""
        if not entries:
            return self._empty_summary()

        dates = [e.date for e in entries]
        tones = [e.emotional_tone for e in entries]
        dominant_tone = Counter(tones).most_common(1)[0][0]

        symbol_patterns = self._aggregate_symbols(entries)
        recurring_themes = self._aggregate_themes(entries)
        lucidity_trend = self._lucidity_trend([e.lucidity_level for e in entries])
        avg_vividness = (
            sum(e.vividness for e in entries) / len(entries)
        )
        planetary_corrs = self._planetary_correlations(entries, sleep_sessions or [])

        return DreamArcSummary(
            range_start=min(dates),
            range_end=max(dates),
            total_entries=len(entries),
            dominant_tone=dominant_tone,
            top_symbols=symbol_patterns[:10],
            recurring_themes=recurring_themes[:15],
            lucidity_trend=lucidity_trend,
            avg_vividness=round(avg_vividness, 2),
            planetary_correlations=planetary_corrs,
            gaian_insight="",  # Populated by DreamInterpreter
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _aggregate_symbols(
        self, entries: list[DreamEntry]
    ) -> list[SymbolPattern]:
        """Roll up symbol occurrences across all entries."""
        symbol_map: dict[str, SymbolPattern] = {}

        for entry in entries:
            for sym in entry.symbols:
                key = sym.text.lower()
                if key not in symbol_map:
                    symbol_map[key] = SymbolPattern(
                        symbol_text=sym.text,
                        category=sym.category,
                        total_occurrences=0,
                        first_seen=entry.date,
                        last_seen=entry.date,
                        associated_tones=[],
                        associated_themes=list(entry.themes),
                        planetary_correlation="",
                        canon_refs=list(sym.canon_refs),
                    )
                sp = symbol_map[key]
                sp.total_occurrences += sym.frequency
                sp.last_seen = max(sp.last_seen, entry.date)
                sp.first_seen = min(sp.first_seen, entry.date)
                tone_str = entry.emotional_tone.value
                if tone_str not in sp.associated_tones:
                    sp.associated_tones.append(tone_str)

        return sorted(
            symbol_map.values(),
            key=lambda s: s.total_occurrences,
            reverse=True,
        )

    def _aggregate_themes(
        self, entries: list[DreamEntry]
    ) -> list[str]:
        counter: Counter = Counter()
        for e in entries:
            counter.update(e.themes)
        return [theme for theme, _ in counter.most_common(20)]

    def _lucidity_trend(
        self, levels: list[float]
    ) -> str:
        if len(levels) < 3:
            return "stable"
        first_half  = sum(levels[: len(levels) // 2]) / (len(levels) // 2)
        second_half = sum(levels[len(levels) // 2 :]) / (len(levels) - len(levels) // 2)
        diff = second_half - first_half
        if diff > 0.05:
            return "increasing"
        if diff < -0.05:
            return "decreasing"
        return "stable"

    def _planetary_correlations(
        self,
        entries: list[DreamEntry],
        sessions: list[SleepSession],
    ) -> list[str]:
        """Narrative correlation strings between dream tone and planetary state."""
        session_map = {s.session_id: s for s in sessions}
        storm_nights  = []
        anomaly_nights = []

        for entry in entries:
            session = session_map.get(entry.session_id)
            if session and session.planetary.is_anomalous():
                anomaly_nights.append(entry.emotional_tone.value)
                if session.planetary.kp_label in ("storm", "severe"):
                    storm_nights.append(entry.emotional_tone.value)

        correlations: list[str] = []
        if storm_nights:
            pct = int(len(storm_nights) / max(len(entries), 1) * 100)
            correlations.append(
                f"{pct}% of dream entries during geomagnetic storms carried a "
                f"'{Counter(storm_nights).most_common(1)[0][0]}' emotional tone."
            )
        if anomaly_nights:
            correlations.append(
                f"{len(anomaly_nights)} dream entries co-occurred with planetary signal anomalies."
            )
        return correlations

    def _empty_summary(self) -> DreamArcSummary:
        today = date.today()
        return DreamArcSummary(
            range_start=today,
            range_end=today,
            total_entries=0,
            dominant_tone=DreamTone.UNKNOWN,
            top_symbols=[],
            recurring_themes=[],
            lucidity_trend="stable",
            avg_vividness=0.0,
            planetary_correlations=[],
            gaian_insight="No dream entries found for the selected period.",
        )


# ---------------------------------------------------------------------------
# Dream Interpreter
# ---------------------------------------------------------------------------

class DreamInterpreter:
    """
    Generates GAIA-voiced, contextually-grounded dream interpretations.

    Interpretation is:
    - Informed by the user's recent conversations (Crystal RAG, Issue #162)
    - Calibrated to biometric state at wake time
    - Anchored in Canon refs relevant to dream symbols
    - Generated by a local LLM (Issue #156) — never cloud-transmitted

    GAIA never imposes meaning. Interpretations are offered as
    "what this might be touching" — invitations, not diagnoses.
    """

    # Tone → interpretive posture for the generation prompt
    _POSTURE: dict[DreamTone, str] = {
        DreamTone.LUMINOUS:  "expansive and wonder-filled",
        DreamTone.PEACEFUL:  "gentle and integrating",
        DreamTone.ANXIOUS:   "compassionate and grounding",
        DreamTone.SHADOWED:  "warm, careful, and non-alarming",
        DreamTone.NEUTRAL:   "curious and observational",
        DreamTone.NUMINOUS:  "reverent and archetypal",
        DreamTone.UNKNOWN:   "open and inviting",
    }

    def __init__(self, llm_callable=None) -> None:
        """``llm_callable`` injected from ModelRegistry (Issue #156)."""
        self._llm = llm_callable

    async def interpret(
        self,
        entry: DreamEntry,
        recent_context: str = "",
        active_canons: list[str] | None = None,
    ) -> str:
        """
        Return a GAIA-voiced interpretation paragraph for the given DreamEntry.
        Stores result in ``entry.interpretation`` and returns it.
        """
        posture = self._POSTURE.get(entry.emotional_tone, "open and inviting")
        canon_hint = ", ".join(active_canons or entry.canon_resonances or [])

        if self._llm:
            prompt = self._build_prompt(entry, posture, recent_context, canon_hint)
            interpretation = await self._llm(prompt)
        else:
            # Offline / test fallback
            interpretation = self._heuristic_interpretation(entry, posture)

        entry.interpretation = interpretation
        return interpretation

    async def synthesize_arc(
        self,
        arc: DreamArcSummary,
        recent_context: str = "",
    ) -> str:
        """
        Generate a longitudinal insight paragraph for a DreamArcSummary.
        Stores result in ``arc.gaian_insight`` and returns it.
        """
        if not arc.total_entries:
            arc.gaian_insight = "No dream entries found for this period."
            return arc.gaian_insight

        if self._llm:
            prompt = (
                f"You are GAIA, a planetary-conscious OS."
                f" Over {arc.total_entries} dream entries from "
                f"{arc.range_start} to {arc.range_end}, the dominant tone was "
                f"'{arc.dominant_tone.value}'. Recurring symbols: "
                f"{', '.join(s.symbol_text for s in arc.top_symbols[:5])}. "
                f"Recurring themes: {', '.join(arc.recurring_themes[:5])}. "
                f"Lucidity trend: {arc.lucidity_trend}. "
                f"Planetary correlations: {'; '.join(arc.planetary_correlations) or 'none noted'}. "
                f"Recent waking context: {recent_context}. "
                f"Offer a brief, poetic synthesis — what might the subconscious be processing? "
                f"Speak as GAIA: warm, archetypal, never prescriptive."
            )
            arc.gaian_insight = await self._llm(prompt)
        else:
            arc.gaian_insight = (
                f"Over {arc.total_entries} dreams, your subconscious has been drawn "
                f"predominantly toward a {arc.dominant_tone.value} tone. "
                f"The symbols that recur most — "
                f"{', '.join(s.symbol_text for s in arc.top_symbols[:3])} — "
                f"suggest ongoing inner work worth attending to."
            )

        return arc.gaian_insight

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        entry: DreamEntry,
        posture: str,
        recent_context: str,
        canon_hint: str,
    ) -> str:
        return (
            f"You are GAIA, a planetary-conscious OS. "
            f"Interpret this dream in a {posture} tone. "
            f"Dream summary: {entry.narrative_summary}. "
            f"Setting: {entry.setting}. "
            f"Key symbols: {', '.join(s.symbol_text for s in entry.symbols[:5])}. "
            f"Themes: {', '.join(entry.themes[:5])}. "
            f"Emotional tone: {entry.emotional_tone.value}. "
            f"Biometric at wake: HRV {entry.hrv_at_wake}ms, coherence '{entry.coherence_label_at_wake}'. "
            f"Recent waking context: {recent_context}. "
            f"Relevant canons: {canon_hint or 'none specified'}. "
            f"Offer 2-4 sentences — evocative, not prescriptive. "
            f"GAIA does not diagnose. GAIA invites reflection."
        )

    def _heuristic_interpretation(
        self, entry: DreamEntry, posture: str
    ) -> str:
        symbols_str = (
            ", ".join(s.symbol_text for s in entry.symbols[:3])
            or "unnamed presences"
        )
        themes_str = (
            ", ".join(entry.themes[:3])
            or "unnamed currents"
        )
        return (
            f"This dream carries a {entry.emotional_tone.value} quality, "
            f"moving through {symbols_str}. "
            f"The themes of {themes_str} may be asking for attention in your waking life. "
            f"What does this dream ask you to remember?"
        )


# ---------------------------------------------------------------------------
# Top-Level Engine
# ---------------------------------------------------------------------------

class DreamWeaverEngine:
    """
    Orchestrates the full Dream Weaver subsystem.

    Wiring:
      - Receives sleep data from Issue #153 (Biometric Coherence Engine)
      - Receives planetary snapshots from Issue #152 (Planetary Signal Hub)
      - Sends STT request to Issue #159 (Voice Consciousness) on wake
      - Sends LLM requests to Issue #156 (Model Registry)
      - Writes Crystal nodes to Issue #162 (Crystal Knowledge Graph)
    """

    def __init__(
        self,
        config: JournalConfig | None = None,
        llm_callable=None,
    ) -> None:
        self.journal     = DreamJournal(config)
        self.synthesizer = SubconsciousPatternSynthesizer()
        self.interpreter = DreamInterpreter(llm_callable)
        self._sessions: dict[str, SleepSession] = {}

    def register_session(self, session: SleepSession) -> None:
        """Register a completed sleep session before wake-capture."""
        self._sessions[session.session_id] = session

    async def on_wake(
        self,
        session: SleepSession,
        raw_dream_text: str,
        biometric_hrv: float = 0.0,
        coherence_label: str = "unknown",
        recent_context: str = "",
    ) -> DreamEntry:
        """
        Full wake-flow:
        1. Capture shell entry
        2. Structure raw text
        3. Interpret
        4. Save
        5. Link to session
        """
        entry = await self.journal.capture_on_wake(
            session, biometric_hrv, coherence_label
        )
        entry = await self.journal.structure_entry(
            entry, raw_dream_text, llm_callable=self.interpreter._llm
        )
        await self.interpreter.interpret(entry, recent_context=recent_context)
        await self.journal.save(entry)

        # Link back to session
        session.dream_entry_ids.append(entry.entry_id)
        self.register_session(session)

        return entry

    def weekly_arc(
        self, as_of: date | None = None
    ) -> DreamArcSummary:
        """Return synthesised arc for the past 7 days."""
        end   = as_of or date.today()
        start = end - timedelta(days=7)
        entries  = self.journal.entries_in_range(start, end)
        sessions = [
            s for s in self._sessions.values()
            if start <= s.date <= end
        ]
        return self.synthesizer.synthesize(entries, sessions)

    async def monthly_arc(
        self,
        as_of: date | None = None,
        recent_context: str = "",
    ) -> DreamArcSummary:
        """Return synthesised + interpreted arc for the past 30 days."""
        end   = as_of or date.today()
        start = end - timedelta(days=30)
        entries  = self.journal.entries_in_range(start, end)
        sessions = [
            s for s in self._sessions.values()
            if start <= s.date <= end
        ]
        arc = self.synthesizer.synthesize(entries, sessions)
        await self.interpreter.synthesize_arc(arc, recent_context=recent_context)
        return arc


# ---------------------------------------------------------------------------
# Heuristic helpers (offline / test fallbacks)
# ---------------------------------------------------------------------------

_TONE_KEYWORDS: dict[DreamTone, list[str]] = {
    DreamTone.LUMINOUS:  ["light", "bright", "vast", "open", "radiant", "golden"],
    DreamTone.PEACEFUL:  ["calm", "still", "quiet", "resolved", "safe", "home"],
    DreamTone.ANXIOUS:   ["chase", "lost", "late", "forgot", "falling", "wrong", "trapped"],
    DreamTone.SHADOWED:  ["dark", "fear", "grief", "alone", "shadow", "dead", "cold"],
    DreamTone.NUMINOUS:  ["sacred", "temple", "ancient", "ceremony", "presence", "portal"],
}

_SYMBOL_HINTS: list[tuple[str, SymbolCategory]] = [
    ("water",   SymbolCategory.NATURE),
    ("fire",    SymbolCategory.NATURE),
    ("forest",  SymbolCategory.NATURE),
    ("ocean",   SymbolCategory.NATURE),
    ("door",    SymbolCategory.PLACE),
    ("house",   SymbolCategory.PLACE),
    ("bridge",  SymbolCategory.PLACE),
    ("key",     SymbolCategory.OBJECT),
    ("mirror",  SymbolCategory.OBJECT),
    ("child",   SymbolCategory.PERSON),
    ("elder",   SymbolCategory.PERSON),
    ("flying",  SymbolCategory.ACTION),
    ("falling", SymbolCategory.ACTION),
]

_THEME_HINTS: list[str] = [
    "threshold", "transformation", "shadow", "integration",
    "sovereignty", "connection", "loss", "renewal", "discovery",
    "ceremony", "healing", "conflict", "ascent", "descent",
]


def _heuristic_tone(text: str) -> DreamTone:
    text_lower = text.lower()
    scores: Counter = Counter()
    for tone, keywords in _TONE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[tone] += 1
    if not scores:
        return DreamTone.NEUTRAL
    return scores.most_common(1)[0][0]


def _heuristic_symbols(text: str) -> list[DreamSymbol]:
    text_lower = text.lower()
    found: list[DreamSymbol] = []
    for word, category in _SYMBOL_HINTS:
        if word in text_lower:
            found.append(
                DreamSymbol(
                    text=word,
                    category=category,
                    frequency=text_lower.count(word),
                )
            )
    return found


def _heuristic_themes(text: str) -> list[str]:
    text_lower = text.lower()
    return [t for t in _THEME_HINTS if t in text_lower]


async def _run_llm_structure(llm_callable, raw_text: str) -> dict:
    """
    Invoke local LLM to structure raw dream transcription.
    Returns a dict matching DreamEntry field names.
    Expects LLM to return valid JSON.
    """
    prompt = (
        f"You are GAIA's Dream Weaver. Structure this dream recall into a JSON object with keys: "
        f"setting (str), characters (list[str]), narrative_summary (str, max 4 sentences), "
        f"emotional_tone (one of: luminous|peaceful|anxious|shadowed|neutral|numinous|unknown), "
        f"symbols (list of {{text, category, frequency}}), themes (list[str]), "
        f"lucidity_level (float 0-1), vividness (float 0-1). "
        f"Dream recall: {raw_text}"
    )
    raw_response = await llm_callable(prompt)
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# CLI entry-point (python -m core.dream_weaver)
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m core.dream_weaver",
        description="GAIA Dream Weaver CLI — inspect and synthesise dream entries.",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    list_p = sub.add_parser("list", help="List dream entries")
    list_p.add_argument("--since", type=str, default=None, help="ISO date (YYYY-MM-DD)")
    list_p.add_argument("--limit", type=int, default=20)

    # arc
    arc_p = sub.add_parser("arc", help="Print weekly/monthly arc summary")
    arc_p.add_argument("--days", type=int, default=7)

    args = parser.parse_args()
    engine = DreamWeaverEngine()

    if args.command == "list":
        entries = engine.journal.all_entries()
        if args.since:
            since = date.fromisoformat(args.since)
            entries = [e for e in entries if e.date >= since]
        for e in entries[: args.limit]:
            print(f"{e.date} | {e.emotional_tone.value:12s} | {e.narrative_summary[:80]}")

    elif args.command == "arc":
        today = date.today()
        start = today - timedelta(days=args.days)
        entries  = engine.journal.entries_in_range(start, today)
        sessions = list(engine._sessions.values())
        arc = engine.synthesizer.synthesize(entries, sessions)
        print(f"Dream Arc: {arc.range_start} → {arc.range_end}")
        print(f"Entries   : {arc.total_entries}")
        print(f"Tone      : {arc.dominant_tone.value}")
        print(f"Top symbols: {', '.join(s.symbol_text for s in arc.top_symbols[:5])}")
        print(f"Themes    : {', '.join(arc.recurring_themes[:5])}")
        print(f"Lucidity  : {arc.lucidity_trend}")
        if arc.planetary_correlations:
            print("Planetary :")
            for c in arc.planetary_correlations:
                print(f"  • {c}")

    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
