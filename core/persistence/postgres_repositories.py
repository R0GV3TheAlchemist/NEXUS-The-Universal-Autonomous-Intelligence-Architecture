"""Postgres-backed repository implementations for memory persistence.

This module provides concrete repository implementations for the interfaces in
`repositories.py` using psycopg2 and a threaded connection pool.
"""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any, Iterator, Sequence

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from .models import (
    Memory,
    MemoryStatus,
    MemoryType,
    SearchResult,
)
from .repositories import MemoryRepository, SearchRepository


class PostgresPool:
    """Small wrapper around a psycopg2 threaded connection pool."""

    def __init__(self, dsn: str, minconn: int = 1, maxconn: int = 10) -> None:
        self._pool = ThreadedConnectionPool(minconn=minconn, maxconn=maxconn, dsn=dsn)

    @contextmanager
    def connection(self):
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self) -> None:
        self._pool.closeall()


class PostgresMemoryRepository(MemoryRepository):
    """Postgres implementation of memory CRUD operations."""

    def __init__(self, pool: PostgresPool) -> None:
        self.pool = pool

    def create_memory(self, memory: Memory) -> Memory:
        memory_id = memory.id or str(uuid.uuid4())
        now = datetime.now(UTC)
        created_at = memory.created_at or now
        updated_at = memory.updated_at or now

        with self.pool.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO memories (
                        id,
                        user_id,
                        content,
                        memory_type,
                        metadata,
                        tags,
                        confidence,
                        source,
                        status,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id, user_id, content, memory_type, metadata, tags,
                              confidence, source, status, created_at, updated_at
                    """,
                    (
                        memory_id,
                        memory.user_id,
                        memory.content,
                        memory.memory_type.value,
                        Json(memory.metadata),
                        list(memory.tags),
                        memory.confidence,
                        memory.source,
                        memory.status.value,
                        created_at,
                        updated_at,
                    ),
                )
                row = cur.fetchone()
        return self._row_to_memory(row)

    def get_memory(self, memory_id: str) -> Memory | None:
        with self.pool.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, user_id, content, memory_type, metadata, tags,
                           confidence, source, status, created_at, updated_at
                    FROM memories
                    WHERE id = %s
                    """,
                    (memory_id,),
                )
                row = cur.fetchone()
        return self._row_to_memory(row) if row else None

    def update_memory(self, memory: Memory) -> Memory:
        if not memory.id:
            raise ValueError("memory.id is required for update")

        updated_at = datetime.now(UTC)
        with self.pool.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE memories
                    SET content = %s,
                        memory_type = %s,
                        metadata = %s,
                        tags = %s,
                        confidence = %s,
                        source = %s,
                        status = %s,
                        updated_at = %s
                    WHERE id = %s
                    RETURNING id, user_id, content, memory_type, metadata, tags,
                              confidence, source, status, created_at, updated_at
                    """,
                    (
                        memory.content,
                        memory.memory_type.value,
                        Json(memory.metadata),
                        list(memory.tags),
                        memory.confidence,
                        memory.source,
                        memory.status.value,
                        updated_at,
                        memory.id,
                    ),
                )
                row = cur.fetchone()
                if not row:
                    raise KeyError(f"memory not found: {memory.id}")
        return self._row_to_memory(row)

    def delete_memory(self, memory_id: str) -> bool:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
                return cur.rowcount > 0

    def list_memories(
        self,
        user_id: str,
        memory_type: MemoryType | None = None,
        status: MemoryStatus | None = None,
        tags: Sequence[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        clauses = ["user_id = %s"]
        params: list[Any] = [user_id]

        if memory_type:
            clauses.append("memory_type = %s")
            params.append(memory_type.value)
        if status:
            clauses.append("status = %s")
            params.append(status.value)
        if tags:
            clauses.append("tags @> %s")
            params.append(list(tags))

        params.extend([limit, offset])
        query = f"""
            SELECT id, user_id, content, memory_type, metadata, tags,
                   confidence, source, status, created_at, updated_at
            FROM memories
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """

        with self.pool.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
        return [self._row_to_memory(row) for row in rows]

    @staticmethod
    def _row_to_memory(row: dict[str, Any]) -> Memory:
        return Memory(
            id=str(row["id"]),
            user_id=row["user_id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            metadata=row.get("metadata") or {},
            tags=list(row.get("tags") or []),
            confidence=float(row["confidence"]),
            source=row["source"],
            status=MemoryStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class PostgresSearchRepository(SearchRepository):
    """Postgres implementation for recording search interactions and results."""

    def __init__(self, pool: PostgresPool) -> None:
        self.pool = pool

    def save_search_result(self, result: SearchResult) -> SearchResult:
        result_id = result.id or str(uuid.uuid4())
        now = datetime.now(UTC)
        created_at = result.created_at or now

        with self.pool.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO search_results (
                        id,
                        user_id,
                        query,
                        results,
                        total_found,
                        search_time_ms,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, query, results, total_found,
                              search_time_ms, created_at
                    """,
                    (
                        result_id,
                        result.user_id,
                        result.query,
                        Json(result.results),
                        result.total_found,
                        result.search_time_ms,
                        created_at,
                    ),
                )
                row = cur.fetchone()
        return self._row_to_search_result(row)

    def get_search_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SearchResult]:
        with self.pool.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, user_id, query, results, total_found,
                           search_time_ms, created_at
                    FROM search_results
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, limit, offset),
                )
                rows = cur.fetchall()
        return [self._row_to_search_result(row) for row in rows]

    def delete_search_history(self, user_id: str) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM search_results WHERE user_id = %s", (user_id,))
                return cur.rowcount

    @staticmethod
    def _row_to_search_result(row: dict[str, Any]) -> SearchResult:
        return SearchResult(
            id=str(row["id"]),
            user_id=row["user_id"],
            query=row["query"],
            results=row.get("results") or [],
            total_found=int(row["total_found"]),
            search_time_ms=int(row["search_time_ms"]),
            created_at=row["created_at"],
        )
