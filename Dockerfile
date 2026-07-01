# =============================================================================
# GAIA OS — Multi-stage Dockerfile
#
# Stage 1 (builder): install Python deps into a venv
# Stage 2 (runtime): copy venv + source, run as non-root
#
# Build:  docker build -t gaia-os .
# Run:    docker run -p 8000:8000 gaia-os
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools (needed for some C-extension wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtualenv so deps are isolated
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies before copying source
# (better layer caching: deps change less often than code)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="GAIA OS"
LABEL org.opencontainers.image.description="The Global Autonomous Intelligence Architecture"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/R0GV3TheAlchemist/GAIA-The-Global-Autonomous-Intelligence-Architecture"

# Non-root user for security
RUN groupadd --gid 1001 gaia \
    && useradd --uid 1001 --gid gaia --shell /bin/bash --create-home gaia

# Copy the virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# App directory
WORKDIR /app

# Copy source (respects .dockerignore)
COPY --chown=gaia:gaia . .

# GAIA data volume — all GAIAN homes, manifests, memory live here
# Mount a host volume or named volume to persist state between restarts.
VOLUME ["/data/gaia"]

# Environment defaults (all overridable at runtime)
ENV GAIA_ROOT=/data/gaia \
    GAIA_HOST=0.0.0.0 \
    GAIA_PORT=8000 \
    GAIA_RELOAD=false \
    GAIA_BEARER_TOKENS="" \
    GAIA_CORS_ORIGINS="*" \
    GAIA_BOOT_NUMBER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health probe (used by Docker and Kubernetes)
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c \
        "import urllib.request; \
         urllib.request.urlopen('http://localhost:${GAIA_PORT}/health').read()"

EXPOSE 8000

# Switch to non-root
USER gaia

# Entrypoint
COPY --chown=gaia:gaia scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
