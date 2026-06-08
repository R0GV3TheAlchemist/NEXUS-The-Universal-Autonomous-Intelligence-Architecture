"""
core/auth.py
GAIA-APP JWT Authentication Layer — Sprint G-3

Provides:
  - JWT access token creation and verification (HS256)
  - FastAPI dependency: require_auth   — enforces valid token
  - FastAPI dependency: optional_auth  — returns user if token present, else None
  - FastAPI dependency: require_admin  — enforces admin role
  - Token payload: user_id, role ("user" | "admin"), gaian_slug (optional), exp
  - GAIA_SECRET_KEY read from environment (never hardcoded)

Canon Ref: C01 (Sovereignty), C15 (Consent)

Usage:
    from core.auth import require_auth, optional_auth, require_admin, create_access_token

    # Protected endpoint
    @app.post("/gaians/{slug}/chat")
    async def chat(slug: str, req: ChatRequest, user: TokenPayload = Depends(require_auth)):
        ...

    # Admin-only endpoint
    @app.get("/admin/me")
    async def admin_me(user: TokenPayload = Depends(require_admin)):
        ...

Environment variables:
    GAIA_SECRET_KEY   — HS256 signing secret (REQUIRED in production)
    GAIA_TOKEN_EXPIRE — access token lifetime in minutes (default: 60)
    GAIA_ADMIN_KEY    — admin registration key (REQUIRED in production)
"""

from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel as _BaseModel

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

try:
    import jwt as pyjwt
except ImportError:
    raise ImportError(
        "PyJWT is required for GAIA auth. "
        "Add 'PyJWT>=2.8.0' to requirements.txt and run pip install."
    )

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  Config from environment                                            #
# ------------------------------------------------------------------ #

_SECRET_KEY   = os.environ.get("GAIA_SECRET_KEY", "")
_TOKEN_EXPIRE = int(os.environ.get("GAIA_TOKEN_EXPIRE", "60"))  # minutes
_ALGORITHM    = "HS256"
_ADMIN_KEY    = os.environ.get("GAIA_ADMIN_KEY", "")

if not _SECRET_KEY:
    import secrets
    _SECRET_KEY = secrets.token_hex(32)
    logger.warning(
        "[AUTH] GAIA_SECRET_KEY not set — generated ephemeral key. "
        "All tokens will be invalidated on restart. "
        "Set GAIA_SECRET_KEY in your environment for production."
    )


# ------------------------------------------------------------------ #
#  Token Payload                                                      #
# ------------------------------------------------------------------ #

class TokenPayload(BaseModel):
    """Decoded JWT payload. Available as a dependency in protected endpoints."""
    user_id:    str
    role:       str             # "user" | "admin"
    gaian_slug: Optional[str] = None   # bound GAIAN for this user (optional)
    exp:        Optional[int] = None   # expiry timestamp (UTC)


# ------------------------------------------------------------------ #
#  Token Creation                                                     #
# ------------------------------------------------------------------ #

def create_access_token(
    user_id:    str,
    role:       str = "user",
    gaian_slug: Optional[str] = None,
    expires_in: Optional[int] = None,     # minutes; defaults to GAIA_TOKEN_EXPIRE
) -> str:
    """
    Create a signed JWT access token.

    Args:
        user_id:    Unique user identifier (platform UID, DID, etc.)
        role:       "user" or "admin"
        gaian_slug: Optional bound GAIAN slug for this session
        expires_in: Token lifetime in minutes (overrides env default)

    Returns:
        Signed JWT string.
    """
    lifetime = timedelta(minutes=expires_in if expires_in is not None else _TOKEN_EXPIRE)
    expire   = datetime.now(timezone.utc) + lifetime

    payload = {
        "sub":        user_id,
        "role":       role,
        "exp":        expire,
    }
    if gaian_slug:
        payload["gaian_slug"] = gaian_slug

    token = pyjwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    logger.debug(f"[AUTH] Token issued: user_id={user_id} role={role} exp={expire.isoformat()}")
    return token


# ------------------------------------------------------------------ #
#  Token Verification                                                 #
# ------------------------------------------------------------------ #

def verify_token(token: str) -> TokenPayload:
    """
    Verify and decode a JWT token.

    Raises:
        HTTPException 401 if token is invalid, expired, or tampered.

    Returns:
        TokenPayload with decoded claims.
    """
    try:
        decoded = pyjwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        return TokenPayload(
            user_id=decoded["sub"],
            role=decoded.get("role", "user"),
            gaian_slug=decoded.get("gaian_slug"),
            exp=decoded.get("exp"),
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ------------------------------------------------------------------ #
#  FastAPI Bearer Scheme                                              #
# ------------------------------------------------------------------ #

_bearer_scheme          = HTTPBearer(auto_error=True)
_bearer_scheme_optional = HTTPBearer(auto_error=False)


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> TokenPayload:
    """
    FastAPI dependency: requires a valid Bearer JWT.
    Raises 401 if token is missing, expired, or invalid.
    """
    return verify_token(credentials.credentials)


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme_optional),
) -> Optional[TokenPayload]:
    """
    FastAPI dependency: returns TokenPayload if a valid token is present,
    otherwise returns None. Does not raise on missing token.
    Use for endpoints that work for both authed and anonymous users.
    """
    if not credentials:
        return None
    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        return None


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> TokenPayload:
    """
    FastAPI dependency: requires a valid Bearer JWT with role="admin".
    Raises 401 if token is invalid, 403 if role is not admin.
    """
    payload = verify_token(credentials.credentials)
    if payload.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return payload


# ------------------------------------------------------------------ #
#  Auth Endpoints (mounted by server.py)                             #
# ------------------------------------------------------------------ #

auth_router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(_BaseModel):
    user_id:    str
    admin_key:  Optional[str] = None   # provide to receive admin role
    gaian_slug: Optional[str] = None


class TokenResponse(_BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int           # seconds
    role:         str
    user_id:      str


@auth_router.post("/token", response_model=TokenResponse)
def issue_token(req: TokenRequest):
    """
    POST /auth/token

    Issue a JWT access token for a user_id.
    If admin_key matches GAIA_ADMIN_KEY, role is set to "admin".

    In production: replace this with your real auth provider
    (OAuth2, magic link, passkey, etc.). This is the bootstrap
    endpoint for development and initial deployment.

    The user_id is the caller's identity — in a real system this
    would be verified (e.g. verified email, DID proof, etc.).
    """
    if not req.user_id or not req.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required.")

    role = "user"
    if req.admin_key and _ADMIN_KEY and req.admin_key == _ADMIN_KEY:
        role = "admin"
    elif req.admin_key and not _ADMIN_KEY:
        logger.warning("[AUTH] Admin key provided but GAIA_ADMIN_KEY not set — ignoring.")

    token = create_access_token(
        user_id=req.user_id.strip(),
        role=role,
        gaian_slug=req.gaian_slug,
        expires_in=_TOKEN_EXPIRE,
    )
    logger.info(f"[AUTH] Token issued via /auth/token: user_id={req.user_id} role={role}")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=_TOKEN_EXPIRE * 60,
        role=role,
        user_id=req.user_id.strip(),
    )


@auth_router.get("/me", response_model=TokenPayload)
def auth_me(user: TokenPayload = Depends(require_auth)):
    """
    GET /auth/me
    Returns the decoded token payload for the authenticated user.
    Use this to verify a token is valid and inspect its claims.
    """
    return user
