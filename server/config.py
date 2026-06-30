"""
GAIA OS Server Configuration.

All values are read from environment variables with sane defaults.
No secrets are hardcoded.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ServerConfig:
    # Network
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # GAIA OS root directory (passed to GAIAFilesystem)
    gaia_root: Optional[Path] = None

    # Auth
    # If bearer_tokens is non-empty, every request must present
    # a valid token. The token value IS the caller_id.
    # Empty list = auth disabled (development mode).
    bearer_tokens: List[str] = field(default_factory=list)
    require_auth: bool = False

    # CORS
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

    # Boot number (incremented externally for multi-boot tracking)
    boot_number: int = 1

    @classmethod
    def from_env(cls) -> "ServerConfig":
        gaia_root_env = os.environ.get("GAIA_ROOT")
        tokens_env = os.environ.get("GAIA_BEARER_TOKENS", "")
        tokens = [t.strip() for t in tokens_env.split(",") if t.strip()]
        cors_env = os.environ.get("GAIA_CORS_ORIGINS", "*")
        cors = [o.strip() for o in cors_env.split(",") if o.strip()]
        return cls(
            host=os.environ.get("GAIA_HOST", "0.0.0.0"),
            port=int(os.environ.get("GAIA_PORT", "8000")),
            reload=os.environ.get("GAIA_RELOAD", "").lower() == "true",
            gaia_root=Path(gaia_root_env) if gaia_root_env else None,
            bearer_tokens=tokens,
            require_auth=len(tokens) > 0,
            cors_origins=cors,
            boot_number=int(os.environ.get("GAIA_BOOT_NUMBER", "1")),
        )
