"""
Given el subpaquete shared.auth con carga lazy (PEP 562),
When se importa shared.auth y se accede a un simbolo de jwt,
Then NO se carga fido2/webauthn; recien al acceder un simbolo de webauthn
     se importa fido2.

Guard de regresion del cold start: el __init__ eager hacia
`from shared.auth.webauthn import ...` y arrastraba fido2/cryptography (el
import mas pesado) en TODA accion que importara shared.auth, aunque no
usara WebAuthn (login.start, session.refresh, ...). El lazy hace que cada
accion solo pague los submodulos que toca. Ver .claude/rules/lambda-config.md.
"""

import importlib
import sys

import pytest

pytestmark = pytest.mark.unit


def _purge_auth_and_fido2() -> None:
    for mod in list(sys.modules):
        if (
            mod == 'shared.auth'
            or mod.startswith('shared.auth.')
            or mod == 'fido2'
            or mod.startswith('fido2.')
        ):
            del sys.modules[mod]


def test_shared_auth_does_not_eager_load_fido2():
    # Arrange: estado limpio para medir que se carga y que no.
    _purge_auth_and_fido2()

    # Act 1: importar shared.auth NO debe cargar ningun submodulo aun.
    auth = importlib.import_module('shared.auth')

    # Assert 1: el __init__ es lazy -> ni webauthn ni fido2 cargados.
    assert 'shared.auth.webauthn' not in sys.modules
    assert 'fido2' not in sys.modules

    # Act 2: acceder a un simbolo jwt dispara solo la carga de jwt.
    _jwt = auth.verify_jwt
    assert callable(_jwt) is True

    # Assert 2: jwt cargado, fido2/webauthn NO (jwt no los arrastra).
    assert 'shared.auth.jwt' in sys.modules
    assert 'fido2' not in sys.modules
    assert 'shared.auth.webauthn' not in sys.modules

    # Act 3: acceder a un simbolo webauthn SI carga fido2.
    _wa = auth.verify_authentication
    assert callable(_wa) is True

    # Assert 3: ahora si estan cargados.
    assert 'shared.auth.webauthn' in sys.modules
    assert 'fido2' in sys.modules
