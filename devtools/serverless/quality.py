"""Quality commands for the SAM backend.

Ruff lint + format + typecheck (mypy) sobre serverless/lambda/. Alineado
con el patron de devtools/docker/quality.py pero scoped al modulo
serverless (Python 3.13, no Python 3.14 como devtools).
"""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from shared.console import CYAN
from shared.console import GREEN
from shared.console import NC
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'
# Codigo del backend: services (lambdas) + shared (libreria comun).
_LAMBDA_DIR = _SERVERLESS_DIR / 'lambda'
_SERVICES_DIR = _LAMBDA_DIR / 'services'
_SHARED_DIR = _LAMBDA_DIR / 'shared'


def _resolve_target(flags: dict[str, Any]) -> list[str]:
    """Devuelve la lista de paths a lintear segun flags.

    --files=path1,path2          -> esos paths
    --module-path=lambda/X/      -> ese subdir
    sin flag                     -> lambda/services/ + lambda/shared/
    """
    files = flags.get('files')
    if files:
        return [f.strip() for f in files.split(',')]

    module_path = flags.get('module_path')
    if module_path:
        return [str(_SERVERLESS_DIR / module_path)]

    return [str(_SERVICES_DIR), str(_SHARED_DIR)]


def cmd_lint(flags: dict[str, Any]) -> int:
    """ruff check sobre src/ (+ tests/)."""
    targets = _resolve_target(flags)
    args = ['ruff', 'check']

    output_format = flags.get('output_format')
    if output_format:
        args.extend(['--output-format', output_format])

    args.extend(targets)

    print(_c(CYAN, f'$ {" ".join(args)}'))
    result = subprocess.run(args, cwd=_SERVERLESS_DIR, check=False)
    if result.returncode == 0:
        print(_c(GREEN, 'OK  ruff check sin warnings'))
    return result.returncode


def cmd_lint_fix(flags: dict[str, Any]) -> int:
    """ruff check --fix sobre src/ (+ tests/)."""
    targets = _resolve_target(flags)
    args = ['ruff', 'check', '--fix', *targets]

    print(_c(CYAN, f'$ {" ".join(args)}'))
    result = subprocess.run(args, cwd=_SERVERLESS_DIR, check=False)
    return result.returncode


def cmd_format(flags: dict[str, Any]) -> int:
    """ruff format sobre src/ (+ tests/)."""
    targets = _resolve_target(flags)
    args = ['ruff', 'format', *targets]

    print(_c(CYAN, f'$ {" ".join(args)}'))
    result = subprocess.run(args, cwd=_SERVERLESS_DIR, check=False)
    return result.returncode


def cmd_typecheck(flags: dict[str, Any]) -> int:
    """mypy strict sobre lambda/."""
    module_path = flags.get('module_path', 'lambda')
    args = ['mypy', '--strict', module_path]

    print(_c(CYAN, f'$ {" ".join(args)}'))
    result = subprocess.run(args, cwd=_SERVERLESS_DIR, check=False)

    if result.returncode == 0:
        print(_c(GREEN, 'OK  mypy --strict pasa'))
    else:
        _err('mypy detecto errores de tipo')
        print(
            f'{YELLOW}  Ver .claude/rules/python.md (type hints obligatorios){NC}'
        )
    return result.returncode
