"""
core/rag/index.py

SQLite-backed vector index for GAIA-OS RAG pipeline.
Stores chunk text, provenance metadata, and embedding vectors.
Supports cosine similarity search over stored embeddings.

Schema:
    chunks table:
        chunk_id    TEXT PRIMARY KEY
        source      TEXT
        doc_title   TEXT
        section     TEXT
        chunk_index INTEGER
        char_start  INTEGER
        text        TEXT
        embedding   BLOB     -- JSON-serialized float list
        ingested_at TEXT

Zero external dependencies: uses stdlib sqlite3 only.

Changes in this revision
------------------------
* size()        -- alias for count(); required by RAGPipeline.status().
* add()         -- alias for add_chunks(); matches pipeline call-site.
* from_store()  -- classmethod to open a persistent db at the canonical
                   path resolved by IndexStore, creating the directory
                   and file on first use.
"""
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from .chunker import Chunk
from .embedder import FallbackEmbedder, cosine_similarity


DEFAULT_DB_PATH = ":memory:"


class VectorIndex:
    """
    Persistent or in-memory SQLite vector index.

    Args:
        db_path: Path to SQLite file, or ':memory:' for in-memory.
        embedder: Embedder instance (default: FallbackEmbedder).
    """

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        embedder: Optional[FallbackEmbedder] = None,
    ):
        self.db_path = db_path
        self.embedder = embedder or FallbackEmbedder()
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    # ------------------------------------------------------------------
    # Classmethod constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_store(cls, store: "IndexStore", embedder=None) -> "VectorIndex":  # type: ignore[name-defined]
        """
        Open (or create) a VectorIndex backed by the SQLite file at
        *store.db_path*, ensuring the parent directory exists first.

        This is the preferred constructor for production use; the default
        constructor with db_path=':memory:' remains the default for tests.
        """
        store.ensure_dir()
        return cls(db_path=str(store.db_path), embedder=embedder)

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id    TEXT PRIMARY KEY,
                    source      TEXT NOT NULL,
                    doc_title   TEXT,
                    section     TEXT,
                    chunk_index INTEGER,
                    char_start  INTEGER,
                    text        TEXT NOT NULL,
                    embedding   TEXT,
                    ingested_at TEXT NOT NULL
                )
            """)
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_source ON chunks(source)"
            )

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: List[Chunk]) -> int:
        """
        Add chunks to the index. Fits embedder vocabulary, then embeds + stores.
        Returns count of newly indexed chunks (skips duplicates by chunk_id).
        """
        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        self.embedder.fit(texts)

        now = datetime.now(timezone.utc).isoformat()
        added = 0
        with self._lock:
            for chunk in chunks:
                embedding = self.embedder.embed(chunk.text)
                try:
                    with self._conn:
                        self._conn.execute(
                            """
                            INSERT OR IGNORE INTO chunks
                                (chunk_id, source, doc_title, section, chunk_index,
                                 char_start, text, embedding, ingested_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                chunk.chunk_id,
                                chunk.source,
                                chunk.doc_title,
                                chunk.section,
                                chunk.chunk_index,
                                chunk.char_start,
                                chunk.text,
                                json.dumps(embedding),
                                now,
                            ),
                        )
                    added += 1
                except sqlite3.Error:
                    pass
        return added

    def add(self, chunks: List[Chunk], embedder=None) -> int:
        """
        Alias for add_chunks(), accepting an optional embedder override.
        This matches the call-site in RAGPipeline.ingest_canon().
        """
        if embedder is not None:
            # Temporarily swap embedder for this batch
            original = self.embedder
            self.embedder = embedder
            result = self.add_chunks(chunks)
            self.embedder = original
            return result
        return self.add_chunks(chunks)

    # ------------------------------------------------------------------
    # Read path
    # ------------------------------------------------------------------

    def search(
        self, query_text: str, top_k: int = 5
    ) -> List[Tuple[Chunk, float]]:
        """
        Dense vector search: embed query, compute cosine similarity vs all stored.
        Returns top_k (chunk, score) pairs sorted by score descending.
        """
        query_vec = self.embedder.embed(query_text)

        with self._lock:
            rows = self._conn.execute(
                "SELECT chunk_id, source, doc_title, section, chunk_index, char_start, text, embedding FROM chunks"
            ).fetchall()

        scored = []
        for row in rows:
            chunk_id, source, doc_title, section, chunk_index, char_start, text, emb_json = row
            if emb_json:
                stored_vec = json.loads(emb_json)
                if len(stored_vec) == len(query_vec):
                    score = cosine_similarity(query_vec, stored_vec)
                    chunk = Chunk(
                        text=text,
                        source=source,
                        doc_title=doc_title or "",
                        section=section or "intro",
                        chunk_index=chunk_index or 0,
                        char_start=char_start or 0,
                    )
                    scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def keyword_search(
        self, query_text: str, top_k: int = 5
    ) -> List[Tuple[Chunk, float]]:
        """
        Sparse keyword search using SQLite LIKE.
        Returns (chunk, 1.0) for any chunk containing any query token.
        """
        tokens = query_text.lower().split()
        if not tokens:
            return []

        like_clauses = " OR ".join(["LOWER(text) LIKE ?" for _ in tokens])
        params = [f"%{tok}%" for tok in tokens]

        with self._lock:
            rows = self._conn.execute(
                f"SELECT chunk_id, source, doc_title, section, chunk_index, char_start, text FROM chunks WHERE {like_clauses} LIMIT ?",
                params + [top_k * 2],
            ).fetchall()

        results = []
        for row in rows:
            chunk_id, source, doc_title, section, chunk_index, char_start, text = row
            chunk = Chunk(
                text=text,
                source=source,
                doc_title=doc_title or "",
                section=section or "intro",
                chunk_index=chunk_index or 0,
                char_start=char_start or 0,
            )
            results.append((chunk, 1.0))

        return results[:top_k]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
            return row[0] if row else 0

    def size(self) -> int:
        """Alias for count(). Required by RAGPipeline.status()."""
        return self.count()

    def sources(self) -> List[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT DISTINCT source FROM chunks ORDER BY source"
            ).fetchall()
            return [r[0] for r in rows]

    def delete_source(self, source: str) -> int:
        """Remove all chunks from a given source file. Returns count deleted."""
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM chunks WHERE source = ?", (source,)
            )
            self._conn.commit()
            return cur.rowcount

    def close(self) -> None:
        self._conn.close()
