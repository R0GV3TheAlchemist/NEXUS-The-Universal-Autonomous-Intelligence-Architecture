"""conftest.py

Pytest configuration for NEXUS src-python test suite.

Sets up sys.path so that all src-python modules are importable
when pytest is run from the repository root or from src-python/.
"""
import sys
from pathlib import Path

# Ensure src-python/ is on the Python path
_SRC = Path(__file__).parent.parent  # src-python/
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Markers
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "xfail: mark test as expected to fail until implementation is complete",
    )
