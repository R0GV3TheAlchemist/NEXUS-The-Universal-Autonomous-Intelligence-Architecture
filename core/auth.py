"""
core/auth.py
============
Backward-compatibility re-export shim.

The canonical implementation of GAIA's JWT auth layer lives in
`core/identity/auth.py`.  This module re-exports every public symbol
so that legacy import paths like::

    from core.auth import require_auth, create_access_token, TokenPayload

continue to work without changes.

Note: there is no `Auth` class — use the individual functions directly.
Do NOT add new auth logic here — use core.identity.auth directly.

Canon Ref: C01 (Sovereignty), C15 (Consent)
"""

from core.identity.auth import (  # noqa: F401  (deliberate re-exports)
    TokenPayload,
    create_access_token,
    verify_token,
    require_auth,
    optional_auth,
    require_admin,
    auth_router,
    TokenRequest,
    TokenResponse,
)

__all__ = [
    "TokenPayload",
    "create_access_token",
    "verify_token",
    "require_auth",
    "optional_auth",
    "require_admin",
    "auth_router",
    "TokenRequest",
    "TokenResponse",
]
