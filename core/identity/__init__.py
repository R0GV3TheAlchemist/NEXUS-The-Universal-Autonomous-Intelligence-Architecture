"""
core/identity/
==============
GAIA Identity & Consent Layer — authentication, consent ledger,
and sovereign identity management.

All symbols redirect to flat core/ files until Phase B physical migration.
Note: there is no `Auth` class in this module — use the individual
functions (require_auth, create_access_token, verify_token, etc.) directly.
"""

from core.identity.auth import (
    create_access_token,
    verify_token,
    require_auth,
    optional_auth,
    require_admin,
    TokenPayload,
    TokenRequest,
    TokenResponse,
    auth_router,
)
from core.consent_ledger import ConsentLedger

__all__ = [
    "create_access_token",
    "verify_token",
    "require_auth",
    "optional_auth",
    "require_admin",
    "TokenPayload",
    "TokenRequest",
    "TokenResponse",
    "auth_router",
    "ConsentLedger",
]
