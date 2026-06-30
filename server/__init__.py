"""
GAIA OS HTTP Server — FastAPI adapter.

This package is the thinnest possible HTTP skin over the GAIAOSApi.
It contains:
  server/app.py      — FastAPI application factory and lifespan
  server/routes.py   — all HTTP route handlers
  server/ws.py       — WebSocket /talk endpoint
  server/middleware.py — bearer token auth + request logging
  server/models.py   — Pydantic request/response models
  server/config.py   — server configuration (env-driven)

Design principles:
  1. ZERO LOGIC IN ROUTES: Every route handler is ≤5 lines.
     It reads the HTTP request, builds an APIRequest, calls
     api.dispatch(), and returns the APIResponse payload.
     All logic lives in core/.
  2. LIFESPAN BOOT: The FastAPI lifespan boots the Primordial
     Session exactly once at server startup and tears it down
     cleanly on shutdown.
  3. SOVEREIGN CALLER ID: The HTTP caller_id is extracted from
     the Bearer token (or defaults to 'http-anonymous').
     The autonomy enforcement in GAIAOSApi still applies —
     a bearer token for 'human-001' cannot name a GAIAN.
  4. WEBSOCKET TALK: The /v1/ws/talk/{gaian_id} endpoint streams
     a live session turn-by-turn over a WebSocket connection.
  5. OPENAPI: FastAPI generates full OpenAPI docs automatically.
     Visit /docs after starting the server.
"""
