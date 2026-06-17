"""
core/jose_compat.py
===================
python-jose / jose compatibility shim.

The GAIA-OS codebase uses JWT tokens for API authentication (api/auth.py).
The JWT library is `python-jose`, installed as:

    pip install python-jose[cryptography]

However, some import chains use `from jose import jwt` (the package
install name) and some use `from python_jose import jwt` (the module name).
This shim resolves both forms transparently so tests and application code
can import from a stable internal path:

    from core.jose_compat import jwt, JWTError

Install instruction (add to pip install -e ".[dev]"):
    python-jose[cryptography]>=3.3.0
"""

from __future__ import annotations

try:
    from jose import jwt, JWTError  # python-jose package
except ImportError:
    try:
        from python_jose import jwt, JWTError  # alternate install name
    except ImportError:
        # Last-resort stub so collection never fails even without the package.
        # Any call to jwt.encode / jwt.decode will raise NotImplementedError.
        import warnings
        warnings.warn(
            "python-jose is not installed. JWT operations will raise NotImplementedError. "
            "Install with: pip install python-jose[cryptography]",
            ImportWarning,
            stacklevel=2,
        )

        class _JWTStub:  # noqa: N801
            def encode(self, *a, **kw):
                raise NotImplementedError("Install python-jose[cryptography]")

            def decode(self, *a, **kw):
                raise NotImplementedError("Install python-jose[cryptography]")

        class JWTError(Exception):  # noqa: N818
            pass

        jwt = _JWTStub()


__all__ = ["jwt", "JWTError"]
