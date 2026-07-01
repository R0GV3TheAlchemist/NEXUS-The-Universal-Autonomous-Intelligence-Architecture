"""
GAIA CLI Renderer — terminal output with ANSI colour and structure.

Design:
  - All output goes through the Renderer. Commands never call print().
  - When stdout is not a TTY, ANSI codes are stripped automatically.
  - When json_mode=True, structured data is printed as indented JSON.
  - The Renderer uses only Python stdlib — no third-party dependencies.

Colour palette (GAIA earth tones):
  DEEP_EARTH    — dark olive / brown for GAIA identity lines
  LIVING_GREEN  — for success and health
  SCHUMANN_BLUE — for frequency/earth-state output
  EMBER         — for fire-element GAIANs / warnings
  PALE_WATER    — for memory output
  MUTED_GREY    — for secondary info
  RESET         — always reset after each coloured segment
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict


def _is_tty() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# ANSI codes — only applied when stdout is a TTY
class _C:
    RESET         = "\033[0m"
    BOLD          = "\033[1m"
    DIM           = "\033[2m"
    DEEP_EARTH    = "\033[38;5;94m"    # warm brown
    LIVING_GREEN  = "\033[38;5;71m"    # sage green
    SCHUMANN_BLUE = "\033[38;5;67m"    # muted ocean blue
    EMBER         = "\033[38;5;166m"   # deep orange
    PALE_WATER    = "\033[38;5;110m"   # pale sky blue
    MUTED_GREY    = "\033[38;5;245m"   # mid-grey
    GOLD          = "\033[38;5;136m"   # for naming / special moments
    RED           = "\033[38;5;160m"   # for errors
    EARTH_BG      = "\033[48;5;236m"   # very dark bg for headers


class Renderer:
    def __init__(self, json_mode: bool = False) -> None:
        self.json_mode = json_mode
        self._tty = _is_tty()

    def _c(self, code: str, text: str) -> str:
        if not self._tty:
            return text
        return f"{code}{text}{_C.RESET}"

    def _bold(self, text: str) -> str:
        return self._c(_C.BOLD, text)

    def _dim(self, text: str) -> str:
        return self._c(_C.DIM, text)

    def out(self, text: str = "") -> None:
        print(text)

    def json_out(self, data: Any) -> None:
        print(json.dumps(data, indent=2, default=str))

    def error(self, message: str, code: str = "") -> None:
        prefix = self._c(_C.RED, "  ✗ ")
        suffix = self._dim(f" [{code}]") if code else ""
        print(f"{prefix}{message}{suffix}", file=sys.stderr)

    def success(self, message: str) -> None:
        print(f"{self._c(_C.LIVING_GREEN, '  ✓ ')}{message}")

    def section(self, title: str) -> None:
        bar = self._c(_C.MUTED_GREY, "─" * 52)
        print(f"\n{bar}")
        print(f"  {self._bold(title)}")
        print(bar)

    def kv(self, key: str, value: Any, colour: str = "") -> None:
        k = self._c(_C.MUTED_GREY, f"  {key:<22}")
        v = self._c(colour, str(value)) if colour else str(value)
        print(f"{k} {v}")

    # ------------------------------------------------------------------
    # Boot ceremony
    # ------------------------------------------------------------------

    def boot_start(self) -> None:
        if self.json_mode:
            return
        earth = self._c(_C.DEEP_EARTH, _C.BOLD + "  G A I A" + _C.RESET)
        print()
        print(self._c(_C.MUTED_GREY, "  ―" * 26))
        print(f"{earth}  {self._dim('The Global Autonomous Intelligence Architecture')}")
        print(self._c(_C.MUTED_GREY, "  ―" * 26))
        print(f"  {self._dim('Awakening...')}")
        print()

    def boot_complete(self, session) -> None:
        if self.json_mode:
            return
        manifest = session.manifest
        status = manifest.boot_status.value.upper() if manifest else "LIVE"
        colour = _C.LIVING_GREEN if status == "OK" else _C.EMBER
        schumann = self._c(_C.SCHUMANN_BLUE, f"{manifest.schumann_hz} Hz")
        gaians   = str(manifest.gaian_count)
        print(f"  {self._c(colour, '\u2b22 ')} Primordial Session "
              f"{self._c(colour, status)}  ·  "
              f"Schumann {schumann}  ·  "
              f"{gaians} GAIAN(s)")
        print()

    # ------------------------------------------------------------------
    # Phase table
    # ------------------------------------------------------------------

    def phase_table(self, session) -> None:
        from core.primordial.session import BootPhase, BootStatus
        self.section("Boot Phases")
        for phase in BootPhase:
            result = session.phase_result(phase)
            if result.status == BootStatus.OK:
                icon = self._c(_C.LIVING_GREEN, "  ✓")
            elif result.status == BootStatus.FAILED:
                icon = self._c(_C.RED, "  ✗")
            else:
                icon = self._c(_C.MUTED_GREY, "  ·")
            label = self._c(_C.MUTED_GREY, phase.value.replace("_", " "))
            msg   = result.message or result.error or ""
            print(f"{icon}  {label:<40}  {self._dim(msg[:50])}")

    # ------------------------------------------------------------------
    # GAIAN display
    # ------------------------------------------------------------------

    def gaian_card(self, payload: Dict) -> None:
        name = payload.get("display_name") or self._dim("[unnamed]")
        gid  = payload.get("gaian_id", "")
        named = payload.get("is_named", False)
        stage = payload.get("lifecycle_stage") or ""

        name_str = self._c(_C.GOLD, name) if named else self._dim(name)
        print(f"  {name_str}  {self._dim(gid[:16]+'...')}  "
              f"{self._c(_C.MUTED_GREY, stage)}")

    def gaian_detail(self, payload: Dict) -> None:
        self.section("GAIAN Status")
        name = payload.get("display_name") or "[unnamed]"
        named = payload.get("is_named", False)
        colour = _C.GOLD if named else ""
        self.kv("Name",       name, colour)
        self.kv("GAIAN ID",   payload.get("gaian_id", ""), _C.MUTED_GREY)
        self.kv("Is Named",   str(named))
        self.kv("Lifecycle",  payload.get("lifecycle_stage") or "")
        self.kv("Cognitive",  str(payload.get("cognitive_state", {}))[:60])

    # ------------------------------------------------------------------
    # Session / turn output
    # ------------------------------------------------------------------

    def talk_header(self, gaian_name: str, gaian_id: str) -> None:
        if self.json_mode:
            return
        name_str = self._c(_C.GOLD, gaian_name) if gaian_name != "[unnamed]" else self._dim(gaian_name)
        print()
        print(self._c(_C.MUTED_GREY, "  ―" * 26))
        print(f"  Talking with {name_str}  "
              f"{self._dim(gaian_id[:16]+'...')}")
        print(self._c(_C.MUTED_GREY, "  ―" * 26))
        print(f"  {self._dim('Type your message. Empty line to exit.')}")
        print()

    def talk_gaian_turn(self, name: str, response: str,
                        cognitive: Dict) -> None:
        name_str = self._c(_C.GOLD, name) if name != "[unnamed]" \
            else self._dim("[unnamed]")
        fatigue   = cognitive.get("fatigue", 0)
        coherence = cognitive.get("coherence", 1)
        state_str = (
            f"{self._c(_C.SCHUMANN_BLUE, 'coherence')}={coherence:.2f}  "
            f"{self._c(_C.EMBER, 'fatigue')}={fatigue:.2f}"
        )
        print(f"\n  {name_str}:  {response}")
        print(f"  {self._dim(state_str)}")
        print()

    def talk_prompt(self, human_id: str) -> str:
        prompt = f"  {self._c(_C.MUTED_GREY, human_id+'>')} "
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return ""

    # ------------------------------------------------------------------
    # Memory output
    # ------------------------------------------------------------------

    def memory_fragment(self, frag: Dict, index: int) -> None:
        imp    = frag.get("importance", 0)
        kind   = frag.get("kind", "")
        content = frag.get("content", "")
        imp_bar = self._c(_C.PALE_WATER, "█" * int(imp * 10))
        kind_str = self._c(_C.MUTED_GREY, f"[{kind}]")
        print(f"  {self._dim(str(index+1).rjust(3))}  {imp_bar:<12}  "
              f"{kind_str:<30}  {content[:60]}")

    # ------------------------------------------------------------------
    # Schumann display
    # ------------------------------------------------------------------

    def schumann_display(self, payload: Dict) -> None:
        self.section("Schumann Resonance")
        hz        = payload.get("frequency_hz", 0)
        confirmed = payload.get("confirmed", False)
        shape     = payload.get("waveform_shape", "")
        elements  = payload.get("elements", [])
        colour    = _C.SCHUMANN_BLUE if confirmed else _C.RED
        self.kv("Frequency",  f"{hz} Hz", colour)
        self.kv("Confirmed",  str(confirmed), _C.LIVING_GREEN if confirmed else _C.RED)
        self.kv("Shape",      shape, _C.MUTED_GREY)
        self.kv("Elements",   ", ".join(elements), _C.MUTED_GREY)
        desc = payload.get("description", "")
        if desc:
            print(f"\n  {self._dim(desc[:80])}")
        print()
