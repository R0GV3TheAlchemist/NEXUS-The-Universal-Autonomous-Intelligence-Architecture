"""
core/jose_compat.py
===================
JWT compatibility shim — backed by PyJWT.

Previously used python-jose, which pulled in the `ecdsa` package.
`ecdsa` has PYSEC-2026-1325 (Minerva timing attack) with no planned fix.
Migrated to PyJWT>=2.8.0, which uses the `cryptography` C-extension
library exclusively — no ecdsa dependency.

All callers that previously did:
    from core.jose_compat import jwt, JWTError

continue to work unchanged. The jwt object exposes .encode() and .decode()
with identical signatures to python-jose.
"""

from __future__ import annotations

try:
    import jwt
    from jwt.exceptions import InvalidTokenError as JWTError
except ImportError:
    import warnings
    warnings.warn(
        "PyJWT is not installed. JWT operations will raise NotImplementedError. "
        "Install with: pip install PyJWT",
        ImportWarning,
        stacklevel=2,
    )

    class _JWTStub:  # noqa: N801
        def encode(self, *a, **kw):
            raise NotImplementedError("Install PyJWT")

        def decode(self, *a, **kw):
            raise NotImplementedError("Install PyJWT")

    class JWTError(Exception):  # noqa: N818
        pass

    jwt = _JWTStub()


__all__ = ["jwt", "JWTError"]
