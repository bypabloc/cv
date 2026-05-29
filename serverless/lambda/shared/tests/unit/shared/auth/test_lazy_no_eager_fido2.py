"""
Given el subpaquete shared.auth con imports CONCRETOS por modulo,
When se importa `shared.auth.jwt`,
Then NO se carga fido2/webauthn; recien al importar `shared.auth.webauthn`
     se carga fido2.

Guard de regresion del cold start: importar un simbolo de jwt
(`login.start`, `session.refresh`) NO debe arrastrar fido2/cryptography (el
import mas pesado). Con imports concretos por modulo esto es natural; el
test protege contra que alguien agregue `import fido2` a `jwt.py` o a una
dep transitiva suya. Ver `.claude/rules/lambda-config.md`.

Se ejecuta en un SUBPROCESO para no contaminar el `sys.modules` de la suite
(un purgado in-process de fido2 rompe `get_type_hints` de las dataclasses
de fido2 en tests posteriores).
"""

import os
import subprocess
import sys

import pytest
import shared

pytestmark = pytest.mark.unit

# Dir que contiene el paquete `shared` (.../serverless/lambda). Es el UNICO
# entry que el subproceso necesita en PYTHONPATH: poner `.../shared` directo
# haria que `shared/http` shadowee el `http` de la stdlib.
_LAMBDA_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(shared.__file__)))

_CHECK = """
import sys

import shared.auth.jwt as _jwt
assert callable(_jwt.verify_jwt)
# jwt cargado; fido2/webauthn NO (jwt no los arrastra).
assert 'shared.auth.jwt' in sys.modules
assert 'fido2' not in sys.modules, 'jwt arrastra fido2 (regresion cold start)'
assert 'shared.auth.webauthn' not in sys.modules

import shared.auth.webauthn as _wa
assert callable(_wa.verify_authentication)
# ahora si: webauthn carga fido2.
assert 'shared.auth.webauthn' in sys.modules
assert 'fido2' in sys.modules
print('OK')
"""


def test_jwt_import_does_not_eager_load_fido2() -> None:
    # Arrange: subproceso con SOLO el lambda root en PYTHONPATH (shared
    # importable como paquete; sin que shared/http shadowee la stdlib).
    env = {**os.environ, 'PYTHONPATH': _LAMBDA_ROOT}

    # Act
    result = subprocess.run(  # noqa: S603
        [sys.executable, '-c', _CHECK],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    # Assert
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'OK'
