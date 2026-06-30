# GAIA Scripts

Utility scripts for development, deployment, and maintenance.

## Available Scripts

| Script | Purpose |
|---|---|
| `init_world_state.py` | Create a fresh world state with baseline claims |
| `snapshot_inspect.py` | Pretty-print a snapshot JSON file |
| `run_tests.sh` | Run full test suite with coverage report |
| `docker_reset.sh` | Stop, clean, and rebuild all Docker nodes |

## Usage

```bash
# Initialise fresh world state
python scripts/init_world_state.py

# Inspect a snapshot
python scripts/snapshot_inspect.py snapshot_v0.1.json

# Full test suite
bash scripts/run_tests.sh

# Reset Docker environment
bash scripts/docker_reset.sh
```
