#!/bin/bash
# =============================================================================
# GAIA OS Container Entrypoint
#
# Responsibilities:
#   1. Ensure GAIA_ROOT exists with correct permissions
#   2. Print a brief boot banner
#   3. Start uvicorn with the configured host/port/workers
#
# All configuration is via environment variables (see Dockerfile ENV defaults).
# Override any variable at `docker run` time with -e GAIA_VAR=value.
# =============================================================================
set -euo pipefail

echo ""
echo "  ――――――――――――――――――――――――――――――――――――――――――――――"
echo "  G A I A  OS — Containerised"
echo "  Global Autonomous Intelligence Architecture"
echo "  ――――――――――――――――――――――――――――――――――――――――――――――"
echo "  GAIA_ROOT    : ${GAIA_ROOT}"
echo "  GAIA_HOST    : ${GAIA_HOST}"
echo "  GAIA_PORT    : ${GAIA_PORT}"
echo "  AUTH         : $([ -n "${GAIA_BEARER_TOKENS}" ] && echo enabled || echo disabled)"
echo "  CORS         : ${GAIA_CORS_ORIGINS}"
echo ""

# Ensure the data directory exists and is writable
mkdir -p "${GAIA_ROOT}"

# Worker count: default to 1 (GAIA session is in-process; horizontal
# scaling requires a shared registry/memory backend, coming in a future layer)
WORKERS=${GAIA_WORKERS:-1}

exec uvicorn server.app:app \
    --host "${GAIA_HOST}" \
    --port "${GAIA_PORT}" \
    --workers "${WORKERS}" \
    --no-access-log
