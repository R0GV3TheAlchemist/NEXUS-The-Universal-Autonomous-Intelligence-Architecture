# GAIA-OS Makefile
# Usage: make <target>

.PHONY: help install dev test lint type-check start canon doctor clean

PYTHON   ?= python
GAIA_REF ?= feat/obs-rag

help: ## Show this help message
	@echo ""
	@echo "  GAIA-OS — available targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Install Python dependencies
	pip install -e .

dev: ## Install Python dependencies including dev extras
	pip install -e ".[dev]"

test: ## Run the full test suite
	$(PYTHON) -m pytest tests/ -v --tb=short

lint: ## Lint with ruff
	$(PYTHON) -m ruff check .

type-check: ## Type-check with mypy
	$(PYTHON) -m mypy core/ gaia/ --ignore-missing-imports

start: ## Boot GAIA (Canon ingestion + API server)
	$(PYTHON) -m gaia.cli start --ref $(GAIA_REF)

canon: ## Manually ingest (or re-ingest) the Canon
	$(PYTHON) -m gaia.cli ingest-canon --ref $(GAIA_REF)

canon-force: ## Force full Canon re-embed (ignores cached index)
	$(PYTHON) -m gaia.cli ingest-canon --ref $(GAIA_REF) --force

doctor: ## Run environment health checks
	$(PYTHON) -m gaia.cli doctor

status: ## Print Canon index status
	$(PYTHON) -m gaia.cli status

clean: ## Remove Python cache files and build artefacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info/ .mypy_cache/ .ruff_cache/
