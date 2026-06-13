"""E2E: con 2+ passkeys 'required', basta UNA al loguear (webauthn = 1 factor).

El usuario reporto la duda: marcar varias passkeys como 'requerido al loguear'
NO debe obligar a usar TODAS. WebAuthn es UN solo factor del checklist: se
satisface con CUALQUIER passkey. `list_required_methods` agrega 'webauthn' una
sola vez si hay >=1 passkey required; `decide_mfa_step` lo compara como un solo
string.

Verifica DETERMINISTICAMENTE (API pura):
- registra DOS passkeys (A y B) y marca AMBAS required.
- login.start (precheck) lista 'webauthn' UNA sola vez en `methods` (no dos).
- verify-password deja webauthn pendiente; un login-verify con UNA passkey (A)
  CIERRA el login (access + refresh). No se exige la segunda.

El user tiene password + las 2 passkeys; las passkeys se firman con SoftPasskey
(authenticator de software). Requiere bypass. Emails sinteticos limpiados en el
teardown del conftest.
"""

from __future__ import annotations

import secrets

import pytest
from shared.auth_support import STRONG_PASSWORD
from shared.auth_support import create_active_user_with_password
from shared.auth_support import field
from shared.auth_support import login_precheck
from shared.config import admin_origin
from shared.environment import Environment
from shared.http import HttpClient
from shared.runner import make_body
from shared.webauthn_device import SoftPasskey


def _access_via_password(
    http: HttpClient,
    origin: str,
    email: str,
    bypass: str,
) -> str:
    """Login solo-password -> access token (la password es el unico required)."""
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth',
        body=make_body('login', 'start'),
        origin=origin,
        bearer=precheck,
    )
    vp = http.post(
        '/auth',
        body=make_body(
            'login',
            'verify-password',
            password=STRONG_PASSWORD,
            temp_token=field(start.body, 'temp_token'),
        ),
        origin=origin,
    )
    access = field(vp.body, 'access_token')
    assert access, f'login solo-password no dio access: {vp.body}'
    return access


def _register_passkey(
    http: HttpClient,
    origin: str,
    access: str,
    pk: SoftPasskey,
    nickname: str,
) -> str:
    """Registra un passkey (register-options -> verify) y devuelve su record id."""
    ro = http.post(
        '/auth',
        body=make_body('webauthn', 'register-options'),
        origin=origin,
        bearer=access,
    )
    assert ro.status == 200, f'register-options fallo: {ro.status} {ro.body}'
    rv = http.post(
        '/auth',
        body=make_body(
            'webauthn',
            'register-verify',
            challenge_id=ro.body['challenge_id'],
            response=pk.register_response(ro.body['options']),
            nickname=nickname,
        ),
        origin=origin,
        bearer=access,
    )
    assert rv.status == 201, f'register-verify fallo: {rv.status} {rv.body}'
    cs = http.post(
        '/auth',
        body=make_body('webauthn', 'list-credentials'),
        origin=origin,
        bearer=access,
    )
    by_nick = {
        c['nickname']: c['credential_id'] for c in cs.body['credentials']
    }
    record_id = by_nick.get(nickname)
    assert record_id is not None, (
        f'no se encontro el passkey {nickname}: {cs.body}'
    )
    return record_id


@pytest.mark.api
def test_two_required_passkeys_one_satisfies_webauthn_factor(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user con password + DOS passkeys, ambas marcadas required,
    When inicia sesion (start -> verify-password -> UNA passkey login-verify),
    Then login.start lista 'webauthn' UNA sola vez y una sola passkey cierra el
        login con access + refresh (no se exigen las dos).
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+wa2req-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http,
        environment,
        origin,
        email,
        bypass,
    )
    assert user_id is not None
    access = _access_via_password(http, origin, email, bypass)

    # Registra DOS passkeys (A y B) y marca AMBAS required.
    pk_a = SoftPasskey(origin)
    pk_b = SoftPasskey(origin)
    rec_a = _register_passkey(http, origin, access, pk_a, 'key-a')
    rec_b = _register_passkey(http, origin, access, pk_b, 'key-b')
    assert environment.count_webauthn_credentials(user_id) == 2
    for rec in (rec_a, rec_b):
        req = http.post(
            '/auth',
            body=make_body(
                'webauthn',
                'set-required',
                credential_id=rec,
                required=True,
            ),
            origin=origin,
            bearer=access,
        )
        assert req.status == 204, (
            f'set-required {rec} fallo: {req.status} {req.body}'
        )

    # login.start: 'webauthn' aparece UNA sola vez (no una por passkey).
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth',
        body=make_body('login', 'start'),
        origin=origin,
        bearer=precheck,
    )
    methods = start.body.get('methods') or []
    assert methods.count('webauthn') == 1, (
        f"'webauthn' deberia listarse UNA sola vez con 2 passkeys required: "
        f'{methods}'
    )
    assert 'password' in methods
    temp = field(start.body, 'temp_token')

    # verify-password (intermedio): webauthn sigue pendiente.
    vp = http.post(
        '/auth',
        body=make_body(
            'login',
            'verify-password',
            password=STRONG_PASSWORD,
            temp_token=temp,
        ),
        origin=origin,
    )
    assert vp.body.get('mfa_complete') is False
    assert 'webauthn' in (vp.body.get('methods') or [])
    temp2 = field(vp.body, 'temp_token')

    # UNA sola passkey (A) cierra el login: NO se exige la segunda (B).
    lo = http.post(
        '/auth',
        body=make_body('webauthn', 'login-options', email=email),
        origin=origin,
    )
    assert lo.status == 200, f'login-options fallo: {lo.status} {lo.body}'
    lv = http.post(
        '/auth',
        body=make_body(
            'webauthn',
            'login-verify',
            challenge_id=lo.body['challenge_id'],
            response=pk_a.login_response(lo.body['options']),
            temp_token=temp2,
        ),
        origin=origin,
    )
    assert lv.body.get('mfa_complete') is True, (
        f'UNA passkey deberia cerrar el login (basta una de las 2 required): '
        f'{lv.body}'
    )
    assert field(lv.body, 'access_token'), (
        f'falta access_token final: {lv.body}'
    )
    assert field(lv.body, 'refresh_token'), (
        f'falta refresh_token final: {lv.body}'
    )
