"""
Given un dominio de `shared.db.models` importado en AISLAMIENTO (como hace
     el handler de un lambda: `import shared.db.models.<dominio>`),
When se resuelven todas las ForeignKey de las tablas registradas,
Then ninguna lanza `NoReferencedTableError`: el dominio carga sus propios
     FK-targets cross-domain (auth->cv_profiles, cv/visitor->taxonomy).

Guard de regresion del bug de PR #199 (carga per-dominio): `auth_users.
profile_id -> cv_profiles.id` es una FK cross-domain. Cargar solo
`shared.db.models.auth` dejaba `cv_profiles` fuera del MetaData -> la FK no
resolvia en el INSERT de `auth_users` -> `NoReferencedTableError` ->
HTTP 500 en register/login/users (y data-loss async en el tracking_worker
por `vis_tracking_events.event_type_id -> tax_event_types.id`).

El fix encapsula los FK-targets en el `__init__` de cada dominio. Este test
protege contra que alguien (a) agregue una FK cross-domain nueva sin cargar
su dominio target, o (b) quite el load encapsulado. Ver
`.claude/rules/lambda-config.md`.

Se ejecuta en un SUBPROCESO por dominio: el MetaData de SQLAlchemy es global
por proceso, asi que cargar un dominio in-process contaminaria a los demas
(todos compartirian el mismo `Base.metadata`) y ocultaria el aislamiento
real que tiene un lambda en su cold start.
"""

import os
import subprocess
import sys

import pytest
import shared

pytestmark = pytest.mark.unit

# Dir que contiene el paquete `shared` (.../serverless/lambda). Unico entry
# del PYTHONPATH del subproceso: poner `.../shared` directo haria que
# `shared/http` shadowee el `http` de la stdlib.
_LAMBDA_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(shared.__file__)))

# Los 5 dominios del schema unificado. Cada uno se importa en aislamiento.
_DOMAINS = ['auth', 'cv', 'visitor', 'taxonomy', 'i18n']

_CHECK = """
import importlib
import sys

domain = sys.argv[1]
importlib.import_module('shared.db.models.' + domain)

from shared.db.base import Base

errors = []
for table in Base.metadata.tables.values():
    for fk in table.foreign_keys:
        try:
            _ = fk.column  # fuerza la resolucion de la FK contra el MetaData
        except Exception as exc:  # noqa: BLE001 -- reportamos cualquier fallo
            errors.append(
                table.name + '.' + fk.parent.name
                + ' -> ' + str(fk._colspec)
                + ' (' + type(exc).__name__ + ')'
            )

if errors:
    print('FK_ERRORS: ' + '; '.join(errors))
    sys.exit(1)
print('OK')
"""


@pytest.mark.parametrize('domain', _DOMAINS)
def test_domain_load_resolves_all_foreign_keys(domain: str) -> None:
    # Arrange: subproceso con SOLO el lambda root en PYTHONPATH para que
    # `import shared.db.models.<domain>` cargue ese dominio aislado.
    env = {**os.environ, 'PYTHONPATH': _LAMBDA_ROOT}

    # Act
    result = subprocess.run(  # noqa: S603
        [sys.executable, '-c', _CHECK, domain],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'OK'
