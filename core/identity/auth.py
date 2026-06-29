"""auth.py — GAIA Identity & Authentication

Handles login link generation and session management.
No 'magic link' terminology — these are secure, time-limited login links.
See canon/C108_GAIA_Duality_Cryptographic_Identity_Dissociation_Architecture.md
for the cryptographic identity architecture this implements.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field
from typing import Optional


# Login link expiry in seconds (default: 15 minutes)
LOGIN_LINK_TTL_SECONDS: int = int(os.getenv("GAIA_LOGIN_LINK_TTL", "900"))

# Secret key for HMAC signing of login links
_SECRET_KEY: bytes = os.getenv("GAIA_AUTH_SECRET", "change-me-in-production").encode()


@dataclass
class LoginLink:
    """A secure, time-limited login link token."""

    user_id: str
    token: str
    issued_at: float = field(default_factory=time.time)
    ttl_seconds: int = LOGIN_LINK_TTL_SECONDS

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.issued_at) > self.ttl_seconds

    @property
    def is_valid(self) -> bool:
        return not self.is_expired


def generate_login_link_token(user_id: str) -> LoginLink:
    """Generate a cryptographically signed login link token for a user.

    The token is an HMAC-SHA256 of (user_id + timestamp), ensuring
    it cannot be forged without the secret key. This is a login link,
    not a 'magic link' — the security is explicit and measurable.

    Args:
        user_id: The unique identifier of the user requesting authentication.

    Returns:
        A LoginLink dataclass containing the signed token and metadata.
    """
    issued_at = time.time()
    payload = f"{user_id}:{issued_at}".encode()
    token = hmac.new(_SECRET_KEY, payload, hashlib.sha256).hexdigest()
    return LoginLink(user_id=user_id, token=token, issued_at=issued_at)


def verify_login_link_token(
    user_id: str,
    token: str,
    issued_at: float,
) -> bool:
    """Verify a login link token.

    Reconstructs the expected HMAC and compares using constant-time
    comparison to prevent timing attacks.

    Args:
        user_id: The user ID associated with the token.
        token: The token string to verify.
        issued_at: The timestamp at which the token was issued.

    Returns:
        True if the token is valid and not expired; False otherwise.
    """
    payload = f"{user_id}:{issued_at}".encode()
    expected = hmac.new(_SECRET_KEY, payload, hashlib.sha256).hexdigest()
    token_valid = hmac.compare_digest(expected, token)
    time_valid = (time.time() - issued_at) <= LOGIN_LINK_TTL_SECONDS
    return token_valid and time_valid


def send_login_link(user_id: str, email: str, base_url: str) -> Optional[str]:
    """Generate and dispatch a login link to a user's email address.

    This function generates the login link token and returns the full
    link URL. In production, integrate with the email dispatch service
    (see docs/CORRESPONDENCE_ARCHITECTURE.md for the connector spec).

    Args:
        user_id: The unique user identifier.
        email: The user's email address.
        base_url: The base URL of the GAIA application.

    Returns:
        The full login link URL string, or None if generation failed.
    """
    try:
        link = generate_login_link_token(user_id)
        url = f"{base_url}/auth/login?token={link.token}&uid={user_id}&iat={link.issued_at}"
        # TODO: integrate email dispatch connector
        # email_connector.send(to=email, subject='Your GAIA login link', body=url)
        return url
    except Exception:
        return None
