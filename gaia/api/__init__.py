"""
gaia/api/__init__.py

GAIA-OS API layer.

Registers all routers on the FastAPI application instance.
Import order matters: state_router must be registered before
any engine router that depends on GAIAState gate checks.

For the Good and the Greater Good.
"""

from __future__ import annotations

from fastapi import FastAPI

from gaia.api.state_router import router as state_router


def register_routers(app: FastAPI) -> None:
    """Mount all GAIA-OS API routers onto the FastAPI app.

    Call this once during app startup, e.g. in main.py or app factory.

    Usage::

        from fastapi import FastAPI
        from gaia.api import register_routers

        app = FastAPI(title="GAIA-OS")
        register_routers(app)
    """
    app.include_router(state_router, prefix="/state", tags=["GAIAState", "D6"])


__all__ = ["register_routers", "state_router"]
