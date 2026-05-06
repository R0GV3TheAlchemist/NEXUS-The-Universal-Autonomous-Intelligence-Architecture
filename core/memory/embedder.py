"""
core.memory.embedder
====================
Abstraction layer over embedding backends.

GAIA uses embeddings to convert text into dense float vectors so that
``MemoryStore`` can do semantic (meaning-based) search via sqlite-vec.

Backends
--------
OllamaEmbedder    — default; uses a locally-running Ollama model (no API key).
OpenAIEmbedder    — uses text-embedding-3-small / text-embedding-ada-002.
FallbackEmbedder  — deterministic hash-based stub; always works offline but
                    produces *random* vectors (useful for dev/testing only).

To add a new backend, subclass EmbeddingProvider and implement ``embed()``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import struct
from abc import ABC, abstractmethod
from typing import List

import httpx

log = logging.getLogger(__name__)

# Default embedding dimensionality.
# sqlite-vec requires every vector in a table to have the same dimension.
# Change this constant only when re-creating the database from scratch.
DEFAULT_DIM = 1536


class EmbeddingProvider(ABC):
    """Abstract base — every embedder must implement ``embed()``."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of the output vectors."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Convert *text* into a list of floats of length ``self.dim``.
        Must be safe to call concurrently.
        """
        ...

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Default implementation: embed one-by-one.  Override for batching."""
        results = []
        for t in texts:
            results.append(await self.embed(t))
        return results


class OllamaEmbedder(EmbeddingProvider):
    """
    Embedder backed by a locally-running Ollama instance.

    Parameters
    ----------
    model     : Ollama model name, e.g. ``"nomic-embed-text"`` (recommended)
                or ``"mxbai-embed-large"``.
    base_url  : Ollama HTTP base URL (default ``http://localhost:11434``).
    dim       : Vector dimension — must match the chosen model.  Defaults
                to 768 for nomic-embed-text; override as needed.
    timeout   : Per-request timeout in seconds.
    """

    def __init__(
        self,
        model:    str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        dim:      int = 768,
        timeout:  float = 30.0,
    ) -> None:
        self._model    = model
        self._base_url = base_url.rstrip("/")
        self._dim      = dim
        self._timeout  = timeout
        self._client   = httpx.AsyncClient(timeout=timeout)

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, text: str) -> List[float]:
        url  = f"{self._base_url}/api/embeddings"
        body = {"model": self._model, "prompt": text}
        try:
            resp = await self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
            vec = data["embedding"]
            if len(vec) != self._dim:
                log.warning(
                    "OllamaEmbedder: expected dim=%d, got dim=%d for model=%s",
                    self._dim, len(vec), self._model,
                )
            return vec[: self._dim]  # truncate if needed
        except Exception as exc:
            log.error("OllamaEmbedder.embed failed: %s — falling back to zeros", exc)
            return [0.0] * self._dim

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Ollama v0.3+ supports POST /api/embed with multiple inputs
        url  = f"{self._base_url}/api/embed"
        body = {"model": self._model, "input": texts}
        try:
            resp = await self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
            return [v[: self._dim] for v in data["embeddings"]]
        except Exception:
            # Fall back to one-by-one
            return [await self.embed(t) for t in texts]


class OpenAIEmbedder(EmbeddingProvider):
    """
    Embedder backed by the OpenAI Embeddings API.

    Parameters
    ----------
    api_key    : Your OpenAI API key.
    model      : ``"text-embedding-3-small"`` (default, 1536-d) or
                 ``"text-embedding-3-large"`` (3072-d).
    dimensions : Override the output dimension (text-embedding-3-* supports
                 server-side truncation).
    base_url   : Override for Azure OpenAI or local proxies.
    """

    _MODEL_DIMS = {
        "text-embedding-3-small":  1536,
        "text-embedding-3-large":  3072,
        "text-embedding-ada-002":  1536,
    }

    def __init__(
        self,
        api_key:    str,
        model:      str   = "text-embedding-3-small",
        dimensions: int   = DEFAULT_DIM,
        base_url:   str   = "https://api.openai.com/v1",
        timeout:    float = 30.0,
    ) -> None:
        self._api_key    = api_key
        self._model      = model
        self._dim        = dimensions
        self._base_url   = base_url.rstrip("/")
        self._client     = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, text: str) -> List[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        url  = f"{self._base_url}/embeddings"
        body: dict = {"model": self._model, "input": texts}
        if self._dim != self._MODEL_DIMS.get(self._model, self._dim):
            body["dimensions"] = self._dim
        try:
            resp = await self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
            return [d["embedding"][: self._dim] for d in sorted(data["data"], key=lambda x: x["index"])]
        except Exception as exc:
            log.error("OpenAIEmbedder.embed_batch failed: %s", exc)
            return [[0.0] * self._dim for _ in texts]


class FallbackEmbedder(EmbeddingProvider):
    """
    Deterministic *hash-based* embedder — for local dev / unit tests only.

    Vectors are derived from SHA-256 of the input, so they are stable
    across runs but carry no semantic meaning.  Do NOT use in production.
    """

    def __init__(self, dim: int = DEFAULT_DIM) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode()).digest()  # 32 bytes
        # Tile the digest to cover `dim` floats
        raw = digest * (self._dim // 32 + 1)
        # Unpack as int8 and normalise to [-1, 1]
        # Fix: format count must match the sliced buffer length (self._dim),
        # not the full tiled buffer length (len(raw)).
        ints   = list(struct.unpack(f"{self._dim}b", raw[: self._dim]))
        norm   = [v / 128.0 for v in ints[: self._dim]]
        return norm
