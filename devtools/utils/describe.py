"""Schema for the ``describe()`` function exposed by each script's flags.py.

Devtools scripts expose machine-readable metadata so the CLI is
self-documenting: an agent (Claude Code, shell completion, CI) can ask
``--list-commands --output=json`` and parse the result instead of reading
prose docs.

Schema (returned by ``flags.describe()``):

    {
        "name": "docker",                       # script name
        "kind": "subcommand" | "monocommand",   # API style
        "summary": "Short one-line description",
        "commands": [                           # only for kind=subcommand
            {
                "name": "up",
                "summary": "Levantar servicios",
                "flags": ["env", "detach", "build", "service", "profile"],
                "destructive": false
            },
            ...
        ],
        "flags": {                              # global flag definitions
            "env": {
                "type": "choice",
                "choices": ["local", "dev", "test", "prod"],
                "default": "local",
                "summary": "Ambiente Docker"
            },
            "verbose": {
                "type": "bool",
                "default": false,
                "summary": "Modo verbose"
            },
            ...
        }
    }

A "monocommand" script has no ``commands``: the script itself is the unit
and all parametrization is via flags (``test_runner``, ``scan``, ``verify``,
``upgrade_deps``, ``init``, ``hooks``, ``e2e``).
"""

from __future__ import annotations

from typing import Any
from typing import Literal
from typing import TypedDict


class FlagSpec(TypedDict, total=False):
    """Per-flag schema entry."""

    type: Literal['bool', 'string', 'int', 'choice', 'list']
    choices: list[str]
    default: Any
    summary: str
    required: bool


class CommandSpec(TypedDict, total=False):
    """Per-command schema entry (only for subcommand-style scripts)."""

    name: str
    summary: str
    flags: list[str]
    destructive: bool
    deprecated: bool


class ScriptDescribe(TypedDict, total=False):
    """Top-level schema returned by ``flags.describe()``."""

    name: str
    kind: Literal['subcommand', 'monocommand']
    summary: str
    commands: list[CommandSpec]
    flags: dict[str, FlagSpec]


def empty_describe(name: str, kind: str = 'monocommand') -> ScriptDescribe:
    """Helper to build a minimal describe payload for scripts that have not
    declared one yet. Keeps ``--list-commands`` from blowing up while we
    incrementally migrate every flags.py."""
    return {
        'name': name,
        'kind': kind,  # type: ignore[typeddict-item]
        'summary': '',
        'commands': [],
        'flags': {},
    }
