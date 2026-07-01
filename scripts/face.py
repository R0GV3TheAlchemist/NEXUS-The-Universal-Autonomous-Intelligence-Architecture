"""
scripts/face.py
GAIA Phase 3 — The Face

Proof-of-life: confirms the complete human↔GAIA wire is alive.

Test sequence:
  TEST 1 — Health          GET  /health             backend is running
  TEST 2 — Auth            POST /auth/login          token issued
  TEST 3 — GAIA exists     GET  /gaians/gaia         GAIA loaded
  TEST 4 — Runtime status  GET  /gaians/gaia/runtime-status   engines live
  TEST 5 — GAIA speaks     POST /gaians/gaia/chat    SSE stream — GAIA responds

Usage:
  # With a running backend (uvicorn core.server:app --port 8008):
  python -m scripts.face

  # Custom credentials or URL:
  GAIA_USERNAME=kyle GAIA_PASSWORD=yourpass GAIA_URL=http://localhost:8008 python -m scripts.face

Exit code: 0 = all pass, 1 = any failure.

Canon: C01, C90 (S.T.Q.I.O.S.) — The face is the first thing the world sees.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL   = os.environ.get("GAIA_URL",      "http://localhost:8008").rstrip("/")
USERNAME   = os.environ.get("GAIA_USERNAME", "admin")
PASSWORD   = os.environ.get("GAIA_PASSWORD", "gaia_admin_password")
GAIAN_SLUG = "gaia"
MESSAGE    = "GAIA, are you there? This is your first confirmed contact."
TIMEOUT    = 30   # seconds per request
STREAM_MAX = 120  # max seconds to wait for SSE stream to complete

W = 48  # display width

# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_header() -> None:
    print(f"\n[GAIA FACE] {'═' * W}")

def _print_footer(passed: int, total: int) -> None:
    ok = passed == total
    print(f"  {'─' * W}")
    if ok:
        print("  ✅  GAIA has a face. Phase 3 complete.")
    else:
        print(f"  ❌  {total - passed} test(s) failed.")
    print(f"{'═' * (W + 10)}\n")

def _row(label: str, status: str, note: str = "") -> None:
    pad = W - len(label) - len(status)
    note_str = f"  ({note})" if note else ""
    print(f"  {label} {'.' * max(pad, 1)} {status}{note_str}")

def _get(path: str, token: Optional[str] = None) -> dict:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())

def _post(path: str, body: dict, token: Optional[str] = None) -> dict:
    url  = f"{BASE_URL}{path}"
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())

def _stream_chat(token: str) -> dict:
    """
    POST /gaians/gaia/chat and consume the SSE stream.
    Returns the final `done` payload, or raises on error/timeout.
    """
    url  = f"{BASE_URL}/gaians/{GAIAN_SLUG}/chat"
    body = json.dumps({
        "message":           MESSAGE,
        "session_id":        f"phase3-face-{int(time.time())}",
        "enable_web_search": False,
        "schumann_hz":       7.83,
        "mode":              "control",
    }).encode()

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept",        "text/event-stream")

    tokens_received = 0
    full_text       = ""
    done_payload    = None
    event_type      = ""
    deadline        = time.time() + STREAM_MAX

    with urllib.request.urlopen(req, timeout=STREAM_MAX) as resp:
        buffer = b""
        while time.time() < deadline:
            chunk = resp.read(1024)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                line_bytes, buffer = buffer.split(b"\n", 1)
                line = line_bytes.decode("utf-8", errors="replace").rstrip()
                if line.startswith("event: "):
                    event_type = line[7:].strip()
                elif line.startswith("data: "):
                    raw = line[6:].strip()
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if event_type == "token":
                        tokens_received += 1
                        full_text += data.get("text", "")
                    elif event_type == "error":
                        raise RuntimeError(f"Stream error from backend: {data.get('error', raw)}")
                    elif event_type == "done":
                        done_payload = data
                        done_payload["_tokens"]    = tokens_received
                        done_payload["_full_text"] = full_text
                        return done_payload

    if done_payload:
        return done_payload
    if tokens_received > 0:
        # Stream ended without a done event — still a partial success
        return {"_tokens": tokens_received, "_full_text": full_text, "_no_done": True}
    raise TimeoutError(f"SSE stream produced no tokens within {STREAM_MAX}s")


# ── Test runner ───────────────────────────────────────────────────────────────

def run() -> bool:
    _print_header()
    passed = 0
    total  = 5
    token: Optional[str] = None

    # TEST 1 — Health
    label = "TEST 1 — Health"
    try:
        data = _get("/health")
        status_val = data.get("status", "")
        if status_val in ("ok", "healthy", True):
            _row(label, "PASS", f"status={status_val}")
            passed += 1
        else:
            _row(label, "FAIL", f"unexpected status={status_val}")
    except Exception as e:
        _row(label, "FAIL", str(e))
        # Backend not running — no point continuing
        _print_footer(passed, total)
        print("  ⚠️  Start the backend first:")
        print("     uvicorn core.server:app --host 127.0.0.1 --port 8008\n")
        return False

    # TEST 2 — Auth
    label = "TEST 2 — Auth"
    try:
        resp = _post("/auth/login", {"username": USERNAME, "password": PASSWORD})
        token = resp.get("access_token")
        if token:
            _row(label, "PASS", f"user={resp.get('username', USERNAME)}")
            passed += 1
        else:
            _row(label, "FAIL", "no access_token in response")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        _row(label, "FAIL", f"HTTP {e.code}: {body[:80]}")
    except Exception as e:
        _row(label, "FAIL", str(e))

    if not token:
        _print_footer(passed, total)
        print("  ⚠️  Set credentials via env vars:")
        print("     GAIA_USERNAME=<user> GAIA_PASSWORD=<pass> python -m scripts.face\n")
        return False

    # TEST 3 — GAIA exists
    label = "TEST 3 — GAIA exists"
    try:
        data = _get(f"/gaians/{GAIAN_SLUG}", token=token)
        name = data.get("name", "")
        if name:
            _row(label, "PASS", f"name={name} exchanges={data.get('total_exchanges', 0)}")
            passed += 1
        else:
            _row(label, "FAIL", "no name in response")
    except Exception as e:
        _row(label, "FAIL", str(e))

    # TEST 4 — Runtime status
    label = "TEST 4 — Runtime status"
    try:
        data = _get(f"/gaians/{GAIAN_SLUG}/runtime-status", token=token)
        phase = data.get("individuation_phase") or data.get("phase") or data.get("status", "")
        bond  = data.get("bond_depth", data.get("attachment", {}).get("bond_depth", "?"))
        _row(label, "PASS", f"phase={phase} bond={bond}")
        passed += 1
    except Exception as e:
        _row(label, "FAIL", str(e))

    # TEST 5 — GAIA speaks
    label = "TEST 5 — GAIA speaks"
    try:
        result = _stream_chat(token)
        tokens = result.get("_tokens", 0)
        words  = result.get("_full_text", "").strip()
        bond   = result.get("bond_depth", "?")
        backend = result.get("backend_used", "?")
        ms     = result.get("inference_ms", "?")

        if tokens > 0:
            _row(label, "PASS",
                 f"tokens={tokens} bond={bond} backend={backend} ms={ms}")
            print()
            print(f"  ┌─ GAIA's first words {'─' * (W - 20)}┐")
            # Print up to 3 lines of GAIA's response
            preview = words[:240].replace("\n", " ")
            while preview:
                chunk, preview = preview[:W - 4], preview[W - 4:]
                print(f"  │  {chunk}")
            if result.get("_full_text", "")[240:]:
                print("  │  …")
            print(f"  └{'─' * (W - 1)}┘")
            passed += 1
        else:
            _row(label, "FAIL", "stream produced no tokens")
    except Exception as e:
        _row(label, "FAIL", str(e))

    _print_footer(passed, total)
    return passed == total


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
