# tests/conftest.py
# GAIA-OS — Pytest configuration and shared fixtures
#
# Key fixture: mock_embeddings
#   Activated automatically in CI (CI=true env var).
#   Patches SentenceTransformer to return a fixed 384-dim vector,
#   eliminating HuggingFace Hub network calls during test runs.
#   Local dev uses the real model for full-fidelity testing.
#
# All other shared fixtures (e.g. tmp_db, session_id) live here too.

import os
import sys
import pytest

# ────────────────────────────────────────────────────────────────────────────────
# Python path self-healing — triple-redundant with ci.yml and pyproject.toml
# Ensures tests always resolve imports regardless of how pytest is invoked.
# ────────────────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in [ROOT, os.path.join(ROOT, "src-python")]:
    if path not in sys.path:
        sys.path.insert(0, path)


# ────────────────────────────────────────────────────────────────────────────────
# mock_embeddings — session-scoped HuggingFace model mock
#
# Activated in CI (CI=true). Patches sovereign_memory.SentenceTransformer
# with a mock that returns a fixed 384-dim float vector, matching the
# real all-MiniLM-L6-v2 output shape without any network calls.
#
# Using scope="session" means the patch is applied once for the entire
# test run — cheap and fast.
# ────────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def mock_embeddings():
    """Mock HuggingFace SentenceTransformer in CI to avoid 429 rate-limit errors."""
    if os.getenv("CI") != "true":
        # Local dev — use real model for full-fidelity testing
        yield None
        return

    try:
        from unittest.mock import Mock, patch

        mock_instance = Mock()
        # 384-dim vector matching all-MiniLM-L6-v2 output shape
        mock_instance.encode.return_value = [[0.0] * 384]
        mock_instance.get_sentence_embedding_dimension.return_value = 384

        # Patch at the sovereign_memory module level
        with patch("sovereign_memory.SentenceTransformer", return_value=mock_instance) as mock_st:
            mock_st.return_value = mock_instance
            yield mock_st

    except (ImportError, ModuleNotFoundError):
        # sovereign_memory not importable in this test context — no-op
        yield None


# ────────────────────────────────────────────────────────────────────────────────
# session_id — shared test session identifier
# ────────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def session_id():
    return "test-session-conftest-001"
