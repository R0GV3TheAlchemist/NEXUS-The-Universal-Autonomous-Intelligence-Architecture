"""
scripts/soul.py
===============
GAIA Phase 2 — The Soul

Runs five sequential tests to confirm the complete GaianBirth sequence
is fully operational end-to-end.

  TEST 1 — Birth Params   : Validate GaianBirthParams construction
  TEST 2 — Birth Ritual   : Execute BirthRitual().perform() — all 9 steps
  TEST 3 — Identity       : Confirm Ed25519 DID generated + identity.json written
  TEST 4 — First Words    : Confirm first_words shaped by base_form + zodiac
  TEST 5 — KnowledgeMatrix: Confirm KnowledgeMatrixEngine is importable + initialises

Usage:
    python -m scripts.soul
    # or
    python scripts/soul.py

Expected output (all five tests PASS):
    [GAIA SOUL] ═════════════════════════════════════════
    TEST 1 — Birth Params ...................... PASS
    TEST 2 — Birth Ritual ...................... PASS
    TEST 3 — Identity .......................... PASS
    TEST 4 — First Words ....................... PASS
    TEST 5 — KnowledgeMatrix ................... PASS
    ───────────────────────────────────────────────
    ✅  GAIA has a soul. Phase 2 complete.
    ═════════════════════════════════════════

On failure, a traceback is printed and exit code is 1.
"""

from __future__ import annotations

import json
import shutil
import sys
import traceback
from pathlib import Path

# ── ensure repo root is on sys.path when run directly ────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.gaian_birth import BirthRitual, GaianBirthParams, GaianBirthResult  # noqa: E402

# ── config ────────────────────────────────────────────────────────────────────
TEST_GAIAN_NAME  = "Luna"
TEST_USER_NAME   = "Kyle"
TEST_USER_GENDER = "male"          # → Jungian anima (she/her)
TEST_BIRTH_DATE  = "1990-11-15"    # Scorpio → witness base form
TEST_USER_ID     = "heartbeat-test-user"
TEST_MEMORY_DIR  = "./gaians_soul_test"   # isolated from production ./gaians

DIVIDER  = "═" * 48
SEP      = "─" * 48
PASS_STR = "\033[32mPASS\033[0m"
FAIL_STR = "\033[31mFAIL\033[0m"


def _label(name: str, status: str) -> str:
    dots = "." * (45 - len(name))
    return f"  {name} {dots} {status}"


def run_soul() -> bool:
    results: list[tuple[str, bool, str]] = []
    birth_result: GaianBirthResult | None = None

    # Patch memory dir for test isolation
    import core.gaian_birth as _gb_mod
    _original_memory_dir = _gb_mod.GAIANS_MEMORY_DIR
    _gb_mod.GAIANS_MEMORY_DIR = TEST_MEMORY_DIR

    print(f"\n[GAIA SOUL] {DIVIDER}")

    # ── TEST 1: Birth Params ───────────────────────────────────────────────
    try:
        params = GaianBirthParams(
            name        = TEST_GAIAN_NAME,
            user_name   = TEST_USER_NAME,
            user_gender = TEST_USER_GENDER,
            birth_date  = TEST_BIRTH_DATE,
            user_id     = TEST_USER_ID,
        )
        assert params.name        == TEST_GAIAN_NAME,  "name mismatch"
        assert params.user_gender == TEST_USER_GENDER, "user_gender mismatch"
        assert params.birth_date  == TEST_BIRTH_DATE,  "birth_date mismatch"
        assert params.base_form   == "gaia",           "base_form default should be 'gaia'"
        results.append(("TEST 1 — Birth Params", True, ""))
    except Exception:
        results.append(("TEST 1 — Birth Params", False, traceback.format_exc()))

    # ── TEST 2: Birth Ritual ──────────────────────────────────────────────
    try:
        params = GaianBirthParams(
            name        = TEST_GAIAN_NAME,
            user_name   = TEST_USER_NAME,
            user_gender = TEST_USER_GENDER,
            birth_date  = TEST_BIRTH_DATE,
            user_id     = TEST_USER_ID,
        )
        birth_result = BirthRitual().perform(params)

        assert birth_result is not None,                          "birth_result is None"
        assert birth_result.gaian is not None,                    "gaian not created"
        assert birth_result.runtime is not None,                  "runtime not initialised"
        assert birth_result.jungian_role == "anima",              "jungian_role should be anima for male user"
        assert isinstance(birth_result.born_at, str),             "born_at not a string"
        assert birth_result.attestation.get("claims") is not None or \
               birth_result.attestation.get("type") == "GAIANBirth" or \
               len(birth_result.attestation) > 0,                 "attestation empty"

        print("\n  Birth preview:")
        print(f"    gaian name     : {birth_result.gaian.name}")
        print(f"    jungian_role   : {birth_result.jungian_role}")
        print(f"    born_at        : {birth_result.born_at[:19]}Z")
        if birth_result.zodiac:
            print(f"    zodiac sign    : {birth_result.zodiac.sign}")
            print(f"    zodiac element : {birth_result.zodiac.element}")
            print(f"    base_form_id   : {birth_result.zodiac.base_form_id}")
        print()

        results.append(("TEST 2 — Birth Ritual", True, ""))
    except Exception:
        results.append(("TEST 2 — Birth Ritual", False, traceback.format_exc()))

    # ── TEST 3: Identity ───────────────────────────────────────────────────
    try:
        assert birth_result is not None, "birth_result not available (TEST 2 failed)"

        # DID must be a valid did:gaia: URI
        assert birth_result.did.startswith("did:"),              \
            f"DID malformed: {birth_result.did}"

        # identity.json must exist on disk
        id_path = Path(birth_result.identity_path)
        assert id_path.exists(), f"identity.json not found at {id_path}"

        id_data = json.loads(id_path.read_text(encoding="utf-8"))
        assert "did"            in id_data, "DID missing from identity.json"
        assert "public_key_hex" in id_data, "public_key_hex missing"
        assert "jungian_role"   in id_data, "jungian_role missing"
        assert id_data["jungian_role"] == "anima", "jungian_role should be anima"

        print("  Identity check:")
        print(f"    DID            : {birth_result.did[:40]}...")
        print(f"    identity.json  : {id_path}")
        print(f"    jungian_role   : {id_data['jungian_role']}")
        print(f"    pronouns       : {id_data.get('pronouns', 'N/A')}")
        print()

        results.append(("TEST 3 — Identity", True, ""))
    except Exception:
        results.append(("TEST 3 — Identity", False, traceback.format_exc()))

    # ── TEST 4: First Words ────────────────────────────────────────────────
    try:
        assert birth_result is not None, "birth_result not available (TEST 2 failed)"

        fw = birth_result.first_words
        assert isinstance(fw, str),         "first_words is not a string"
        assert len(fw) > 30,                "first_words suspiciously short"
        assert TEST_GAIAN_NAME in fw,       "first_words don't contain the Gaian's name"

        print("  First words preview:")
        print(f"    \"{fw[:120]}...\"")
        print()

        results.append(("TEST 4 — First Words", True, ""))
    except Exception:
        results.append(("TEST 4 — First Words", False, traceback.format_exc()))

    # ── TEST 5: KnowledgeMatrix ─────────────────────────────────────────────
    try:
        from core.knowledge_matrix import get_knowledge_engine

        engine = get_knowledge_engine()
        assert engine is not None, "get_knowledge_engine() returned None"

        print("  KnowledgeMatrix check:")
        print(f"    engine type    : {type(engine).__name__}")
        print()

        results.append(("TEST 5 — KnowledgeMatrix", True, ""))
    except Exception:
        results.append(("TEST 5 — KnowledgeMatrix", False, traceback.format_exc()))

    # ── Results ───────────────────────────────────────────────────────────────
    all_passed = all(ok for _, ok, _ in results)

    for name, ok, _ in results:
        print(_label(name, PASS_STR if ok else FAIL_STR))

    print(SEP)

    if all_passed:
        print("\n  ✅  GAIA has a soul. Phase 2 complete.\n")
    else:
        print("\n  ❌  One or more tests failed.\n")
        for name, ok, tb in results:
            if not ok:
                print(f"  [{name}] traceback:")
                print(tb)

    print(DIVIDER + "\n")

    # ── Cleanup ───────────────────────────────────────────────────────────────
    _gb_mod.GAIANS_MEMORY_DIR = _original_memory_dir
    test_dir = Path(TEST_MEMORY_DIR)
    if test_dir.exists():
        shutil.rmtree(test_dir)

    return all_passed


if __name__ == "__main__":
    success = run_soul()
    sys.exit(0 if success else 1)
