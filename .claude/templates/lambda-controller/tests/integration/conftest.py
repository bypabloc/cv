"""
Configuracion pytest de los tests de integracion (E2E).

Diferencias con tests/conftest.py (unit):
  - NO mockea librerias propietarias: usa los recursos AWS reales.
  - Carga env vars del entorno real (o de un archivo de secrets) antes
    de importar el codigo del lambda.
  - Provee fixtures de recursos (cliente Lambda, datos de prueba) con
    cleanup automatico post-test.

Requisitos para correr integracion:
  - Credenciales AWS validas (SSO o IAM key) con permisos de invoke.
  - Acceso de red a los recursos que el lambda consume.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

import os
import sys
from pathlib import Path

import pytest

# core/ al sys.path antes de cualquier import del lambda.
CORE_ROOT = Path(__file__).resolve().parent.parent.parent / 'core'
sys.path.insert(0, str(CORE_ROOT))


def _load_real_env() -> None:
    """
    Carga las env vars del entorno real. Adaptar segun el proyecto:
    leer de un archivo secrets.json, de SSM, o asumir que ya estan en
    el entorno. NUNCA hardcodear secretos aqui.
    """
    required = ['ARN_EXAMPLE']
    missing = [k for k in required if k not in os.environ]
    if missing:
        raise RuntimeError(
            f'Faltan env vars para integracion: {missing}. '
            f'Exportarlas antes de correr tests/integration/.'
        )


_load_real_env()


@pytest.fixture(scope='session')
def aws_region() -> str:
    """Region AWS de los recursos bajo prueba."""
    return os.environ.get('AWS_REGION', 'us-east-1')


@pytest.fixture(autouse=True)
def cleanup_resources():
    """
    Cleanup automatico antes y despues de cada test de integracion.

    Garantiza estado limpio aunque un test previo haya fallado dejando
    datos huerfanos. Adaptar al dominio (borrar registros de prueba,
    objetos S3, etc.).
    """
    # ... cleanup pre-test ...
    yield
    # ... cleanup post-test ...
