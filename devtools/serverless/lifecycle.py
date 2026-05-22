"""Comandos de mantenimiento del backend serverless.

El backend del portfolio son stacks CloudFormation independientes (un
`manifest.yaml` por Lambda en `serverless/lambda/services/*`, un stack por
recurso compartido en `serverless/lambda/resources/*`). El ciclo de vida
de cada stack se opera con los comandos del modo lambda-controller
(`sam-generate`, `run`, `deploy`, `tests`) y `deploy-infra` para los
recursos compartidos.

Este modulo conserva solo los comandos transversales que NO dependen de
un SAM template monolitico: `init` (setup del entorno) y `clean`
(limpieza de caches y artefactos efimeros).
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Any

from shared.console import CYAN
from shared.console import GREEN
from shared.console import NC
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


# Path al modulo serverless/ desde el root del repo.
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'


def _ensure_sam_available() -> None:
    """Verifica que `sam` esta en el PATH; aborta con hint si falta."""
    if shutil.which('sam') is None:
        _err('AWS SAM CLI no esta instalado')
        print(
            f'{YELLOW}  Instalar con:{NC} '
            f'{CYAN}brew install aws-sam-cli{NC} '
            f'o {CYAN}pip install aws-sam-cli{NC}',
        )
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Setup / Init
# ---------------------------------------------------------------------------


def cmd_init(flags: dict[str, Any]) -> int:
    """Setup inicial: verifica deps (sam, aws CLI) y uv sync del modulo."""
    _ = flags
    _ensure_sam_available()

    if shutil.which('aws') is None:
        _err('AWS CLI no esta instalado')
        print(
            f'{YELLOW}  Instalar con:{NC} '
            f'{CYAN}brew install awscli{NC} o '
            f'{CYAN}pip install awscli{NC}'
        )
        return 1

    # uv sync del pyproject del modulo (deps de runtime de los lambdas).
    pyproject = _SERVERLESS_DIR / 'pyproject.toml'
    if pyproject.exists():
        print(_c(CYAN, '$ uv sync --project serverless'))
        result = subprocess.run(
            ['uv', 'sync', '--project', str(_SERVERLESS_DIR)],
            check=False,
        )
        if result.returncode != 0:
            _err('uv sync fallo')
            return 1

    print()
    print(_c(GREEN, 'OK  serverless/ listo para usar'))
    print(f'{YELLOW}Siguiente paso:{NC}')
    print('  python devtools/run.py serverless deploy-infra --stage=dev')
    print('  python devtools/run.py serverless deploy --lambda=db --stage=dev')
    return 0


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------


def cmd_clean(flags: dict[str, Any]) -> int:
    """Elimina caches y artefactos efimeros del backend.

    Limpia, en `serverless/` y en cada lambda de
    `serverless/lambda/services/*/`:
      - `.aws-sam/` (build de SAM)
      - `template.yaml` efimero generado por sam-generate
      - `build/` y `core/shared/` vendorizados
      - caches de Python / pytest / ruff / coverage
    """
    targets: list[Path] = [
        _SERVERLESS_DIR / '.aws-sam',
        _SERVERLESS_DIR / '.pytest_cache',
        _SERVERLESS_DIR / '.ruff_cache',
        _SERVERLESS_DIR / '.coverage',
        _SERVERLESS_DIR / 'htmlcov',
    ]

    # Artefactos efimeros por lambda: template.yaml, .aws-sam/, build/,
    # core/shared/ vendorizado.
    services_dir = _SERVERLESS_DIR / 'lambda' / 'services'
    if services_dir.is_dir():
        for lambda_dir in services_dir.iterdir():
            if not lambda_dir.is_dir():
                continue
            targets.append(lambda_dir / 'template.yaml')
            targets.append(lambda_dir / '.aws-sam')
            targets.append(lambda_dir / 'build')
            targets.append(lambda_dir / 'core' / 'shared')

    # __pycache__ recursivo.
    targets.extend(_SERVERLESS_DIR.rglob('__pycache__'))

    if flags.get('dry_run'):
        for t in targets:
            if t.exists():
                print(_c(YELLOW, f'[dry-run] rm -rf {t}'))
        return 0

    for t in targets:
        if t.exists():
            print(_c(CYAN, f'rm -rf {t}'))
            if t.is_dir():
                shutil.rmtree(t)
            else:
                t.unlink()

    print(_c(GREEN, 'OK  caches y artefactos efimeros limpios'))
    return 0
