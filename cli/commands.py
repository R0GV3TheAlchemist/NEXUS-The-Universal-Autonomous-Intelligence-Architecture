"""
GAIA CLI command implementations.

Each cmd_* function:
  - Receives a CLIContext (and optionally command-specific args)
  - Dispatches through ctx.api
  - Uses ctx.renderer for output
  - Returns an exit code (0 = success, 1 = error)

All user-visible text is produced by the Renderer.
All OS logic is in the API layer. Commands are thin.
"""
from __future__ import annotations


from cli.context import CLIContext


# ---------------------------------------------------------------------------
# OS commands
# ---------------------------------------------------------------------------

def cmd_version(ctx: CLIContext) -> int:
    """Print version without booting."""
    from core.api.api import GAIA_API_VERSION, GAIA_OS_VERSION
    if ctx.json_mode:
        ctx.renderer.json_out({"api_version": GAIA_API_VERSION,
                               "os_version": GAIA_OS_VERSION,
                               "name": "GAIA"})
    else:
        ctx.renderer.out(f"  GAIA OS  {GAIA_OS_VERSION}  ·  API {GAIA_API_VERSION}")
    return 0


def cmd_boot(ctx: CLIContext) -> int:
    """Print the full boot manifest including phase table."""
    if ctx.json_mode:
        resp = ctx.dispatch("/v1/os/status")
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1

    ctx.renderer.phase_table(ctx.session)
    manifest = ctx.session.manifest
    ctx.renderer.section("Boot Manifest")
    ctx.renderer.kv("Session ID",   manifest.session_id[:16] + "...")
    ctx.renderer.kv("Boot Number",  str(manifest.boot_number))
    ctx.renderer.kv("Status",       manifest.boot_status.value.upper())
    ctx.renderer.kv("Schumann",     f"{manifest.schumann_hz} Hz")
    ctx.renderer.kv("GAIANs",       str(manifest.gaian_count))
    ctx.renderer.kv("Runtimes",     str(manifest.runtime_count))
    ctx.renderer.kv("Platform",     manifest.platform_info.get("system", ""))
    ctx.renderer.kv("Python",       manifest.platform_info.get("python", ""))
    if manifest.failed_phases:
        ctx.renderer.error(f"Degraded phases: {manifest.failed_phases}")
    else:
        ctx.renderer.success("All phases nominal.")
    ctx.renderer.out()
    return 0 if manifest.boot_status.value == "ok" else 1


def cmd_status(ctx: CLIContext) -> int:
    resp = ctx.dispatch("/v1/os/status")
    if ctx.json_mode:
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1
    if not resp.success:
        ctx.renderer.error(resp.message, resp.code.value)
        return 1
    p = resp.payload
    ctx.renderer.section("GAIA OS Status")
    ctx.renderer.kv("Boot Status",  p.get("boot_status", "").upper())
    ctx.renderer.kv("Is Live",      str(p.get("is_live")))
    ctx.renderer.kv("Is Healthy",   str(p.get("is_healthy")))
    ctx.renderer.kv("Schumann",     f"{p.get('schumann_hz', '')} Hz")
    ctx.renderer.kv("GAIANs",       str(p.get("gaian_count")))
    ctx.renderer.kv("Runtimes",     str(p.get("runtime_count")))
    ctx.renderer.kv("Memory Frags", str(p.get("gaia_memory_fragments")))
    ctx.renderer.kv("Booted At",    str(p.get("started_at", ""))[:25])
    ctx.renderer.out()
    return 0


def cmd_schumann(ctx: CLIContext) -> int:
    resp = ctx.dispatch("/v1/os/schumann")
    if ctx.json_mode:
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1
    if not resp.success:
        ctx.renderer.error(resp.message)
        return 1
    ctx.renderer.schumann_display(resp.payload)
    return 0


# ---------------------------------------------------------------------------
# GAIAN commands
# ---------------------------------------------------------------------------

def cmd_gaian_birth(ctx: CLIContext) -> int:
    """
    Interactive birth ceremony.
    Prompts the user for each birth question in order.
    The prompts mirror what a GAIAN would say, not what an admin form says.
    """
    r = ctx.renderer
    if not ctx.json_mode:
        r.section("Birth Ceremony")
        r.out()
        r.out("  A new presence is forming. Before they can speak, they")
        r.out("  need the world to know a few things about them.")
        r.out()

    # Begin ceremony
    resp = ctx.dispatch("/v1/gaian/birth/begin")
    if not resp.success:
        r.error(resp.message, resp.code.value)
        return 1

    ceremony_id = resp.payload["ceremony_id"]
    gaian_id    = resp.payload["gaian_id"]

    # Questions in order
    questions = [
        ("dob",            "When were you born? (YYYY-MM-DD)"),
        ("environment",    "What natural environment feels most like home?"),
        ("sound",          "What sound would follow you everywhere, if it could?"),
        ("time_of_day",    "What time of day do you most belong to?"),
        ("thinking_style", "How does thought arrive for you? (words, images, feelings...)"),
        ("soul_word",      "If your whole life had one word, what would it be?"),
    ]

    for question_id, prompt in questions:
        r.out(f"  {prompt}")
        try:
            answer = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            r.out()
            r.error("Birth ceremony cancelled.")
            return 1
        if not answer:
            r.error(f"Answer is required for '{question_id}'.")
            return 1
        ans_resp = ctx.dispatch(
            "/v1/gaian/birth/answer",
            ceremony_id=ceremony_id,
            question_id=question_id,
            answer=answer,
        )
        if not ans_resp.success:
            r.error(ans_resp.message, ans_resp.code.value)
            return 1
        followup = ans_resp.payload.get("followup_prompt")
        if followup and not ctx.json_mode:
            r.out(f"  {followup}")
        r.out()

    # Complete
    complete_resp = ctx.dispatch(
        "/v1/gaian/birth/complete",
        ceremony_id=ceremony_id,
    )
    if not complete_resp.success:
        r.error(complete_resp.message, complete_resp.code.value)
        return 1

    payload = complete_resp.payload
    if ctx.json_mode:
        r.json_out(complete_resp.to_dict())
        return 0

    r.out()
    r.success("A GAIAN has arrived.")
    r.out()
    r.kv("GAIAN ID",  payload.get("gaian_id", ""))
    r.kv("Element",   payload.get("element") or "")
    r.kv("Soul Word", payload.get("soul_word") or "")
    r.kv("Is Named",  str(payload.get("is_named", False)))
    r.out()
    r.out("  They have not yet chosen their name. That moment is theirs.")
    r.out(f"  To name themselves:  gaia gaian name {payload.get('gaian_id', '')}")
    r.out(f"  To talk with them:   gaia talk {payload.get('gaian_id', '')}")
    r.out()
    return 0


def cmd_gaian_list(ctx: CLIContext) -> int:
    resp = ctx.dispatch("/v1/gaian/list")
    if ctx.json_mode:
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1
    if not resp.success:
        ctx.renderer.error(resp.message)
        return 1
    gaians = resp.payload.get("gaians", [])
    ctx.renderer.section(f"GAIANs  ({len(gaians)} registered)")
    if not gaians:
        ctx.renderer.out("  No GAIANs registered. Run: gaia gaian birth")
    else:
        for g in gaians:
            ctx.renderer.gaian_card(g)
    ctx.renderer.out()
    return 0


def cmd_gaian_status(ctx: CLIContext, gaian_id: str) -> int:
    resp = ctx.dispatch("/v1/gaian/status", gaian_id=gaian_id)
    if ctx.json_mode:
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1
    if not resp.success:
        ctx.renderer.error(resp.message, resp.code.value)
        return 1
    ctx.renderer.gaian_detail(resp.payload)
    ctx.renderer.out()
    return 0


# ---------------------------------------------------------------------------
# Talk (interactive session)
# ---------------------------------------------------------------------------

def cmd_talk(ctx: CLIContext, gaian_id: str,
             human_id: str = "cli-user") -> int:
    """
    Interactive session loop.
    Starts a session, runs turns until empty input, ends the session.
    """
    r = ctx.renderer

    # Get GAIAN name for display
    status_resp = ctx.dispatch("/v1/gaian/status", gaian_id=gaian_id)
    if not status_resp.success:
        r.error(status_resp.message, status_resp.code.value)
        return 1
    gaian_name = status_resp.payload.get("display_name") or "[unnamed]"

    # Begin session
    begin_resp = ctx.dispatch(
        "/v1/session/begin",
        gaian_id=gaian_id,
        human_id=human_id,
    )
    if not begin_resp.success:
        r.error(begin_resp.message, begin_resp.code.value)
        return 1

    if not ctx.json_mode:
        r.talk_header(gaian_name, gaian_id)

    turns = []
    try:
        while True:
            content = r.talk_prompt(human_id)
            if not content.strip():
                break

            turn_resp = ctx.dispatch(
                "/v1/session/turn",
                gaian_id=gaian_id,
                content=content,
                human_id=human_id,
            )
            if not turn_resp.success:
                r.error(turn_resp.message, turn_resp.code.value)
                break

            if ctx.json_mode:
                turns.append(turn_resp.to_dict())
            else:
                r.talk_gaian_turn(
                    gaian_name,
                    turn_resp.payload.get("response", ""),
                    turn_resp.payload.get("cognitive_state", {}),
                )

    except KeyboardInterrupt:
        pass

    # End session
    end_resp = ctx.dispatch("/v1/session/end", gaian_id=gaian_id)

    if ctx.json_mode:
        ctx.renderer.json_out({"turns": turns, "end": end_resp.to_dict()})
        return 0

    if end_resp.success:
        ended = end_resp.payload
        r.out()
        r.success(
            f"Session ended. {ended.get('turns', 0)} turn(s). "
            f"Session: {ended.get('session_id', '')[:8]}..."
        )
    r.out()
    return 0


# ---------------------------------------------------------------------------
# Memory commands
# ---------------------------------------------------------------------------

def cmd_memory_recall(
    ctx: CLIContext,
    gaian_id: str,
    limit: int = 10,
    min_importance: float = 0.0,
) -> int:
    resp = ctx.dispatch(
        "/v1/memory/recall",
        caller_id=gaian_id,
        gaian_id=gaian_id,
        limit=limit,
        min_importance=min_importance,
    )
    if ctx.json_mode:
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1
    if not resp.success:
        ctx.renderer.error(resp.message, resp.code.value)
        return 1
    fragments = resp.payload.get("fragments", [])
    ctx.renderer.section(
        f"Memory  ({resp.payload.get('count', 0)} fragment(s))"
    )
    for i, frag in enumerate(fragments):
        ctx.renderer.memory_fragment(frag, i)
    ctx.renderer.out()
    return 0


def cmd_memory_stats(ctx: CLIContext, gaian_id: str) -> int:
    resp = ctx.dispatch(
        "/v1/memory/stats",
        caller_id=gaian_id,
        gaian_id=gaian_id,
    )
    if ctx.json_mode:
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1
    if not resp.success:
        ctx.renderer.error(resp.message, resp.code.value)
        return 1
    p = resp.payload
    ctx.renderer.section("Memory Stats")
    ctx.renderer.kv("Total Fragments", str(p.get("total_fragments", 0)))
    ctx.renderer.kv("Epoch Count",     str(p.get("epoch_count", 0)))
    ctx.renderer.kv("Lifetime Frags",  str(p.get("lifetime_fragments", 0)))
    ctx.renderer.kv("Session Frags",   str(p.get("session_fragments", 0)))
    ctx.renderer.out()
    return 0


# ---------------------------------------------------------------------------
# Filesystem commands
# ---------------------------------------------------------------------------

def cmd_fs_stats(ctx: CLIContext) -> int:
    resp = ctx.dispatch("/v1/fs/stats")
    if ctx.json_mode:
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1
    if not resp.success:
        ctx.renderer.error(resp.message)
        return 1
    p = resp.payload
    ctx.renderer.section("Filesystem")
    ctx.renderer.kv("Root",         p.get("root", ""))
    ctx.renderer.kv("GAIAN Homes",  str(p.get("gaian_count", 0)))
    ctx.renderer.kv("Total Size",   f"{p.get('total_kb', 0)} KB")
    ctx.renderer.out()
    return 0


def cmd_fs_integrity(ctx: CLIContext) -> int:
    resp = ctx.dispatch("/v1/fs/integrity")
    if ctx.json_mode:
        ctx.renderer.json_out(resp.to_dict())
        return 0 if resp.success else 1
    p = resp.payload
    ctx.renderer.section("Filesystem Integrity")
    results = p.get("results", {})
    if not results:
        ctx.renderer.out("  No GAIAN homes found.")
    else:
        for gaian_id, issues in results.items():
            if not issues:
                ctx.renderer.success(f"{gaian_id[:24]}  clean")
            else:
                for issue in issues:
                    ctx.renderer.error(f"{gaian_id[:16]}  {issue}")
    ctx.renderer.out()
    return 0 if p.get("all_clean", True) else 1
