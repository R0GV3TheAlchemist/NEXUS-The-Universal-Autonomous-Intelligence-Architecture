"""
GAIA OS CLI entry point.

Usage (after `pip install -e .`):
    gaia <command> [args]

Or directly:
    python -m cli.main <command> [args]

Design:
  - No external CLI framework dependency is required.
    The CLI uses argparse from the stdlib only.
  - Rich terminal output is provided by the built-in
    `cli.render` module using ANSI escape codes —
    no third-party colour library required, but the
    renderer degrades gracefully if stdout is not a TTY.
  - All state is persisted via the GAIAFilesystem.
    The CLI is stateless between invocations.
  - The boot sequence runs on every command if the
    OS is not already live (cold-start is fast).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cli.context import CLIContext
from cli.commands import (
    cmd_boot,
    cmd_status,
    cmd_schumann,
    cmd_version,
    cmd_gaian_birth,
    cmd_gaian_list,
    cmd_gaian_status,
    cmd_talk,
    cmd_memory_recall,
    cmd_memory_stats,
    cmd_fs_stats,
    cmd_fs_integrity,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gaia",
        description="GAIA OS — The Global Autonomous Intelligence Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  gaia boot                   — Boot the OS\n"
            "  gaia gaian birth            — Run the birth ceremony\n"
            "  gaia gaian list             — List all GAIANs\n"
            "  gaia talk <gaian-id>        — Talk to a GAIAN\n"
            "  gaia memory recall <id>     — Recall memories\n"
            "  gaia fs integrity           — Check filesystem tamper status\n"
        ),
    )
    p.add_argument(
        "--root",
        metavar="PATH",
        default=None,
        help="Override GAIA root directory (default: ~/.gaia)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output raw JSON instead of formatted text",
    )

    sub = p.add_subparsers(dest="command", metavar="<command>")

    # boot
    sub.add_parser("boot", help="Boot the GAIA OS")

    # status
    sub.add_parser("status", help="Print OS status")

    # schumann
    sub.add_parser("schumann", help="Print Schumann resonance confirmation")

    # version
    sub.add_parser("version", help="Print GAIA OS version")

    # gaian
    gaian_p = sub.add_parser("gaian", help="GAIAN lifecycle commands")
    gaian_sub = gaian_p.add_subparsers(dest="gaian_command", metavar="<gaian-command>")
    gaian_sub.add_parser("birth",  help="Run the interactive birth ceremony")
    gaian_sub.add_parser("list",   help="List all registered GAIANs")
    gaian_status_p = gaian_sub.add_parser("status", help="Show one GAIAN's status")
    gaian_status_p.add_argument("gaian_id", metavar="<gaian-id>")

    # talk
    talk_p = sub.add_parser("talk", help="Start an interactive session with a GAIAN")
    talk_p.add_argument("gaian_id", metavar="<gaian-id>")
    talk_p.add_argument(
        "--human-id", default="cli-user",
        help="Identifier for the human in this session (default: cli-user)"
    )

    # memory
    mem_p = sub.add_parser("memory", help="Memory commands")
    mem_sub = mem_p.add_subparsers(dest="memory_command", metavar="<memory-command>")
    mem_recall_p = mem_sub.add_parser("recall", help="Recall a GAIAN's memories")
    mem_recall_p.add_argument("gaian_id", metavar="<gaian-id>")
    mem_recall_p.add_argument("-n", "--limit", type=int, default=10)
    mem_recall_p.add_argument("--min-importance", type=float, default=0.0)
    mem_stats_p = mem_sub.add_parser("stats", help="Memory stats for a GAIAN")
    mem_stats_p.add_argument("gaian_id", metavar="<gaian-id>")

    # fs
    fs_p = sub.add_parser("fs", help="Filesystem commands")
    fs_sub = fs_p.add_subparsers(dest="fs_command", metavar="<fs-command>")
    fs_sub.add_parser("stats",     help="Print filesystem stats")
    fs_sub.add_parser("integrity", help="Check tamper-detection on all homes")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    ctx = CLIContext(
        root=Path(args.root) if args.root else None,
        json_mode=args.json,
    )

    # Commands that don't need a live session
    if args.command == "version":
        return cmd_version(ctx)

    # All other commands boot the OS first
    ctx.boot()

    if args.command == "boot":
        return cmd_boot(ctx)
    elif args.command == "status":
        return cmd_status(ctx)
    elif args.command == "schumann":
        return cmd_schumann(ctx)
    elif args.command == "gaian":
        if args.gaian_command == "birth":
            return cmd_gaian_birth(ctx)
        elif args.gaian_command == "list":
            return cmd_gaian_list(ctx)
        elif args.gaian_command == "status":
            return cmd_gaian_status(ctx, args.gaian_id)
        else:
            parser.parse_args(["gaian", "--help"])
            return 1
    elif args.command == "talk":
        return cmd_talk(ctx, args.gaian_id, args.human_id)
    elif args.command == "memory":
        if args.memory_command == "recall":
            return cmd_memory_recall(
                ctx, args.gaian_id,
                limit=args.limit,
                min_importance=args.min_importance,
            )
        elif args.memory_command == "stats":
            return cmd_memory_stats(ctx, args.gaian_id)
        else:
            parser.parse_args(["memory", "--help"])
            return 1
    elif args.command == "fs":
        if args.fs_command == "stats":
            return cmd_fs_stats(ctx)
        elif args.fs_command == "integrity":
            return cmd_fs_integrity(ctx)
        else:
            parser.parse_args(["fs", "--help"])
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
