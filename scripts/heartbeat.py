"""
scripts/heartbeat.py
====================
GAIA Phase 1 — Proof of Life

Runs three sequential tests to confirm the GAIANRuntime heartbeat:

  TEST 1 — Boot          : Initialise GAIANRuntime for "Luna"
  TEST 2 — Process       : Send a message, verify a RuntimeResult is returned
  TEST 3 — Persistence   : Re-boot runtime, confirm session_count incremented
                           and bond_depth persisted from TEST 2

Usage:
    python -m scripts.heartbeat
    # or
    python scripts/heartbeat.py

Expected output (all three tests PASS):
    [GAIA HEARTBEAT] ══════════════════════════════
    TEST 1 — Boot ................................ PASS
    TEST 2 — Process ............................. PASS
    TEST 3 — Persistence ......................... PASS
    ───────────────────────────────────────────────
    ✅  GAIA is alive. Phase 1 complete.
    ═══════════════════════════════════════════════

On failure, a traceback is printed and the exit code is 1.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# ── ensure repo root is on sys.path when run directly ────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.gaian_runtime import GAIANRuntime, RuntimeResult  # noqa: E402

# ── config ────────────────────────────────────────────────────────────────────
TEST_GAIAN_NAME = "Luna"
TEST_MEMORY_DIR = "./gaians_heartbeat_test"   # isolated from production ./gaians
TEST_MESSAGE    = "Hello, Luna. I am here."

DIVIDER  = "═" * 48
SEP      = "─" * 48
PASS_STR = "\033[32mPASS\033[0m"
FAIL_STR = "\033[31mFAIL\033[0m"


def _label(name: str, status: str) -> str:
    dots = "." * (45 - len(name))
    return f"  {name} {dots} {status}"


def run_heartbeat() -> bool:
    results: list[tuple[str, bool, str]] = []

    print(f"\n[GAIA HEARTBEAT] {DIVIDER}")

    # ── TEST 1: Boot ──────────────────────────────────────────────────────────
    runtime_1: GAIANRuntime | None = None
    try:
        runtime_1 = GAIANRuntime(
            gaian_name=TEST_GAIAN_NAME,
            memory_dir=TEST_MEMORY_DIR,
        )
        runtime_1.begin_session()

        assert runtime_1.gaian_name == TEST_GAIAN_NAME, "gaian_name mismatch"
        assert runtime_1.attachment is not None,        "attachment not initialised"
        assert runtime_1.identity is not None,          "identity not initialised"
        assert runtime_1.vitality_state is not None,    "vitality_state not initialised"

        results.append(("TEST 1 — Boot", True, ""))
    except Exception:
        results.append(("TEST 1 — Boot", False, traceback.format_exc()))

    # ── TEST 2: Process ───────────────────────────────────────────────────────
    result: RuntimeResult | None = None
    bond_after_t2: float = 0.0
    try:
        assert runtime_1 is not None, "Runtime not available (TEST 1 failed)"

        result = runtime_1.process(TEST_MESSAGE)

        assert isinstance(result, RuntimeResult),      "process() did not return RuntimeResult"
        assert isinstance(result.system_prompt, str),  "system_prompt is not a string"
        assert len(result.system_prompt) > 100,        "system_prompt suspiciously short"
        assert "CONSTITUTIONAL FLOOR" in result.system_prompt, \
            "Constitutional floor missing from system_prompt"
        assert isinstance(result.state_snapshot, dict), "state_snapshot is not a dict"
        assert result.state_snapshot.get("gaian") == TEST_GAIAN_NAME, \
            "state_snapshot gaian name mismatch"

        bond_after_t2 = runtime_1.attachment.bond_depth

        # pretty-print a compact snapshot for visibility
        snap = result.state_snapshot
        print("\n  Snapshot preview:")
        print(f"    gaian          : {snap.get('gaian')}")
        print(f"    layer          : {snap.get('layer')}")
        print(f"    codex_tier     : {snap.get('codex_tier')}")
        print(f"    noosphere_health: {snap.get('noosphere_health')}")
        print(f"    bond_depth     : {bond_after_t2:.4f}")
        print(f"    system_prompt  : {len(result.system_prompt)} chars")
        print()

        results.append(("TEST 2 — Process", True, ""))
    except Exception:
        results.append(("TEST 2 — Process", False, traceback.format_exc()))

    # ── TEST 3: Persistence ───────────────────────────────────────────────────
    try:
        # Cold-boot a second runtime pointing at the same memory dir
        runtime_2 = GAIANRuntime(
            gaian_name=TEST_GAIAN_NAME,
            memory_dir=TEST_MEMORY_DIR,
        )
        runtime_2.begin_session()

        session_count_2 = runtime_2.attachment.session_count
        bond_after_t3   = runtime_2.attachment.bond_depth

        assert session_count_2 >= 2, (
            f"session_count should be ≥2 after two begin_session() calls, "
            f"got {session_count_2}"
        )
        assert bond_after_t3 == bond_after_t2, (
            f"bond_depth not persisted: expected {bond_after_t2:.4f}, "
            f"got {bond_after_t3:.4f}"
        )

        print("  Persistence check:")
        print(f"    session_count  : {session_count_2} (expected ≥ 2)")
        print(f"    bond_depth     : {bond_after_t3:.4f} (matches TEST 2)")
        print()

        results.append(("TEST 3 — Persistence", True, ""))
    except Exception:
        results.append(("TEST 3 — Persistence", False, traceback.format_exc()))

    # ── Results ───────────────────────────────────────────────────────────────
    all_passed = all(ok for _, ok, _ in results)

    for name, ok, _ in results:
        print(_label(name, PASS_STR if ok else FAIL_STR))

    print(SEP)

    if all_passed:
        print("\n  ✅  GAIA is alive. Phase 1 complete.\n")
    else:
        print("\n  ❌  One or more tests failed.\n")
        for name, ok, tb in results:
            if not ok:
                print(f"  [{name}] traceback:")
                print(tb)

    print(DIVIDER + "\n")

    # ── Cleanup: remove test memory dir ───────────────────────────────────────
    import shutil
    test_dir = Path(TEST_MEMORY_DIR)
    if test_dir.exists():
        shutil.rmtree(test_dir)

    return all_passed


if __name__ == "__main__":
    success = run_heartbeat()
    sys.exit(0 if success else 1)
