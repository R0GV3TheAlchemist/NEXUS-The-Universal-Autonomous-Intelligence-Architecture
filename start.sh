#!/usr/bin/env bash
# start.sh — GAIA-OS unified startup script
# Delegates to `gaia start` (gaia/cli.py) after environment validation.
# Preserves direct uvicorn fallback for Docker/CI environments where
# the package may not be installed as an editable install.
set -euo pipefail

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${CYAN}[GAIA]${NC} $*"; }
ok()   { echo -e "${GREEN}[GAIA] ✓${NC} $*"; }
warn() { echo -e "${YELLOW}[GAIA] ⚠${NC} $*"; }
die()  { echo -e "${RED}[GAIA] ✗${NC} $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
GAIA_REF="${GAIA_REF:-feat/obs-rag}"
GAIA_HOST="${GAIA_HOST:-0.0.0.0}"
GAIA_PORT="${GAIA_PORT:-8000}"
GAIA_STORE="${GAIA_STORE:-$HOME/.gaia/data}"
GAIA_FORCE="${GAIA_FORCE:-false}"
GAIA_NO_SERVER="${GAIA_NO_SERVER:-false}"

# ---------------------------------------------------------------------------
# Python version check
# ---------------------------------------------------------------------------
log "Checking Python version..."
PY_VERSION=$(python --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 11 ]]; then
    die "Python >=3.11 required (found $PY_VERSION). Aborting."
fi
ok "Python $PY_VERSION"

# ---------------------------------------------------------------------------
# Load .env if present
# ---------------------------------------------------------------------------
if [[ -f ".env" ]]; then
    log "Loading .env"
    set -a
    # shellcheck source=/dev/null
    source .env
    set +a
    ok ".env loaded"
else
    warn ".env not found — using environment defaults"
fi

# ---------------------------------------------------------------------------
# Install / verify Python package
# ---------------------------------------------------------------------------
if python -c "import gaia.cli" 2>/dev/null; then
    ok "gaia package found"
else
    log "gaia package not found — running pip install -e . ..."
    pip install -e . --quiet || die "pip install failed"
    ok "gaia package installed"
fi

# ---------------------------------------------------------------------------
# Build CLI flags
# ---------------------------------------------------------------------------
CLI_FLAGS="--ref $GAIA_REF --store $GAIA_STORE"

if [[ "$GAIA_FORCE" == "true" ]]; then
    CLI_FLAGS="$CLI_FLAGS --force"
    warn "GAIA_FORCE=true — Canon index will be rebuilt from scratch"
fi

if [[ "$GAIA_NO_SERVER" == "true" ]]; then
    CLI_FLAGS="$CLI_FLAGS --no-server"
    warn "GAIA_NO_SERVER=true — API server will not be launched"
fi

# ---------------------------------------------------------------------------
# Hand off to gaia CLI
# ---------------------------------------------------------------------------
log "Handing off to: python -m gaia.cli start $CLI_FLAGS"
echo ""
exec python -m gaia.cli start $CLI_FLAGS
