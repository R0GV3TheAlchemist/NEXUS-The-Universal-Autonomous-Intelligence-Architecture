"""
Root conftest.py — ensures the repo root is on sys.path so that
`from core.spectral.<color>.X import ...` works in all pytest invocations
regardless of how pytest is launched (tox, direct, CI matrix).
"""
import sys
import pathlib

# Insert repo root at front of sys.path if not already present
_ROOT = str(pathlib.Path(__file__).parent.resolve())
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
