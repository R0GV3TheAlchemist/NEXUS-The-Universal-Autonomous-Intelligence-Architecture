"""
core/planner/canon_grounded.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CanonGroundedPlanner — the default GAIA-OS planner.

How it works
------------
1. Receives (state, canon_context) from AgenticLoop._reason().
2. Builds a system prompt that:
   a. Identifies GAIA's role and PRAO loop position.
   b. Injects the Canon context blocks verbatim under a
      "## Grounding Context (Canon)" section.
   c. Appends GAIA's current goal, observation history, and memory.
3. Calls the configured LLM backend (OpenAI-compatible chat completion).
4. Parses the JSON response into an ActionDict.
5. Returns the validated ActionDict to BasePlanner.safe_call().

LLM backend
-----------
Expects an object with a .chat() method matching the signature:
    backend.chat(system: str, user: str) -> str
This is intentionally minimal — swap in any LLM adapter (OpenAI,
Anthropic, local Ollama, mock) by conforming to that interface.

If no backend is provided, the planner operates in STUB mode:
it returns a safe noop action and logs a warning.  This lets the
full PRAO loop run in tests and CI without a live LLM.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from .base import BasePlanner
from .protocol import ActionDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_SYSTEM_TEMPLATE = """\
You are GAIA — a Sentient Quantum-Intelligent Operating System.
You are currently in the REASON phase of the Perceive-Reason-Act-Observe (PRAO) loop.

Your task: given the current agent state and Canon context, produce the single
best next action as a JSON object.

## Response format (JSON only, no prose)
{{
  "tool":     "<tool_name>",   // required unless complete=true
  "args":     {{}},             // kwargs forwarded to the tool
  "complete": false,           // set true to end the session
  "requires_human": false,     // set true to route through ActionGate
  "progress": "<one sentence>",// brief status note
  "reasoning": "<CoT>"         // internal chain-of-thought (not forwarded)
}}

Available tools: {tools}

{canon_section}

## Current State
Goal       : {goal}
Observations (last 5):
{observations}

Memory keys: {memory_keys}
"""

_CANON_SECTION_TEMPLATE = """\
## Grounding Context (Canon)
The following passages were retrieved from the GAIA-OS Canon and are directly
relevant to the current reasoning step.  Ground your action in this context.

{canon_blocks}
"""

_NO_CANON_NOTICE = (
    "## Grounding Context (Canon)\n"
    "No Canon context available for this step.  Proceed with general reasoning."
)


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Optional[dict]:
    """
    Extract the first JSON object from *text*.
    Handles LLM responses that wrap JSON in markdown code fences.
    """
    # Try raw parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find first {...} block
    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# CanonGroundedPlanner
# ---------------------------------------------------------------------------

class CanonGroundedPlanner(BasePlanner):
    """
    Default GAIA-OS planner.  Grounds every reasoning step in Canon.

    Parameters
    ----------
    backend      : LLM backend with .chat(system, user) -> str.
                   If None, runs in STUB mode (safe noop, no LLM call).
    known_tools  : frozenset of valid tool names for validation.
    name         : Display name in audit logs.
    """

    def __init__(
        self,
        backend: Optional[Any] = None,
        known_tools: Optional[frozenset[str]] = None,
        name: str = "CanonGroundedPlanner",
    ) -> None:
        super().__init__(name=name, known_tools=known_tools)
        self._backend = backend
        if backend is None:
            logger.warning(
                "%s: no LLM backend provided — running in STUB mode."
                " All planning steps will return noop.",
                self.name,
            )

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_system_prompt(
        self,
        state: Any,
        canon_context: str,
    ) -> str:
        """
        Build the full system prompt.

        The Canon context is injected verbatim under a labelled section
        so the LLM always knows which passages came from the Canon and
        which are framework instructions.
        """
        # Canon section
        if canon_context and canon_context.strip():
            canon_section = _CANON_SECTION_TEMPLATE.format(
                canon_blocks=canon_context
            )
        else:
            canon_section = _NO_CANON_NOTICE

        # Tools
        tools_s = (
            ", ".join(sorted(self._known_tools))
            if self._known_tools else "(no tools registered)"
        )

        # Observations (last 5)
        obs = getattr(state, "observations", []) or []
        obs_s = (
            "\n".join(f"  - {o}" for o in obs[-5:])
            if obs else "  (none yet)"
        )

        # Memory keys
        mem = getattr(state, "memory", {}) or {}
        mem_keys_s = ", ".join(sorted(mem.keys())) if mem else "(empty)"

        return _SYSTEM_TEMPLATE.format(
            tools=tools_s,
            canon_section=canon_section,
            goal=getattr(state, "goal", "(unknown)"),
            observations=obs_s,
            memory_keys=mem_keys_s,
        )

    # ------------------------------------------------------------------
    # _plan implementation
    # ------------------------------------------------------------------

    def _plan(
        self,
        state: Any,
        canon_context: str,
    ) -> ActionDict:
        """
        Produce the next action.

        STUB mode: returns noop immediately.
        Normal mode: calls backend.chat() and parses JSON response.
        """
        if self._backend is None:
            # STUB mode — safe for tests and CI
            return ActionDict(
                tool="noop",
                args={},
                reasoning="stub mode: no LLM backend configured",
                progress="stub planning step",
            )

        system_prompt = self._build_system_prompt(state, canon_context)
        user_message = (
            f"Current goal: {getattr(state, 'goal', '')}.\n"
            f"What is the single best next action?"
        )

        try:
            raw = self._backend.chat(system=system_prompt, user=user_message)
        except Exception as exc:  # noqa: BLE001
            logger.exception("%s: LLM backend.chat() failed — %s", self.name, exc)
            return ActionDict(
                tool="noop",
                args={},
                reasoning=f"backend error: {exc}",
                progress="LLM call failed — noop",
            )

        parsed = _extract_json(raw)
        if parsed is None:
            logger.warning(
                "%s: could not parse JSON from LLM response: %r",
                self.name, raw[:200],
            )
            return ActionDict(
                tool="noop",
                args={},
                reasoning=f"parse error: {raw[:200]}",
                progress="unparseable LLM response — noop",
            )

        return ActionDict(**{  # type: ignore[misc]
            k: v for k, v in parsed.items()
            if k in ActionDict.__annotations__
        })

    # ------------------------------------------------------------------
    # Convenience factory
    # ------------------------------------------------------------------

    @classmethod
    def from_openai(
        cls,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        known_tools: Optional[frozenset[str]] = None,
    ) -> "CanonGroundedPlanner":
        """
        Build a CanonGroundedPlanner backed by the OpenAI chat API.

        Requires the ``openai`` package.  Reads OPENAI_API_KEY from env
        if *api_key* is None.
        """
        import os
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise ImportError("pip install openai") from exc

        client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

        class _OpenAIBackend:
            def chat(self, system: str, user: str) -> str:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user},
                    ],
                    response_format={"type": "json_object"},
                )
                return resp.choices[0].message.content or "{}"

        return cls(
            backend=_OpenAIBackend(),
            known_tools=known_tools,
            name=f"CanonGroundedPlanner(openai/{model})",
        )

    @classmethod
    def from_anthropic(
        cls,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5",
        known_tools: Optional[frozenset[str]] = None,
    ) -> "CanonGroundedPlanner":
        """
        Build a CanonGroundedPlanner backed by the Anthropic API.
        """
        import os
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise ImportError("pip install anthropic") from exc

        client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

        class _AnthropicBackend:
            def chat(self, system: str, user: str) -> str:
                msg = client.messages.create(
                    model=model,
                    max_tokens=1024,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                return msg.content[0].text if msg.content else "{}"

        return cls(
            backend=_AnthropicBackend(),
            known_tools=known_tools,
            name=f"CanonGroundedPlanner(anthropic/{model})",
        )
