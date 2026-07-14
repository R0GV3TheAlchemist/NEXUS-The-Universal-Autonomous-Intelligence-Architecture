"""
api/auth.py — GAIA-OS Authentication

SQLite-backed user store with bcrypt passwords and JWT tokens.
Fully self-hosted — no external auth service required.

Endpoints:
  POST /auth/register   { email, username, password }  → AuthResult
  POST /auth/login      { username, password }          → AuthResult
  GET  /auth/me         Bearer token required           → UserInfo

Setup (auto-runs on first import):
  pip install bcrypt PyJWT

DB: data/users.db (SQLite, created automatically)
"""

import os
import sqlite3
import secrets
import logging
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator

log = logging.getLogger("gaia.auth")

# ── Config ──────────────────────────────────────────────────────────────────────────────────────

_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.path.join(_ROOT, "data", "users.db")

# Secret key — stable across restarts via env var or auto-generated and persisted
_SECRET_KEY_FILE = os.path.join(_ROOT, "data", ".jwt_secret")

def _get_secret_key() -> str:
    os.makedirs(os.path.dirname(_SECRET_KEY_FILE), exist_ok=True)
    if os.path.exists(_SECRET_KEY_FILE):
        with open(_SECRET_KEY_FILE) as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(_SECRET_KEY_FILE, "w") as f:
        f.write(key)
    return key

SECRET_KEY    = os.environ.get("GAIA_JWT_SECRET") or _get_secret_key()
ALGORITHM     = "HS256"
TOKEN_EXPIRY  = timedelta(days=7)

# ── DB ──────────────────────────────────────────────────────────────────────────────────────

def _init_db():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                email         TEXT UNIQUE NOT NULL,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL DEFAULT 'user',
                created_at    TEXT NOT NULL
            )
        """)
        conn.commit()

_init_db()

@contextmanager
def _db():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ── Schemas ──────────────────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    str
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def username_valid(cls, v: str) -> str:
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]{2,32}$', v):
            raise ValueError('Username must be 2–32 chars: letters, numbers, _ or -')
        return v

    @field_validator('password')
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class LoginRequest(BaseModel):
    username: str   # accepts username or email
    password: str


class AuthResult(BaseModel):
    access_token: str
    user_id:      str
    username:     str
    email:        str
    role:         str


class UserInfo(BaseModel):
    user_id:    str
    username:   str
    email:      str
    role:       str
    created_at: str

# ── JWT helpers ─────────────────────────────────────────────────────────────────────────────────

def _create_token(user_id: str, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + TOKEN_EXPIRY
    return jwt.encode(
        {"sub": user_id, "username": username, "role": role, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# ── Auth dependency ────────────────────────────────────────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode_token(credentials.credentials)


# ── Router ───────────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResult)
def register(req: RegisterRequest):
    import uuid
    with _db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ? OR username = ?",
            (req.email.lower(), req.username.lower()),
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already registered.",
            )

        user_id     = str(uuid.uuid4())
        pw_hash     = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
        created_at  = datetime.now(timezone.utc).isoformat()

        conn.execute(
            "INSERT INTO users (id, email, username, password_hash, role, created_at) VALUES (?,?,?,?,?,?)",
            (user_id, req.email.lower(), req.username, pw_hash, "user", created_at),
        )
        conn.commit()

    log.info(f"[Auth] New user registered: {req.username}")
    token = _create_token(user_id, req.username, "user")
    return AuthResult(
        access_token=token,
        user_id=user_id,
        username=req.username,
        email=req.email.lower(),
        role="user",
    )


@router.post("/login", response_model=AuthResult)
def login(req: LoginRequest):
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (req.username.lower(), req.username.lower()),
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    if not bcrypt.checkpw(req.password.encode(), row["password_hash"].encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    log.info(f"[Auth] User logged in: {row['username']}")
    token = _create_token(row["id"], row["username"], row["role"])
    return AuthResult(
        access_token=token,
        user_id=row["id"],
        username=row["username"],
        email=row["email"],
        role=row["role"],
    )


@router.get("/me", response_model=UserInfo)
def me(current_user: dict = Depends(get_current_user)):
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (current_user["sub"],)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserInfo(
        user_id=row["id"],
        username=row["username"],
        email=row["email"],
        role=row["role"],
        created_at=row["created_at"],
    )
