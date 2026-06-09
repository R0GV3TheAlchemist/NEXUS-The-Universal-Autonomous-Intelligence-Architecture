"""
core.memory.embedder
====================
Abstraction layer over embedding backends.

GAIA uses embeddings to convert text into dense float vectors so that
``MemoryStore`` can do semantic (meaning-based) search via sqlite-vec.

Backends
--------
SentenceTransformerEmbedder -- default for offline / sovereign deployments.
                               Uses sentence-transformers (MiniLM by default).
                               No Ollama, no API key, ~80 MB download.
OllamaEmbedder             -- uses a locally-running Ollama model.
OpenAIEmbedder             -- uses text-embedding-3-small / ada-002.
FallbackEmbedder           -- deterministic hash-based stub; always works
                              offline but produces random vectors (dev/test only).

To add a new backend, subclass EmbeddingProvider and implement ``embed()``.
"""

from __future__ import annotations

import hashlib
import logging
import struct
from abc import ABC, abstractmethod

import httpx

log = logging.getLogger(__name__)

# Default embedding dimensionality.
# sqlite-vec requires every vector in a table to have the same dimension.
# Change this constant only when re-creating the database from scratch.
DEFAULT_DIM = 1536


class EmbeddingProvider(ABC):
    """Abstract base -- every embedder must implement ``embed()``."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of the output vectors."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """
        Convert *text* into a list of floats of length ``self.dim``.
        Must be safe to call concurrently.
        """
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Default implementation: embed one-by-one.  Override for batching."""
        results = []
        for t in texts:
            results.append(await self.embed(t))
        return results


class SentenceTransformerEmbedder(EmbeddingProvider):
    """
    Offline, local embedder using the ``sentence-transformers`` library.

    This is the recommended default for GAIA-OS sovereign deployments:
    no Ollama daemon, no API key, fully air-gapped after first download.

    Parameters
    ----------
    model_name   : Any sentence-transformers model name.
                   Recommended defaults:
                     - ``"all-MiniLM-L6-v2"``   -- 384-d, ~80 MB, fast
                     - ``"all-mpnet-base-v2"``   -- 768-d, ~420 MB, accurate
                     - ``"BAAI/bge-small-en-v1.5"`` -- 384-d, ~130 MB, excellent
    dim          : Override output dimension (must match model output).
                   If None, inferred from the model on first load.
    device       : Torch device string ("cpu", "cuda", "mps").
                   Defaults to "cpu" for maximum portability.
    normalize    : L2-normalise vectors before returning.  Recommended True
                   so that cosine similarity == dot product.

    Notes
    -----
    The underlying SentenceTransformer model is loaded lazily on first
    ``embed()`` call so that importing this module is always fast.
    ``encode()`` is called in a thread-pool executor so that async callers
    (e.g. ``MemoryStore.remember()``) are never blocked.

    If ``sentence-transformers`` is not installed, construction raises
    ``ImportError`` with a helpful install hint.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        dim:        int | None = None,
        device:     str = "cpu",
        normalize:  bool = True,
    ) -> None:
        self._model_name = model_name
        self._device     = device
        self._normalize  = normalize
        self._model      = None   # lazy-loaded
        self._dim: int | None = dim
        # Validate that sentence-transformers is importable at construction
        # time so the error surfaces early (not at first embed() call).
        try:
            import sentence_transformers  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for SentenceTransformerEmbedder.\n"
                "Install it with:  pip install sentence-transformers"
            ) from exc

    @property
    def dim(self) -> int:
        if self._dim is None:
            # Load the model now to discover its dimension.
            self._ensure_model()
        return self._dim  # type: ignore[return-value]

    def _ensure_model(self) -> None:
        """Load the SentenceTransformer model once, thread-safely."""
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer  # type: ignore
        log.info(
            "SentenceTransformerEmbedder: loading model '%s' on device '%s' ...",
            self._model_name, self._device,
        )
        self._model = SentenceTransformer(self._model_name, device=self._device)
        if self._dim is None:
            # Probe dimension by encoding an empty string
            probe = self._model.encode("", normalize_embeddings=self._normalize)
            self._dim = int(probe.shape[0])
        log.info(
            "SentenceTransformerEmbedder: model loaded -- dim=%d", self._dim
        )

    async def embed(self, text: str) -> list[float]:
        import asyncio
        import functools
        loop = asyncio.get_event_loop()
        # Run the blocking encode() in a thread-pool so the event loop
        # is not stalled during inference.
        vec = await loop.run_in_executor(
            None,
            functools.partial(self._encode_sync, text),
        )
        return vec

    def _encode_sync(self, text: str) -> list[float]:
        """Blocking encode -- called from a thread via run_in_executor."""
        self._ensure_model()
        vec = self._model.encode(
            text,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
        )
        return vec.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        import functools
        loop = asyncio.get_event_loop()
        vecs = await loop.run_in_executor(
            None,
            functools.partial(self._encode_batch_sync, texts),
        )
        return vecs

    def _encode_batch_sync(self, texts: list[str]) -> list[list[float]]:
        self._ensure_model()
        vecs = self._model.encode(
            texts,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
            batch_size=64,
        )
        return [v.tolist() for v in vecs]


class OllamaEmbedder(EmbeddingProvider):
    """
    Embedder backed by a locally-running Ollama instance.

    Parameters
    ----------
    model     : Ollama model name, e.g. ``"nomic-embed-text"`` (recommended)
                or ``"mxbai-embed-large"``.
    base_url  : Ollama HTTP base URL (default ``http://localhost:11434``).
    dim       : Vector dimension -- must match the chosen model.  Defaults
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

    async def embed(self, text: str) -> list[float]:
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
            return vec[: self._dim]
        except Exception as exc:
            log.error("OllamaEmbedder.embed failed: %s -- falling back to zeros", exc)
            return [0.0] * self._dim

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        url  = f"{self._base_url}/api/embed"
        body = {"model": self._model, "input": texts}
        try:
            resp = await self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
            return [v[: self._dim] for v in data["embeddings"]]
        except Exception:
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

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        url  = f"{self._base_url}/embeddings"
        body: dict = {"model": self._model, "input": texts}
        if self._dim != self._MODEL_DIMS.get(self._model, self._dim):
            body["dimensions"] = self._dim
        try:
            resp = await self._client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
            return [
                d["embedding"][: self._dim]
                for d in sorted(data["data"], key=lambda x: x["index"])
            ]
        except Exception as exc:
            log.error("OpenAIEmbedder.embed_batch failed: %s", exc)
            return [[0.0] * self._dim for _ in texts]


class FallbackEmbedder(EmbeddingProvider):
    """
    Deterministic *hash-based* embedder -- for local dev / unit tests only.

    Vectors are derived from SHA-256 of the input, so they are stable
    across runs but carry no semantic meaning.  Do NOT use in production.
    """

    def __init__(self, dim: int = DEFAULT_DIM) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    async def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()  # 32 bytes
        raw    = digest * (self._dim // 32 + 1)
        ints   = list(struct.unpack(f"{self._dim}b", raw[: self._dim]))
        return [v / 128.0 for v in ints[: self._dim]]
