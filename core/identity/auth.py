"""auth.py — GAIA Identity & Authentication

JWT-based authentication layer for GAIA OS (Sprint G-3).

Provides:
  - create_access_token   — mint a signed JWT
  - verify_token          — decode + validate, returns TokenPayload
  - require_auth          — FastAPI dependency: valid token required
  - require_admin         — FastAPI dependency: admin role required
  - optional_auth         — FastAPI dependency: returns payload or None
  - auth_router           — FastAPI router with /auth/token endpoint
  - TokenPayload          — Pydantic model for decoded JWT claims
  - TokenRequest          — Pydantic model for token request body
  - TokenResponse         — Pydantic model for token response body

See canon/C108_GAIA_Duality_Cryptographic_Identity_Dissociation_Architecture.md
for the cryptographic identity architecture this implements.
"""

from __future__ import annotations

import os
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

try:
    import jwt as _jwt
except ImportError:
    _jwt = None  # type: ignore


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_SECRET_KEY: str = os.getenv("GAIA_JWT_SECRET", "gaia-dev-secret-change-in-production")
_ALGORITHM: str = "HS256"
_DEFAULT_EXPIRES_IN: int = 3600  # 1 hour


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class TokenPayload(BaseModel):
    """Decoded JWT claims returned by verify_token."""
    user_id: str
    role: str = "user"
    gaian_slug: Optional[str] = None
    exp: Optional[int] = None


class TokenRequest(BaseModel):
    """Request body for /auth/token."""
    user_id: str
    role: str = "user"
    gaian_slug: Optional[str] = None
    expires_in: int = _DEFAULT_EXPIRES_IN


class TokenResponse(BaseModel):
    """Response body for /auth/token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(
    user_id: str,
    role: str = "user",
    gaian_slug: Optional[str] = None,
    expires_in: int = _DEFAULT_EXPIRES_IN,
) -> str:
    """Mint a signed JWT for the given user."""
    if _jwt is None:
        raise RuntimeError("PyJWT is not installed. Add 'PyJWT>=2.8.0' to requirements.txt.")
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + max(0, expires_in),
    }
    if gaian_slug is not None:
        payload["gaian_slug"] = gaian_slug
    return _jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def verify_token(token: str) -> TokenPayload:
    """Decode and validate a JWT. Raises HTTP 401 on any failure."""
    if _jwt is None:
        raise RuntimeError("PyJWT is not installed.")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing.")
    try:
        data = _jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    return TokenPayload(
        user_id=data.get("user_id", data.get("sub", "")),
        role=data.get("role", "user"),
        gaian_slug=data.get("gaian_slug"),
        exp=data.get("exp"),
    )


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> TokenPayload:
    """FastAPI dependency: rejects request if no valid token is present."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return verify_token(credentials.credentials)


def require_admin(
    payload: TokenPayload = Depends(require_auth),
) -> TokenPayload:
    """FastAPI dependency: rejects request if caller is not an admin."""
    if payload.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return payload


def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[TokenPayload]:
    """FastAPI dependency: returns TokenPayload if token is valid, else None."""
    if credentials is None:
        return None
    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        return None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/token", response_model=TokenResponse)
def issue_token(body: TokenRequest) -> TokenResponse:
    """Issue a JWT for the given user_id and role."""
    token = create_access_token(
        user_id=body.user_id,
        role=body.role,
        gaian_slug=body.gaian_slug,
        expires_in=body.expires_in,
    )
    return TokenResponse(access_token=token, expires_in=body.expires_in)
