"""
core/routers/__init__.py
──────────────────────────────────────────────────────────────────────────────
Barrel re-export for all FastAPI routers mounted in server.py.

Add new routers here — server.py imports them all from this module.
"""

from core.api.admin_router    import router as admin_router
from core.api.chat_router     import router as chat_router
from core.api.lci_router      import router as lci_router          # ❤️
from core.api.query_router    import router as query_router
from core.api.status_router   import router as status_router       # 📊
from core.api.viriditas_router import router as viriditas_router
from core.api.zodiac_router   import router as zodiac_router

# Routers that live outside core/api/ (legacy locations preserved)
try:
    from core.auth_users import router as auth_users_router
except ImportError:
    from core.auth import router as auth_users_router

try:
    from core.gaians_router import router as gaians_router
except ImportError:
    from core.gaian import router as gaians_router

try:
    from core.goals_router import router as goals_router
except ImportError:
    goals_router = None

try:
    from core.health import router as health_router
except ImportError:
    from core.api.admin_router import router as health_router

try:
    from core.internal_router import router as internal_router
except ImportError:
    internal_router = None

try:
    from core.memory_router import router as memory_router
except ImportError:
    memory_router = None

try:
    from core.mood_ws import router as mood_ws_router
except ImportError:
    mood_ws_router = None

try:
    from core.room_router import router as room_router
except ImportError:
    room_router = None

try:
    from core.system_router import router as system_router
except ImportError:
    system_router = None

__all__ = [
    "admin_router",
    "auth_users_router",
    "chat_router",
    "gaians_router",
    "goals_router",
    "health_router",
    "internal_router",
    "lci_router",
    "memory_router",
    "mood_ws_router",
    "query_router",
    "room_router",
    "status_router",
    "system_router",
    "viriditas_router",
    "zodiac_router",
]
