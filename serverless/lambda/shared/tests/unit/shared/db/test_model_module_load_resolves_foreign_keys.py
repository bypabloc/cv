"""
Given un MODULO de modelo de `shared.db.models` importado en AISLAMIENTO
     (como hace cualquier consumidor: `from shared.db.models.auth.user
     import AuthUser`),
When se resuelven todas las ForeignKey de las tablas que quedan registradas,
Then ninguna lanza `NoReferencedTableError`: cada modulo importa los modulos
     concretos de sus FK-targets (intra y cross-domain).

Guard del refactor no-barrels. Antes los `__init__.py` de dominio
re-exportaban TODO el dominio, asi que importar cualquier clase cargaba el
dominio entero y las FK intra-dominio resolvian de rebote. Sin barrels, cada
modulo debe declarar (importar) sus FK-targets concretos o la FK no resuelve
en el INSERT/UPDATE de su tabla (`NoReferencedTableError` -> 500 / data-loss
async). Ej: `auth/user.py` importa `cv/profile.py` (FK auth_users.profile_id
-> cv_profiles); `visitor/tracking.py` importa `taxonomy/event_type.py`.

Este test protege contra que alguien (a) agregue una FK sin importar el
modulo target, o (b) quite uno de esos imports. Recorre TODOS los modulos de
modelo y los importa uno por uno en un SUBPROCESO (el MetaData de SQLAlchemy
es global por proceso; in-process un modulo contaminaria a los demas y
ocultaria el aislamiento real). Ver `.claude/rules/lambda-shared-imports.md`.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import shared

pytestmark = pytest.mark.unit

# Dir que contiene el paquete `shared` (.../serverless/lambda). Unico entry
# del PYTHONPATH del subproceso (poner `.../shared` directo haria que
# `shared/http` shadowee el `http` de la stdlib).
_LAMBDA_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(shared.__file__)))
_MODELS_DIR = Path(shared.__file__).parent / 'db' / 'models'


def _model_modules() -> list[str]:
    """FQMN de cada modulo de modelo SQL (excluye `__init__`/`registry`)."""
    mods: list[str] = []
    for p in sorted(_MODELS_DIR.rglob('*.py')):
        if p.name in ('__init__.py', 'registry.py'):
            continue
        rel = p.relative_to(Path(_LAMBDA_ROOT)).with_suffix('')
        mods.append('.'.join(rel.parts))
    return mods


_CHECK = """
import importlib
import sys

importlib.import_module(sys.argv[1])

from shared.db.base import Base

errors = []
for table in Base.metadata.tables.values():
    for fk in table.foreign_keys:
        try:
            _ = fk.column  # fuerza la resolucion de la FK contra el MetaData
        except Exception as exc:  # noqa: BLE001 -- reportamos cualquier fallo
            errors.append(
                table.name + '.' + fk.parent.name
                + ' -> ' + str(fk._colspec) + ' (' + type(exc).__name__ + ')'
            )

if errors:
    print('FK_ERRORS: ' + '; '.join(errors))
    sys.exit(1)
print('OK')
"""


@pytest.mark.parametrize('module', _model_modules())
def test_model_module_load_resolves_all_foreign_keys(module: str) -> None:
    # Arrange: subproceso con SOLO el lambda root en PYTHONPATH.
    env = {**os.environ, 'PYTHONPATH': _LAMBDA_ROOT}

    # Act
    result = subprocess.run(  # noqa: S603
        [sys.executable, '-c', _CHECK, module],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'OK'
