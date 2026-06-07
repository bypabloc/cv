"""Configuracion raiz de pytest para el arbol E2E (`tests/`).

Declara las opciones CLI compartidas por los modulos `api`, `admin` y
`app` (`--env`, `--aws-profile`, `--samples`, `--keep-data`, `--lambda`)
y las expone como fixtures de sesion. El comando `e2e/main.py` invoca
pytest pasando estas opciones segun los flags del usuario.

Asegura que el paquete top-level `shared.*` (en `tests/shared/`) sea
importable agregando este directorio (`tests/`) al `sys.path`. Esto duplica
lo que declara `tests/pyproject.toml` (`pythonpath = ['.']`), para que los
imports funcionen tambien cuando pytest se invoca con un rootdir distinto.
"""

from __future__ import annotations

import os
import sys

import pytest


# tests/ al frente del sys.path -> `import shared.config` resuelve a
# tests/shared/ (NUNCA a devtools/shared/, que es otro paquete `shared`).
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Registra las opciones CLI del harness E2E.

    Given una invocacion de pytest desde `e2e/main.py` o directa,
    When se parsean los argumentos,
    Then quedan disponibles `--env`, `--aws-profile`, `--samples`,
    `--keep-data` y `--lambda` con sus defaults.
    """
    parser.addoption(
        '--env',
        action='store',
        default='dev',
        choices=('dev', 'stage'),
        help='Entorno de deploy contra el que correr (dev|stage). NUNCA prod.',
    )
    parser.addoption(
        '--aws-profile',
        action='store',
        default=None,
        help='Perfil AWS CLI para SSM/Lambda/DynamoDB (default: del shell).',
    )
    parser.addoption(
        '--samples',
        action='store',
        type=int,
        default=5,
        help='Muestras por caso del modulo api (timing cold/warm).',
    )
    parser.addoption(
        '--keep-data',
        action='store_true',
        default=False,
        help='No limpiar los datos sinteticos creados (debug).',
    )
    parser.addoption(
        '--lambda',
        action='store',
        default=None,
        help='Limita el modulo api a un solo Lambda (cv|auth|users|...).',
    )


@pytest.fixture(scope='session')
def env(request: pytest.FixtureRequest) -> str:
    """Entorno de deploy elegido (`dev` | `stage`)."""
    return str(request.config.getoption('--env'))


@pytest.fixture(scope='session')
def aws_profile(request: pytest.FixtureRequest) -> str | None:
    """Perfil AWS CLI elegido, o None (usa el del shell)."""
    value = request.config.getoption('--aws-profile')
    return str(value) if value is not None else None


@pytest.fixture(scope='session')
def samples(request: pytest.FixtureRequest) -> int:
    """Muestras por caso del modulo api."""
    return int(request.config.getoption('--samples'))


@pytest.fixture(scope='session')
def keep_data(request: pytest.FixtureRequest) -> bool:
    """True si NO se deben limpiar los datos sinteticos (debug)."""
    return bool(request.config.getoption('--keep-data'))


@pytest.fixture(scope='session')
def lambda_filter(request: pytest.FixtureRequest) -> str | None:
    """Lambda unico al que limitar el modulo api, o None (todos)."""
    value = request.config.getoption('--lambda')
    return str(value) if value is not None else None
