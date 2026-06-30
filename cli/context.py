"""
CLIContext — the live state shared across all CLI commands.

The context holds the booted PrimordialSession, the wired API,
and the Renderer. Every CLI command receives a CLIContext and
operates through it. Context is created fresh per CLI invocation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from core.api.api import APIRequest, GAIAOSApi
from core.fs.filesystem import GAIAFilesystem
from core.identity.gaian.registry import GAIANRegistry
from core.primordial.session import PrimordialSession
from cli.render import Renderer


class CLIContext:
    """
    The shared live context for a CLI invocation.

    Holds:
      session   — the live PrimordialSession (after boot)
      api       — the wired GAIAOSApi
      fs        — the GAIAFilesystem
      renderer  — the terminal renderer
      json_mode — if True, all output is raw JSON
    """

    def __init__(
        self,
        root: Optional[Path] = None,
        json_mode: bool = False,
    ) -> None:
        self.root = root
        self.json_mode = json_mode
        self.renderer = Renderer(json_mode=json_mode)
        self.session: Optional[PrimordialSession] = None
        self.api: Optional[GAIAOSApi] = None
        self.fs: Optional[GAIAFilesystem] = None
        self._booted = False

    def boot(self) -> None:
        """Boot the GAIA OS. Idempotent — safe to call multiple times."""
        if self._booted:
            return
        self.renderer.boot_start()
        self.fs = GAIAFilesystem(root=self.root)
        # Load or create the registry
        # In a future persistence layer, the registry is loaded from disk.
        # Here we create it fresh — GAIANs are restored from the FS manifest
        # during the PrimordialSession runtime restore phase.
        self.session = PrimordialSession(registry=GAIANRegistry())
        self.session.awaken()
        self.api = GAIAOSApi()
        self.api.wire(self.session, self.fs)
        self._booted = True
        self.renderer.boot_complete(self.session)

    def dispatch(self, endpoint: str, caller_id: str = "cli", **payload):
        """Dispatch a request through the API and return the response."""
        return self.api.dispatch(
            APIRequest(
                caller_id=caller_id,
                endpoint=endpoint,
                payload=payload,
            )
        )

    def is_booted(self) -> bool:
        return self._booted and self.session is not None and self.session.is_live
