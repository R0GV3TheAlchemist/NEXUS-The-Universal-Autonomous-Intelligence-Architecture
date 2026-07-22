# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Sovereign Memory — SovereignMemory Engine
# Phase E: All NotImplementedError stubs replaced with real, running code.
# SQLite-backed, consent-gated, Ledger-wired.
# Architecture: NEXUS_UNIVERSAL_OS.md Domain 2.1
# GAIAN Law II: Memory Sovereignty

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .consent import ConsentGate, ConsentScope

logger = logging.getLogger("sovereign_memory.engine")

_DEFAULT_DB = Path(os.environ.get("NEXUS_MEMORY_DB", "nexus_data/soul_mirror.db"))


# ---------------------------------------------------------------------------
# Data types (kept compatible with existing types.py contracts)
# ---------------------------------------------------------------------------

@dataclass
class EpisodicRecord:
    """A single episodic memory entry."""
    record_id: str
    timestamp: str
    content: str
    affect_tag: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(cls, content: str, affect_tag: str | None = None, **meta: Any) -> "EpisodicRecord":
        return cls(
            record_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            content=content,
            affect_tag=affect_tag,
            metadata=meta,
        )


@dataclass
class SemanticFact:
    """A persistent semantic fact node."""
    fact_id: str
    subject: str
    predicate: str
    obj: str
    confidence: float = 1.0

    @classmethod
    def new(cls, subject: str, predicate: str, obj: str, confidence: float = 1.0) -> "SemanticFact":
        return cls(
            fact_id=str(uuid.uuid4()),
            subject=subject,
            predicate=predicate,
            obj=obj,
            confidence=confidence,
        )


@dataclass
class BiometricSnapshot:
    """A biometric signal snapshot."""
    snapshot_id: str
    timestamp: str
    heart_rate: Optional[float] = None
    hrv: Optional[float] = None
    skin_conductance: Optional[float] = None

    @classmethod
    def new(
        cls,
        heart_rate: float | None = None,
        hrv: float | None = None,
        skin_conductance: float | None = None,
    ) -> "BiometricSnapshot":
        return cls(
            snapshot_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            heart_rate=heart_rate,
            hrv=hrv,
            skin_conductance=skin_conductance,
        )


# ---------------------------------------------------------------------------
# SovereignMemory — Phase E: fully implemented
# ---------------------------------------------------------------------------

class SovereignMemory:
    """
    Local-first persistent memory for NEXUS / GAIA-OS.

    Every operation passes through the ConsentGate before touching SQLite.
    Every write is echoed to the Planetary Ledger as a 'memory_commit' event.

    Architecture: NEXUS_UNIVERSAL_OS.md Domain 2.1
    GAIAN Law II: Memory Sovereignty

    Usage::

        mem = SovereignMemory()
        mem.open()
        rec = EpisodicRecord.new("NEXUS Phase E began", affect_tag="focused")
        mem.store_episodic(rec)
        recent = mem.retrieve_episodic(limit=10)
        mem.close()
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        consent_gate: ConsentGate | None = None,
        ledger: Any | None = None,
        session_id: str | None = None,
    ) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._gate = consent_gate or ConsentGate()
        self._ledger = ledger
        self._session_id = session_id
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()
        logger.info("SovereignMemory created (db=%s)", self._db_path)

    # ── Lifecycle ──────────────────────────────────────────────────────

    def open(self) -> None:
        """Open SQLite connection and initialise schema."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_schema()
        logger.info("SovereignMemory opened (db=%s)", self._db_path)

    def close(self) -> None:
        """Flush and close the database connection."""
        with self._lock:
            if self._conn:
                self._conn.commit()
                self._conn.close()
                self._conn = None
        logger.info("SovereignMemory closed")

    # ── Episodic Memory ────────────────────────────────────────────────

    def store_episodic(self, record: EpisodicRecord) -> None:
        """Persist an episodic memory record (consent required)."""
        self._gate.require(ConsentScope.EPISODIC_WRITE)
        with self._lock:
            self._get_conn().execute(
                "INSERT OR REPLACE INTO episodic_records "
                "(record_id, timestamp, content, affect_tag, metadata_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    record.record_id,
                    record.timestamp,
                    record.content,
                    record.affect_tag,
                    json.dumps(record.metadata),
                ),
            )
            self._get_conn().commit()
        self._ledger_write("episodic", {"record_id": record.record_id, "affect_tag": record.affect_tag})
        logger.debug("store_episodic record_id=%s", record.record_id)

    def retrieve_episodic(
        self,
        limit: int = 50,
        affect_tag: str | None = None,
    ) -> list[EpisodicRecord]:
        """Return recent episodic records (consent required)."""
        self._gate.require(ConsentScope.EPISODIC_READ)
        with self._lock:
            if affect_tag:
                rows = self._get_conn().execute(
                    "SELECT record_id, timestamp, content, affect_tag, metadata_json "
                    "FROM episodic_records WHERE affect_tag = ? ORDER BY timestamp DESC LIMIT ?",
                    (affect_tag, limit),
                ).fetchall()
            else:
                rows = self._get_conn().execute(
                    "SELECT record_id, timestamp, content, affect_tag, metadata_json "
                    "FROM episodic_records ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [
            EpisodicRecord(
                record_id=r[0],
                timestamp=r[1],
                content=r[2],
                affect_tag=r[3],
                metadata=json.loads(r[4]) if r[4] else {},
            )
            for r in rows
        ]

    def count_episodic(self) -> int:
        self._gate.require(ConsentScope.EPISODIC_READ)
        with self._lock:
            return self._get_conn().execute("SELECT COUNT(*) FROM episodic_records").fetchone()[0]

    # ── Semantic Memory ────────────────────────────────────────────────

    def store_fact(self, fact: SemanticFact) -> None:
        """Store or update a semantic fact (consent required)."""
        self._gate.require(ConsentScope.SEMANTIC_WRITE)
        with self._lock:
            self._get_conn().execute(
                "INSERT OR REPLACE INTO semantic_facts "
                "(fact_id, subject, predicate, obj, confidence) "
                "VALUES (?, ?, ?, ?, ?)",
                (fact.fact_id, fact.subject, fact.predicate, fact.obj, fact.confidence),
            )
            self._get_conn().commit()
        self._ledger_write("semantic", {"fact_id": fact.fact_id, "subject": fact.subject})
        logger.debug("store_fact fact_id=%s", fact.fact_id)

    def query_facts(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        limit: int = 100,
    ) -> list[SemanticFact]:
        """Query semantic facts (consent required)."""
        self._gate.require(ConsentScope.SEMANTIC_READ)
        with self._lock:
            clauses, params = [], []
            if subject:
                clauses.append("subject = ?")
                params.append(subject)
            if predicate:
                clauses.append("predicate = ?")
                params.append(predicate)
            where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
            params.append(limit)
            rows = self._get_conn().execute(
                f"SELECT fact_id, subject, predicate, obj, confidence "
                f"FROM semantic_facts {where} LIMIT ?",
                params,
            ).fetchall()
        return [
            SemanticFact(fact_id=r[0], subject=r[1], predicate=r[2], obj=r[3], confidence=r[4])
            for r in rows
        ]

    def count_facts(self) -> int:
        self._gate.require(ConsentScope.SEMANTIC_READ)
        with self._lock:
            return self._get_conn().execute("SELECT COUNT(*) FROM semantic_facts").fetchone()[0]

    # ── Biometric Memory ───────────────────────────────────────────────

    def store_biometric(self, snapshot: BiometricSnapshot) -> None:
        """Persist a biometric snapshot (consent required)."""
        self._gate.require(ConsentScope.BIOMETRIC_WRITE)
        with self._lock:
            self._get_conn().execute(
                "INSERT OR REPLACE INTO biometric_snapshots "
                "(snapshot_id, timestamp, heart_rate, hrv, skin_conductance) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    snapshot.snapshot_id,
                    snapshot.timestamp,
                    snapshot.heart_rate,
                    snapshot.hrv,
                    snapshot.skin_conductance,
                ),
            )
            self._get_conn().commit()
        self._ledger_write("biometric", {"snapshot_id": snapshot.snapshot_id})
        logger.debug("store_biometric snapshot_id=%s", snapshot.snapshot_id)

    def retrieve_biometric(self, limit: int = 20) -> list[BiometricSnapshot]:
        """Return recent biometric snapshots (consent required)."""
        self._gate.require(ConsentScope.BIOMETRIC_READ)
        with self._lock:
            rows = self._get_conn().execute(
                "SELECT snapshot_id, timestamp, heart_rate, hrv, skin_conductance "
                "FROM biometric_snapshots ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            BiometricSnapshot(
                snapshot_id=r[0],
                timestamp=r[1],
                heart_rate=r[2],
                hrv=r[3],
                skin_conductance=r[4],
            )
            for r in rows
        ]

    # ── Internal ───────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS episodic_records (
                record_id    TEXT PRIMARY KEY,
                timestamp    TEXT NOT NULL,
                content      TEXT NOT NULL,
                affect_tag   TEXT,
                metadata_json TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_episodic_timestamp
                ON episodic_records(timestamp);
            CREATE INDEX IF NOT EXISTS idx_episodic_affect
                ON episodic_records(affect_tag);

            CREATE TABLE IF NOT EXISTS semantic_facts (
                fact_id    TEXT PRIMARY KEY,
                subject    TEXT NOT NULL,
                predicate  TEXT NOT NULL,
                obj        TEXT NOT NULL,
                confidence REAL DEFAULT 1.0
            );
            CREATE INDEX IF NOT EXISTS idx_facts_subject
                ON semantic_facts(subject);

            CREATE TABLE IF NOT EXISTS biometric_snapshots (
                snapshot_id      TEXT PRIMARY KEY,
                timestamp        TEXT NOT NULL,
                heart_rate       REAL,
                hrv              REAL,
                skin_conductance REAL
            );
            CREATE INDEX IF NOT EXISTS idx_bio_timestamp
                ON biometric_snapshots(timestamp);
        """)
        conn.commit()

    def _ledger_write(self, memory_type: str, payload: dict[str, Any]) -> None:
        if self._ledger is None:
            return
        try:
            from planetary_ledger import EventType
            self._ledger.append(
                event_type=EventType.MEMORY_COMMIT,
                payload={"memory_type": memory_type, **payload},
                tags=["sovereign_memory", "phase-e"],
                session_id=self._session_id,
            )
        except Exception:
            logger.exception("SovereignMemory ledger write failed")

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("SovereignMemory is not open. Call open() first.")
        return self._conn
