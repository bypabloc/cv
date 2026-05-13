"""ANSI colour helpers and console messaging for devtools scripts.

Centralizes the small print primitives that every devtools script reuses:
coloured headers, info/ok/warn/err lines, step markers. Importing from
``shared.console`` keeps scripts decoupled from each other (previously they
imported these helpers from ``docker.main``, creating an inverted dependency
where ``test_runner`` and ``e2e`` depended on the docker module).

**Output discipline (CRITICAL for piping/agents)**:

All decorative output (headers, status, step markers, info/ok/warn/err) goes
to **stderr**. This keeps **stdout** clean for actual content (JSON payloads,
table rows, file lists) so callers can pipe to ``jq`` / ``python -c
'json.load(sys.stdin)'`` without the bootstrap or progress text contaminating
the parse.

Concrete examples:

- ``python devtools/run.py docker db-tables --output=json | jq '.[0]'`` works
  because the JSON is the only thing on stdout.
- ``python devtools/run.py verify --json | jq '.files'`` works for the same
  reason.
- Subcommand stdout (``docker compose ...``, ``manage.py migrate``) flows
  through unchanged on stdout, so ``docker logs ... | grep ERROR`` keeps
  working.

Reading order: a script wanting structured console output imports the
relevant helper here and never needs to know about other scripts.
"""

from __future__ import annotations

import sys


RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
DIM = '\033[2m'
NC = '\033[0m'


def colour(code: str, text: str) -> str:
    """Wrap *text* in an ANSI colour escape sequence."""
    return f'{code}{text}{NC}'


# Backwards-compatible short alias used heavily by docker/main.py
_c = colour


def header(title: str) -> None:
    """Print a coloured section header to stderr."""
    width = 60
    print(file=sys.stderr)
    print(colour(CYAN, '=' * width), file=sys.stderr)
    print(colour(CYAN, f' {title}'), file=sys.stderr)
    print(colour(CYAN, '=' * width), file=sys.stderr)


def info(msg: str) -> None:
    print(f'{colour(CYAN, "[INFO]")} {msg}', file=sys.stderr)


def ok(msg: str) -> None:
    print(f'{colour(GREEN, "[OK]")} {msg}', file=sys.stderr)


def warn(msg: str) -> None:
    print(f'{colour(YELLOW, "[WARN]")} {msg}', file=sys.stderr)


def err(msg: str) -> None:
    print(f'{colour(RED, "[ERROR]")} {msg}', file=sys.stderr)


def step(msg: str) -> None:
    print(f'{colour(BOLD, ">>>")} {msg}', file=sys.stderr)


# Underscore aliases for legacy import sites (`from shared.console import _err`).
# The leading underscore signaled "module-private" originally; here we keep both
# spellings so callers can pick whichever reads better at the call site.
_header = header
_info = info
_ok = ok
_warn = warn
_err = err
_step = step
