"""E2E: el alta crea el email_code confirmado (sin pasar por setup-email-code).

El email se verifica al registrarse (code/magic-link), asi que el metodo MFA
`email_code` debe nacer configurado en el alta. Verifica DETERMINISTICAMENTE
(API pura) que tras dar de alta un user por el flujo real
(`login.start` -> `login.verify-code`) el `security.overview` ya reporta
email_code `configured:true, enabled:true, required:false`, SIN haber invocado
`mfa.setup-email-code`.

Cubre AC-1 (alta via verify-code crea el row) y AC-6 (overview lo refleja).

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


@pytest.mark.api
def test_register_creates_email_code_configured(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given el alta de un user por el flujo real (login.start -> verify-code),
    When se consulta security.overview SIN llamar setup-email-code,
    Then la entrada email_code ya es configured:true, enabled:true,
        required:false (el email se verifico en el alta).
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+regemc-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)

    # Alta por el flujo real (verify-code activa el pending -> crea email_code).
    user_id = create_active_user_with_password(
        http,
        environment,
        origin,
        email,
        bypass,
    )
    assert user_id is not None

    # overview SIN setup-email-code: email_code ya configurado por el alta.
    access = _access_via_password(http, origin, email, bypass)
    r = http.post(
        '/auth',
        body=make_body('security', 'overview'),
        origin=origin,
        bearer=access,
    )
    by_type = {m['type']: m for m in (r.body.get('methods') or [])}
    email_code = by_type.get('email_code')
    assert email_code is not None, f'falta email_code en overview: {r.body}'
    assert email_code['configured'] is True, (
        f'email_code deberia nacer configurado en el alta: {email_code}'
    )
    assert email_code['enabled'] is True, (
        f'email_code deberia estar enabled: {email_code}'
    )
    assert email_code['required'] is False, (
        f'email_code no deberia ser required por defecto: {email_code}'
    )
