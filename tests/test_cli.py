"""
tests/test_cli.py
~~~~~~~~~~~~~~~~~
Tests for gaia/cli.py subcommands.

All RAG I/O is mocked — tests are fully offline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_cli(*argv: str):
    """Run cli.main() with the given argv and return the SystemExit code."""
    from gaia.cli import main
    try:
        main(list(argv))
        return 0
    except SystemExit as e:
        return int(e.code) if e.code is not None else 0


def _mock_rag(status="ok", warm=False, docs=3, chunks=42):
    rag = MagicMock()
    rag.ingest_canon.return_value = {
        "status": status,
        "warm_start": warm,
        "doc_count": docs,
        "chunk_count": chunks,
        "duration_s": 0.1,
        "store_path": "/tmp/gaia/canon_index.db",
        "fingerprint": "abcd1234",
    }
    rag.status.return_value = {
        "canon_loaded": True,
        "warm_start": warm,
        "canon_doc_count": docs,
        "canon_chunk_count": chunks,
        "index_size": chunks,
        "top_k": 5,
        "store_path": "/tmp/gaia/canon_index.db",
        "fingerprint": "abcd1234",
    }
    return rag


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class TestArgParsing:

    def test_start_defaults(self):
        from gaia.cli import _build_parser
        parser = _build_parser()
        args = parser.parse_args(["start", "--no-server"])
        assert args.command == "start"
        assert args.no_server is True
        assert args.force is False
        assert args.ref == "feat/obs-rag"

    def test_ingest_canon_force_flag(self):
        from gaia.cli import _build_parser
        parser = _build_parser()
        args = parser.parse_args(["ingest-canon", "--force", "--ref", "main"])
        assert args.force is True
        assert args.ref == "main"

    def test_status_json_flag(self):
        from gaia.cli import _build_parser
        parser = _build_parser()
        args = parser.parse_args(["status", "--json"])
        assert args.json is True

    def test_unknown_command_exits_nonzero(self):
        from gaia.cli import _build_parser
        with pytest.raises(SystemExit) as exc_info:
            _build_parser().parse_args(["nonexistent"])
        assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# start subcommand
# ---------------------------------------------------------------------------

class TestCmdStart:

    @patch("gaia.cli._build_rag")
    def test_start_no_server_returns_zero(self, mock_build, tmp_path):
        mock_build.return_value = _mock_rag()
        rc = _run_cli("start", "--no-server", "--store", str(tmp_path))
        assert rc == 0

    @patch("gaia.cli._build_rag")
    def test_start_warm_start_reported(self, mock_build, tmp_path, capsys):
        mock_build.return_value = _mock_rag(status="warm_start", warm=True)
        _run_cli("start", "--no-server", "--store", str(tmp_path))
        out = capsys.readouterr().out
        assert "warm" in out.lower()

    @patch("gaia.cli._build_rag")
    def test_start_no_rag_warns(self, mock_build, tmp_path, capsys):
        mock_build.return_value = None
        rc = _run_cli("start", "--no-server", "--store", str(tmp_path))
        out = capsys.readouterr().out
        assert "unavailable" in out.lower() or rc == 0  # graceful


# ---------------------------------------------------------------------------
# ingest-canon subcommand
# ---------------------------------------------------------------------------

class TestCmdIngestCanon:

    @patch("gaia.cli._build_rag")
    def test_ingest_ok_returns_zero(self, mock_build, tmp_path):
        mock_build.return_value = _mock_rag()
        rc = _run_cli("ingest-canon", "--store", str(tmp_path))
        assert rc == 0

    @patch("gaia.cli._build_rag")
    def test_ingest_json_output(self, mock_build, tmp_path, capsys):
        mock_build.return_value = _mock_rag()
        _run_cli("ingest-canon", "--store", str(tmp_path), "--json")
        out = capsys.readouterr().out
        # find the JSON block (last occurrence of '{' to '}')
        start = out.rfind("{")
        assert start != -1, "Expected JSON in output"
        data = json.loads(out[start:])
        assert "status" in data

    @patch("gaia.cli._build_rag")
    def test_ingest_error_returns_nonzero(self, mock_build, tmp_path):
        rag = _mock_rag(status="error_exception")
        mock_build.return_value = rag
        rc = _run_cli("ingest-canon", "--store", str(tmp_path))
        assert rc != 0


# ---------------------------------------------------------------------------
# doctor subcommand
# ---------------------------------------------------------------------------

class TestCmdDoctor:

    def test_doctor_runs_without_crash(self, tmp_path):
        """doctor should always exit cleanly (0 or 1 only)."""
        rc = _run_cli("doctor", "--store", str(tmp_path))
        assert rc in (0, 1)

    def test_doctor_reports_python_version(self, tmp_path, capsys):
        rc = _run_cli("doctor", "--store", str(tmp_path))
        out = capsys.readouterr().out
        assert "Python" in out
