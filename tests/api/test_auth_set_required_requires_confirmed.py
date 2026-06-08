"""E2E del invariante: un metodo MFA no confirmado NO puede ser `required`.

Regresion del bug reportado: un user tenia un TOTP con `required=true` en la
columna pero `confirmed=false` (nunca se valido el code del authenticator).
`login.start` lo IGNORABA (list_required_methods exige confirmado), asi que
settings mostraba "required: true" pero el login no lo pedia -> contradiccion.

El fix cierra el invariante en el origen: `mfa.set-required` rechaza (404) un
TOTP no confirmado. Asi nunca se llega al estado inconsistente y `login.start`
solo lista factores realmente exigibles.

Verifica DETERMINISTICAMENTE (API pura):
- setup-totp crea el row PENDIENTE (confirmed=false), sin confirmar.
- mfa.set-required {kind:totp, required:true} -> 404 NOT_FOUND.
- login.start NO lista `totp` en `methods` (solo `password`).
- tras confirm-totp + set-required, login.start SI lista `totp`.

Requiere bypass (registra users active). Emails sinteticos limpiados en el
teardown del conftest.
"""

from __future__ import annotations

import secrets

import pytest
from shared.auth_support import (
    STRONG_PASSWORD,
    create_active_user_with_password,
    field,
    login_precheck,
)
from shared.config import admin_origin
from shared.environment import Environment
from shared.http import HttpClient
from shared.runner import make_body
from shared.totp import totp_now


def _access_via_password(
    http: HttpClient, origin: str, email: str, bypass: str,
) -> str:
    """Login solo-password -> access token (la password es el unico required)."""
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth', body=make_body('login', 'start'), origin=origin,
        bearer=precheck,
    )
    vp = http.post(
        '/auth',
        body=make_body(
            'login', 'verify-password',
            password=STRONG_PASSWORD, temp_token=field(start.body, 'temp_token'),
        ),
        origin=origin,
    )
    access = field(vp.body, 'access_token')
    assert access, f'login solo-password no dio access: {vp.body}'
    return access


def _login_methods(
    http: HttpClient, origin: str, email: str, bypass: str,
) -> list[str]:
    """`login.start` -> la lista de factores `methods` que el login exige."""
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth', body=make_body('login', 'start'), origin=origin,
        bearer=precheck,
    )
    return list(start.body.get('methods') or [])


@pytest.mark.api
def test_set_required_unconfirmed_totp_is_rejected_and_not_in_login(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user con un TOTP en setup (pendiente, confirmed=false),
    When intenta marcarlo `required` antes de confirmarlo,
    Then mfa.set-required -> 404 NOT_FOUND y login.start NO lista totp; tras
        confirmar y marcarlo required, login.start SI lo lista.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+reqconf-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http, environment, origin, email, bypass,
    )
    assert user_id is not None
    access = _access_via_password(http, origin, email, bypass)

    # setup-totp: crea el row TOTP PENDIENTE (confirmed=false), sin confirmar.
    setup = http.post(
        '/auth', body=make_body('mfa', 'setup-totp'), origin=origin,
        bearer=access,
    )
    secret = field(setup.body, 'secret_b32')
    assert secret is not None, f'setup-totp no dio secret: {setup.body}'

    # set-required sobre el TOTP NO confirmado -> 404 NOT_FOUND (el invariante).
    req_unconfirmed = http.post(
        '/auth',
        body=make_body('mfa', 'set-required', kind='totp', required=True),
        origin=origin, bearer=access,
    )
    assert req_unconfirmed.status == 404, (
        f'set-required de un TOTP no confirmado deberia ser 404, '
        f'fue {req_unconfirmed.status}: {req_unconfirmed.body}'
    )

    # login.start NO lista el TOTP pendiente (solo password).
    methods_before = _login_methods(http, origin, email, bypass)
    assert methods_before == ['password'], (
        f'un TOTP pendiente no deberia exigirse en el login: {methods_before}'
    )

    # confirm-totp + set-required -> ahora SI es required y login.start lo lista.
    confirm = http.post(
        '/auth',
        body=make_body('mfa', 'confirm-totp', code=totp_now(secret)),
        origin=origin, bearer=access,
    )
    assert confirm.status == 204, f'confirm-totp fallo: {confirm.body}'
    req_confirmed = http.post(
        '/auth',
        body=make_body('mfa', 'set-required', kind='totp', required=True),
        origin=origin, bearer=access,
    )
    assert req_confirmed.status == 204, (
        f'set-required de un TOTP confirmado deberia ser 204, '
        f'fue {req_confirmed.status}: {req_confirmed.body}'
    )
    methods_after = _login_methods(http, origin, email, bypass)
    assert set(methods_after) == {'password', 'totp'}, (
        f'tras confirmar+required, el login deberia exigir totp: {methods_after}'
    )
