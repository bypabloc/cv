"""Comandos de mantenimiento del backend serverless.

El backend del portfolio son recursos AWS provisionados con AWS CLI
directo (sin SAM ni CloudFormation): un `manifest.yaml` por Lambda en
`serverless/lambda/services/*` y los fragmentos de recurso compartido en
`serverless/lambda/resources/*`. El ciclo de vida de cada Lambda se opera
con los comandos del modo lambda-controller (`run`, `deploy`, `destroy`,
`status`, `tests`) y `provision-infra` para los recursos compartidos.

Este modulo conserva los comandos transversales: `init` (setup del
entorno) y `clean` (limpieza de caches y artefactos efimeros).
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


# ---------------------------------------------------------------------------
# Setup / Init
# ---------------------------------------------------------------------------


def cmd_init(flags: dict[str, Any]) -> int:
    """Setup inicial: verifica deps (aws CLI + uv) y uv sync del modulo."""
    _ = flags

    if shutil.which('aws') is None:
        _err('AWS CLI no esta instalado')
        print(
            f'{YELLOW}  Instalar con:{NC} '
            f'{CYAN}brew install awscli{NC} o '
            f'{CYAN}pip install awscli{NC}'
        )
        return 1

    if shutil.which('uv') is None:
        _err('uv no esta instalado')
        print(
            f'{YELLOW}  Instalar con:{NC} '
            f'{CYAN}curl -LsSf https://astral.sh/uv/install.sh | sh{NC}'
        )
        return 1

    # uv sync del pyproject del modulo (deps de runtime de los lambdas).
    pyproject = _SERVERLESS_DIR / 'pyproject.toml'
    if pyproject.exists():
        print(_c(CYAN, '$ uv sync --project serverless'))

        result = subprocess.run(  # noqa: S603
            ['uv', 'sync', '--project', str(_SERVERLESS_DIR)],  # noqa: S607
            check=False,
        )
        if result.returncode != 0:
            _err('uv sync fallo')
            return 1

    print()
    print(_c(GREEN, 'OK  serverless/ listo para usar'))
    print(f'{YELLOW}Siguiente paso:{NC}')
    print('  python devtools/run.py serverless provision-infra --stage=dev')
    print('  python devtools/run.py serverless deploy --lambda=db --stage=dev')
    return 0


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------


def cmd_clean(flags: dict[str, Any]) -> int:
    """Elimina caches y artefactos efimeros del backend.

    Limpia, en `serverless/` y en cada lambda de
    `serverless/lambda/services/*/`:
      - `build/` y `build.zip` (artefacto que devtools arma con uv)
      - `core/shared/` vendorizado
      - caches de Python / pytest / ruff / coverage
    """
    targets: list[Path] = [
        _SERVERLESS_DIR / '.pytest_cache',
        _SERVERLESS_DIR / '.ruff_cache',
        _SERVERLESS_DIR / '.coverage',
        _SERVERLESS_DIR / 'htmlcov',
    ]

    # Artefactos efimeros por lambda: build/, build.zip, core/shared/
    # vendorizado, .invoke/ con la respuesta de aws lambda invoke.
    services_dir = _SERVERLESS_DIR / 'lambda' / 'services'
    if services_dir.is_dir():
        for lambda_dir in services_dir.iterdir():
            if not lambda_dir.is_dir():
                continue
            targets.append(lambda_dir / 'build')
            targets.append(lambda_dir / 'build.zip')
            targets.append(lambda_dir / '.invoke')
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
