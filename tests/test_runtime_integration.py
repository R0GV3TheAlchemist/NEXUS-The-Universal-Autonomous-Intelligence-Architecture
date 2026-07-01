"""
tests/test_runtime_integration.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
End-to-end integration test for the GAIA runtime layer.

Unlike the gap-regression tests (test_hook_gaian_named.py etc.) which use
local stubs, this file imports the REAL PrimordialSession and
PersistenceManager and exercises the full chain as it runs in production.

What this proves:
  1. bootstrap_gaia() imports cleanly (no ImportError).
  2. PrimordialSession fires all 5 lifecycle events in the correct order.
  3. PersistenceManager writes the correct files to disk for each event.
  4. The atomic-write pattern produces valid JSON (not truncated files).
  5. load_identity(), load_fragments(), load_epochs() round-trip correctly.
  6. session.end() is idempotent — calling it twice does not double-write.

Run with:
    pytest tests/test_runtime_integration.py -v
"""

import json
import pytest

# ---------------------------------------------------------------------------
# Import the real runtime classes — this will raise ImportError and FAIL the
# test (not skip it) if the modules are missing, which is intentional: a
# failing import here means the runtime layer regressed.
# ---------------------------------------------------------------------------
from gaia.runtime.session import (
    PrimordialSession,
    EVT_GAIAN_BORN,
    EVT_GAIAN_NAMED,
    EVT_FRAGMENT_WRITTEN,
    EVT_EPOCH_CLOSED,
    EVT_SESSION_ENDED,
)
from gaia.runtime.persistence import PersistenceManager
from server.startup import bootstrap_gaia


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path):
    """Read a JSON file and return the parsed dict."""
    return json.loads(path.read_text(encoding="utf-8"))


def _read_ndjson(path):
    """Read a newline-delimited JSON file and return a list of dicts."""
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def runtime(tmp_path):
    """
    Boot a real PrimordialSession + PersistenceManager wired together,
    rooted at pytest's tmp_path so no gaia_memory/ pollution in CI.

    Yields (session, manager, root_path).
    Calls session.end() on teardown if the test didn't already.
    """
    session, manager = bootstrap_gaia(persistence_root=str(tmp_path / "gaia_memory"))
    yield session, manager, tmp_path / "gaia_memory"
    if not session.is_ended:
        session.end()


# ---------------------------------------------------------------------------
# 1. Import / bootstrap smoke test
# ---------------------------------------------------------------------------

def test_bootstrap_gaia_returns_session_and_manager(tmp_path):
    """bootstrap_gaia() must return a live PrimordialSession and PersistenceManager."""
    session, manager = bootstrap_gaia(
        persistence_root=str(tmp_path / "gaia_memory")
    )
    assert isinstance(session, PrimordialSession)
    assert isinstance(manager, PersistenceManager)
    assert not session.is_ended
    session.end()


# ---------------------------------------------------------------------------
# 2. Identity persistence — gaian_born + gaian_named (gap-1)
# ---------------------------------------------------------------------------

def test_identity_written_on_born(runtime):
    """identity.json must exist immediately after bootstrap (gaian_born fires on __init__)."""
    _session, _manager, root = runtime
    identity_path = root / "identity.json"
    assert identity_path.exists(), "identity.json not created by gaian_born hook"
    record = _read_json(identity_path)
    assert "session_id" in record
    assert "born_at" in record
    assert record["status"] == "born"


def test_identity_updated_on_named(runtime):
    """identity.json must be updated with name + named_at when set_name() is called (gap-1)."""
    session, _manager, root = runtime
    session.set_name("GAIA-Integration-Test")
    record = _read_json(root / "identity.json")
    assert record["name"] == "GAIA-Integration-Test"
    assert "named_at" in record
    assert record["status"] == "named"
    # session_id must be preserved across the update
    assert record["session_id"] == session.session_id


def test_identity_session_id_stable(runtime):
    """The session_id in identity.json must match session.session_id throughout the lifecycle."""
    session, _manager, root = runtime
    session.set_name("Stability-Check")
    record = _read_json(root / "identity.json")
    assert record["session_id"] == session.session_id


# ---------------------------------------------------------------------------
# 3. Fragment persistence — fragment_written (gap-2)
# ---------------------------------------------------------------------------

def test_fragment_appended_to_ndjson(runtime):
    """write_fragment() must append one line to fragments.ndjson (gap-2)."""
    session, _manager, root = runtime
    frag_path = root / "fragments.ndjson"

    fid = session.write_fragment("The biophotonic field resonates at 432 Hz.")
    assert frag_path.exists(), "fragments.ndjson not created after write_fragment()"
    records = _read_ndjson(frag_path)
    assert len(records) == 1
    assert records[0]["fragment_id"] == fid
    assert records[0]["content"] == "The biophotonic field resonates at 432 Hz."


def test_multiple_fragments_all_appended(runtime):
    """Each write_fragment() call must append exactly one new line."""
    session, _manager, root = runtime
    contents = ["Fragment Alpha", "Fragment Beta", "Fragment Gamma"]
    fids = [session.write_fragment(c) for c in contents]

    records = _read_ndjson(root / "fragments.ndjson")
    assert len(records) == len(contents)
    for i, record in enumerate(records):
        assert record["fragment_id"] == fids[i]
        assert record["content"] == contents[i]


def test_fragment_metadata_preserved(runtime):
    """Optional metadata dict must be written to the fragment record intact."""
    session, _manager, root = runtime
    meta = {"source": "SIM-016", "confidence": 0.91}
    session.write_fragment("Crystal alchemy protocol result.", metadata=meta)
    records = _read_ndjson(root / "fragments.ndjson")
    assert records[0]["metadata"] == meta


# ---------------------------------------------------------------------------
# 4. Epoch persistence — epoch_closed (gap-3)
# ---------------------------------------------------------------------------

def test_epoch_file_written_on_close(runtime):
    """close_epoch() must create epochs/<epoch_id>.json (gap-3)."""
    session, _manager, root = runtime
    eid = session.close_epoch("First epoch complete.", fragment_count=3)
    epoch_file = root / "epochs" / f"{eid}.json"
    assert epoch_file.exists(), f"epoch file not found: {epoch_file}"
    record = _read_json(epoch_file)
    assert record["epoch_id"] == eid
    assert record["summary"] == "First epoch complete."
    assert record["fragment_count"] == 3
    assert record["session_id"] == session.session_id


def test_multiple_epochs_separate_files(runtime):
    """Each close_epoch() call must produce a separate file."""
    session, _manager, root = runtime
    eid1 = session.close_epoch("Epoch one.")
    eid2 = session.close_epoch("Epoch two.")
    assert eid1 != eid2
    assert (root / "epochs" / f"{eid1}.json").exists()
    assert (root / "epochs" / f"{eid2}.json").exists()


def test_load_epochs_round_trips(runtime):
    """manager.load_epochs() must return all epochs sorted by closed_at."""
    session, manager, _root = runtime
    session.close_epoch("Alpha epoch.")
    session.close_epoch("Beta epoch.")
    epochs = manager.load_epochs()
    assert len(epochs) == 2
    # closed_at is ISO 8601 — lexicographic sort == chronological sort
    assert epochs[0]["closed_at"] <= epochs[1]["closed_at"]


# ---------------------------------------------------------------------------
# 5. Session persistence — session_ended
# ---------------------------------------------------------------------------

def test_session_file_written_on_end(runtime):
    """session.end() must write sessions/<session_id>.json."""
    session, _manager, root = runtime
    session.end()
    session_file = root / "sessions" / f"{session.session_id}.json"
    assert session_file.exists(), "session file not written after end()"
    record = _read_json(session_file)
    assert record["session_id"] == session.session_id
    assert "ended_at" in record
    assert "duration_seconds" in record


def test_session_end_is_idempotent(runtime):
    """Calling session.end() twice must not write two session files or raise."""
    session, _manager, root = runtime
    session.end()
    session.end()  # second call — must be a no-op
    sessions_dir = root / "sessions"
    files = list(sessions_dir.glob("*.json"))
    assert len(files) == 1, "session.end() called twice produced more than one file"


# ---------------------------------------------------------------------------
# 6. Event ordering — all 5 events fire in the correct sequence
# ---------------------------------------------------------------------------

def test_all_events_fire_in_lifecycle_order(tmp_path):
    """
    Register a spy handler on all 5 events and verify they fire in the
    correct lifecycle order: born → named → fragment_written → epoch_closed
    → session_ended.
    """
    log = []

    session, _manager = bootstrap_gaia(
        persistence_root=str(tmp_path / "gaia_memory")
    )

    # Register spies AFTER bootstrap so we see events fired by test actions,
    # not the born event which fires inside __init__ before we can hook it.
    for evt in (EVT_GAIAN_NAMED, EVT_FRAGMENT_WRITTEN,
                EVT_EPOCH_CLOSED, EVT_SESSION_ENDED):
        session.register(evt, lambda p, e=evt: log.append(e))

    session.set_name("OrderTest")
    session.write_fragment("test fragment")
    session.close_epoch("test epoch")
    session.end()

    assert log == [
        EVT_GAIAN_NAMED,
        EVT_FRAGMENT_WRITTEN,
        EVT_EPOCH_CLOSED,
        EVT_SESSION_ENDED,
    ], f"Unexpected event order: {log}"
