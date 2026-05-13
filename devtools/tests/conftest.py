"""Pytest config for devtools unit tests.

Adds devtools/ to sys.path so tests can import shared.* directly.
Devtools tests run in local Python (3.12), not in Docker.
"""

from pathlib import Path
import sys


_DEVTOOLS_ROOT = Path(__file__).resolve().parent.parent
if str(_DEVTOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEVTOOLS_ROOT))
