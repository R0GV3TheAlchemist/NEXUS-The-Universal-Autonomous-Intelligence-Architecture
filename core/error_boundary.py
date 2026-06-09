"""
core/error_boundary.py - STUB (Phase C)

Physical implementation has moved to core/infra/error_boundary.py.
This stub re-exports the full public surface so all existing callers
continue to work without any changes.

Note: private names (_code, _envelope, etc.) must be imported explicitly -
wildcard imports do not carry names that begin with an underscore.
"""
from core.infra.error_boundary import *  # noqa: F403
from core.infra.error_boundary import (  # noqa: F401
    _code,
    _envelope,
    _handle_http_exception,
    _handle_unhandled_exception,
    _handle_validation_error,
    _json,
    install_error_handlers,
)
