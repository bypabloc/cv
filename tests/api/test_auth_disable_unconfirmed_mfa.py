"""E2E: un metodo MFA no confirmado siempre se puede eliminar (anti-lockout).

Regresion del lockout reportado: un user tenia un TOTP `configured` pero
`confirmed:false` (setup-totp abandonado). No lo podia confirmar (no tenia el
authenticator), no lo podia marcar required (404 por no confirmado), y
`mfa.disable` daba 409 MUST_KEEP_ONE porque `count_active_mfa` solo cuenta
confirmados -> el TOTP pendiente no sumaba, la cuenta caia a <=1 y el guard
bloqueaba el disable. Resultado: atrapado con un metodo roto.

El fix: el guard MUST_KEEP_ONE solo protege metodos CONFIRMADOS. Un pendiente
no es una via de entrada real -> siempre se puede deshabilitar.

Verifica DETERMINISTICAMENTE (API pura):
- setup-totp crea el row PENDIENTE (confirmed=false), sin confirmar.
- mfa.disable {kind:totp} del pendiente -> 204 (ya no 409), aunque sea el
  unico metodo MFA "contado".
- tras el disable, el TOTP ya no aparece en security.overview como activo.

Requiere bypass (registra users active). Emails sinteticos limpiados en el
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


def _overview(http: HttpClient, origin: str, access: str) -> dict:
    """security.overview -> {type: entry} indexado por tipo de metodo."""
    r = http.post(
        '/auth',
        body=make_body('security', 'overview'),
        origin=origin,
        bearer=access,
    )
    methods = r.body.get('methods') or []
    return {m['type']: m for m in methods}


@pytest.mark.api
def test_disable_unconfirmed_totp_is_allowed(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user con un TOTP en setup (pendiente, confirmed=false),
    When lo deshabilita con mfa.disable,
    Then -> 204 (el guard MUST_KEEP_ONE no aplica a un pendiente) y el TOTP
        deja de figurar configurado en el overview. El user no queda atrapado.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+disunc-{secrets.token_hex(4)}@simulator.amazonses.com'
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

    # setup-totp: crea el row TOTP PENDIENTE (confirmed=false), sin confirmar.
    setup = http.post(
        '/auth',
        body=make_body('mfa', 'setup-totp'),
        origin=origin,
        bearer=access,
    )
    assert field(setup.body, 'secret_b32') is not None, (
        f'setup-totp no dio secret: {setup.body}'
    )
    before = _overview(http, origin, access)
    assert before['totp']['configured'] is True
    assert before['totp']['detail'] == {'confirmed': False}

    # disable del TOTP pendiente -> 204 (antes daba 409 MUST_KEEP_ONE).
    disabled = http.post(
        '/auth',
        body=make_body('mfa', 'disable', kind='totp'),
        origin=origin,
        bearer=access,
    )
    assert disabled.status == 204, (
        f'disable de un TOTP pendiente deberia ser 204, '
        f'fue {disabled.status}: {disabled.body}'
    )

    # el TOTP ya no figura activo/configurado en el overview.
    after = _overview(http, origin, access)
    assert after['totp']['enabled'] is False, (
        f'el TOTP deberia quedar deshabilitado: {after["totp"]}'
    )
