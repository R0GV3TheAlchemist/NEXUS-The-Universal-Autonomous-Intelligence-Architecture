"""
core/rag/embedder.py

FallbackEmbedder — zero-dependency TF-IDF bag-of-words embedder for GAIA-OS RAG.
Produces L2-normalised float vectors from text.

Design intent:
- Works with zero external dependencies (stdlib only).
- Vocabulary is built incrementally from ingested documents.
- When sentence-transformers or a local model becomes available,
  swap in a HuggingFaceEmbedder that implements the same interface.

Interface (duck-typed):
    embedder.embed(text: str) -> List[float]
    embedder.embed_batch(texts: List[str]) -> List[List[float]]
    embedder.vocab_size -> int
"""
import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class FallbackEmbedder:
    """
    TF-IDF bag-of-words embedder.

    Build flow:
        1. Call fit(corpus) or fit_one(text) to build vocabulary + IDF.
        2. Call embed(text) to get a normalized vector.

    Vectors are sparse in concept but stored as dense lists for SQLite compat.
    Dimensionality = vocabulary size (capped at max_features).
    """

    def __init__(self, max_features: int = 2048):
        self.max_features: int = max_features
        self._doc_freq: Counter = Counter()
        self._doc_count: int = 0
        self._vocab: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._fitted: bool = False

    def fit_one(self, text: str) -> None:
        tokens = set(_tokenize(text))
        for tok in tokens:
            self._doc_freq[tok] += 1
        self._doc_count += 1
        self._fitted = False

    def fit(self, texts: List[str]) -> None:
        for text in texts:
            self.fit_one(text)
        self._build_vocab()

    def _build_vocab(self) -> None:
        top = self._doc_freq.most_common(self.max_features)
        self._vocab = {tok: i for i, (tok, _) in enumerate(top)}
        N = max(self._doc_count, 1)
        self._idf = {
            tok: math.log((N + 1) / (freq + 1)) + 1.0
            for tok, freq in self._doc_freq.items()
            if tok in self._vocab
        }
        self._fitted = True

    def _ensure_fitted(self) -> None:
        if not self._fitted:
            self._build_vocab()

    def embed(self, text: str) -> List[float]:
        self._ensure_fitted()
        tokens = _tokenize(text)
        tf: Counter = Counter(tokens)
        total = max(len(tokens), 1)
        vec = [0.0] * len(self._vocab)
        for tok, count in tf.items():
            if tok in self._vocab:
                idx = self._vocab[tok]
                tfidf = (count / total) * self._idf.get(tok, 1.0)
                vec[idx] = tfidf
        return _l2_normalize(vec)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._ensure_fitted()
        return [self.embed(t) for t in texts]

    @property
    def vocab_size(self) -> int:
        return len(self._vocab)


def _l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two L2-normalised vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return max(-1.0, min(1.0, dot))
