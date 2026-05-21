"""Comandos de test de la libreria comun del backend.

`cmd_test` / `cmd_test_coverage` corren pytest sobre `serverless/tests/`,
que cubre la libreria comun `serverless/shared/` (cors, logger,
rate_limit, db, cache, turnstile, etc.).

Los tests de cada Lambda viven DENTRO del Lambda
(`serverless/src/<lambda>/tests/`) y se corren con
`serverless test-unit --path=<lambda>` (modo lambda-controller, ver
`lambda_controller.py`).

moto + responses mockean AWS y httpx. Patron python.md: BDD-style en
docstrings, AAA en cuerpo, asserts EXACTOS, coverage >= 80% per-file.
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


def _pytest_base_args(flags: dict[str, Any]) -> list[str]:
    """Comunes a todos los subcomandos test*."""
    args = ['pytest']
    if flags.get('verbose') or flags.get('v'):
        args.append('-v')
    if flags.get('quiet'):
        args.append('-q')
    marker = flags.get('marker')
    if marker:
        args.extend(['-m', marker])
    return args


def cmd_test(flags: dict[str, Any]) -> int:
    """pytest unit + integration con coverage."""
    args = _pytest_base_args(flags)
    threshold = flags.get('coverage_threshold', 80)
    args.extend(
        [
            '--cov=src',
            '--cov-report=term-missing',
            f'--cov-fail-under={threshold}',
            'tests/',
        ]
    )

    print(_c(CYAN, f'$ {" ".join(args)}'))
    result = subprocess.run(args, cwd=_SERVERLESS_DIR, check=False)

    if result.returncode == 0:
        print(_c(GREEN, f'OK  tests pasan + coverage >= {threshold}%'))
    return result.returncode


def cmd_test_coverage(flags: dict[str, Any]) -> int:
    """pytest --cov con threshold per-file 80%."""
    threshold = flags.get('coverage_threshold', 80)
    args = [
        'pytest',
        '--cov=src',
        '--cov-report=term-missing',
        '--cov-report=html',
        f'--cov-fail-under={threshold}',
        'tests/',
    ]

    print(_c(CYAN, f'$ {" ".join(args)}'))
    result = subprocess.run(args, cwd=_SERVERLESS_DIR, check=False)

    if result.returncode == 0:
        report_path = _SERVERLESS_DIR / 'htmlcov' / 'index.html'
        print(_c(GREEN, f'OK  coverage report: {report_path}'))
    else:
        _err(f'Coverage < {threshold}%')
        print(
            f'{YELLOW}  Revisar archivos con cobertura baja y agregar tests{NC}'
        )
    return result.returncode
