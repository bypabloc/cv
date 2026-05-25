"""
Configuracion pytest del lambda <NOMBRE_DEL_SERVICIO>.

Setea las env vars minimas requeridas por settings/config.py y agrega
core/ al sys.path ANTES de importar cualquier modulo del lambda.

NOTA: Los mocks de librerias propietarias del runtime Lambda SOLO se
aplican en tests/unit/. Para tests/integration/ (recursos AWS reales)
los mocks se omiten — eso lo gestiona tests/integration/conftest.py.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock


def _is_integration_run() -> bool:
    """True si pytest fue invocado apuntando a tests/integration."""
    return any('integration' in arg for arg in sys.argv[1:])


# Mock de librerias privadas del runtime Lambda que no estan en pip, para
# que los imports del codigo no fallen en los tests unitarios aislados.
# Solo aplica a unit; integracion usa los recursos/layers reales.
# Si el lambda no usa librerias propietarias, dejar la lista vacia.
if not _is_integration_run():
    for mod_name in [
        # 'bifrost', 'bifrost.logger', 'bifrost.connection_aws',
    ]:
        sys.modules.setdefault(mod_name, MagicMock())

# Env vars minimas para que AppConfig (settings/config.py) cargue sin un
# entorno Lambda real. Agregar las que el servicio necesite.
os.environ.setdefault('ENVIRONMENT', 'dev')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault(
    'ARN_EXAMPLE',
    'arn:aws:lambda:us-east-1:000000000000:function:dummy',
)

# Agregar core/ al sys.path para que los imports absolutos del codigo
# (handler, models., settings., services., utils.) resuelvan en tests.
CORE_ROOT = Path(__file__).resolve().parent.parent / 'core'
sys.path.insert(0, str(CORE_ROOT))
