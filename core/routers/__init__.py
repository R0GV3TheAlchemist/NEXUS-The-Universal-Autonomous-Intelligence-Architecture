"""
core/routers/__init__.py
Central re-export for all GAIA API routers.
Import from here in server.py to keep it clean.
"""

from core.routers.admin        import router as admin_router
from core.routers.auth_users   import router as auth_users_router
from core.routers.chat         import router as chat_router
from core.routers.gaians       import router as gaians_router
from core.routers.goals_router import router as goals_router          # ★ Goals + Spiritus
from core.routers.health       import router as health_router
from core.routers.internal_router import router as internal_router
from core.routers.memory       import router as memory_router
from core.routers.mood_ws      import router as mood_ws_router
from core.routers.query        import router as query_router
from core.routers.room         import router as room_router
from core.routers.system       import router as system_router
from core.routers.zodiac       import router as zodiac_router

__all__ = [
    "admin_router",
    "auth_users_router",
    "chat_router",
    "gaians_router",
    "goals_router",
    "health_router",
    "internal_router",
    "memory_router",
    "mood_ws_router",
    "query_router",
    "room_router",
    "system_router",
    "zodiac_router",
]
