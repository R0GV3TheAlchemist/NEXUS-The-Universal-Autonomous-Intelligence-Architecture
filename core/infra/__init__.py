"""
core/infra/__init__.py
GAIA Infrastructure Layer — public surface

Only names that actually exist in their respective modules are exported here.
Do not add a name unless you have verified it exists in the source file.
"""

# action_gate.py  →  class ActionGate, enum RiskTier
from .action_gate           import ActionGate, RiskTier

# error_boundary.py  →  function install_error_handlers  (no ErrorBoundary class)
from .error_boundary        import install_error_handlers

# rate_limiter.py  →  class RateLimitMiddleware, factory rate_limit  (no RateLimiter class)
from .rate_limiter          import RateLimitMiddleware, rate_limit

# server_models.py  →  Pydantic request/response models  (no ServerConfig class)
from .server_models         import (
    QueryRequest,
    ChatRequest,
    CreateGaianRequest,
    BirthRequest,
    RememberRequest,
    VisibleMemoryRequest,
    SetGaianRequest,
    ConsentRequest,
)

# server_state.py  →  module-level singletons accessed via getters  (no ServerState class)
from .server_state          import (
    get_action_gate,
    get_magnum_opus_report,
    set_magnum_opus_report,
)

# sqlite repositories  →  classes confirmed present in their files
from .sqlite_lifecycle_repository   import SqliteLifecycleRepository
from .sqlite_stewardship_repository import SqliteStewardshipRepository

__all__ = [
    # action gate
    "ActionGate",
    "RiskTier",
    # error boundary
    "install_error_handlers",
    # rate limiting
    "RateLimitMiddleware",
    "rate_limit",
    # request/response models
    "QueryRequest",
    "ChatRequest",
    "CreateGaianRequest",
    "BirthRequest",
    "RememberRequest",
    "VisibleMemoryRequest",
    "SetGaianRequest",
    "ConsentRequest",
    # server state accessors
    "get_action_gate",
    "get_magnum_opus_report",
    "set_magnum_opus_report",
    # repositories
    "SqliteLifecycleRepository",
    "SqliteStewardshipRepository",
]
