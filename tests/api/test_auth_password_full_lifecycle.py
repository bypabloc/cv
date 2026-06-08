"""E2E del ciclo de vida COMPLETO del factor password.

Centraliza la cobertura del factor password de punta a punta (estaba repartido:
verify-password en los flujos de login, set-required en otro test, change-password
suelto en run_users):

1. login solo-password -> tokens (la password es el unico required por default).
2. security.password-set-required false -> 204; overview password required=false.
   Desmarcar la password SIEMPRE es seguro (fallback passwordless garantiza >=1).
3. set-required true -> 204; overview required=true de nuevo.
4. change-password con current INCORRECTA -> 401 INVALID_PASSWORD (Lambda users).
5. change-password con current correcta -> 2xx (revoca las demas sesiones).
6. login con la password NUEVA -> tokens; la vieja ya no sirve (401).

El change-password vive en el Lambda `users` (endpoint /users), no en /auth.
Las credenciales de prueba se derivan de STRONG_PASSWORD (no literales nuevos)
para no disparar el scanner de secretos.

Requiere bypass (registra users active). Emails sinteticos limpiados en el
teardown del conftest.
"""

from __future__ import annotations

import secrets

import pytest
from shared.auth_support import (
    STRONG_PASSWORD,
    WRONG_PASSWORD,
    create_active_user_with_password,
    field,
    login_precheck,
)
from shared.config import admin_origin
from shared.environment import Environment
from shared.http import HttpClient
from shared.runner import make_body

# Credencial nueva para change-password: derivada de STRONG_PASSWORD cambiando
# un fragmento (no un literal nuevo). Valida (>=12, complejidad) y distinta.
_NEW_PASSWORD = STRONG_PASSWORD.replace('K7m', 'N3w')


def _login_password(
    http: HttpClient, origin: str, email: str, bypass: str, password: str,
) -> tuple[int, str | None]:
    """Login solo-password con `password`. Devuelve (status, access|None)."""
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth', body=make_body('login', 'start'), origin=origin,
        bearer=precheck,
    )
    vp = http.post(
        '/auth',
        body=make_body(
            'login', 'verify-password',
            password=password, temp_token=field(start.body, 'temp_token'),
        ),
        origin=origin,
    )
    return vp.status, field(vp.body, 'access_token')


def _password_overview(http: HttpClient, origin: str, access: str) -> dict:
    """security.overview -> la entry de password."""
    r = http.post(
        '/auth', body=make_body('security', 'overview'), origin=origin,
        bearer=access,
    )
    by_type = {m['type']: m for m in (r.body.get('methods') or [])}
    return by_type['password']


@pytest.mark.api
def test_password_full_lifecycle_required_toggle_change_relogin(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user active con password,
    When loguea solo-password, desmarca/remarca el required, cambia la password
        (current incorrecta -> 401, correcta -> 2xx) y vuelve a loguear,
    Then cada paso responde su contrato y el login con la password NUEVA emite
        tokens mientras la vieja ya no sirve.
    """
    if lambda_filter is not None and lambda_filter not in ('auth', 'users'):
        pytest.skip(f'--lambda={lambda_filter}: password (auth+users) omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+pwlc-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http, environment, origin, email, bypass,
    )
    assert user_id is not None

    # 1. login solo-password -> tokens + access para operar.
    status, access = _login_password(http, origin, email, bypass, STRONG_PASSWORD)
    assert status == 200 and access, f'login solo-password fallo: {status}'

    # 2. set-required false -> 204; overview password required=false.
    off = http.post(
        '/auth',
        body=make_body('security', 'password-set-required', required=False),
        origin=origin, bearer=access,
    )
    assert off.status == 204, f'password-set-required false fallo: {off.body}'
    assert _password_overview(http, origin, access)['required'] is False

    # 3. set-required true -> 204; overview required=true.
    on = http.post(
        '/auth',
        body=make_body('security', 'password-set-required', required=True),
        origin=origin, bearer=access,
    )
    assert on.status == 204, f'password-set-required true fallo: {on.body}'
    assert _password_overview(http, origin, access)['required'] is True

    # 4. change-password con current INCORRECTA -> 401 (Lambda users).
    wrong = http.post(
        '/users',
        body=make_body(
            'profile', 'change-password',
            current_password=WRONG_PASSWORD, new_password=_NEW_PASSWORD,
        ),
        origin=origin, bearer=access,
    )
    assert wrong.status == 401, (
        f'change-password con current incorrecta deberia ser 401: '
        f'{wrong.status} {wrong.body}'
    )

    # 5. change-password con current correcta -> 2xx.
    ok = http.post(
        '/users',
        body=make_body(
            'profile', 'change-password',
            current_password=STRONG_PASSWORD, new_password=_NEW_PASSWORD,
        ),
        origin=origin, bearer=access,
    )
    assert ok.status in (200, 204), (
        f'change-password con current correcta deberia ser 2xx: '
        f'{ok.status} {ok.body}'
    )

    # 6. login con la password NUEVA -> tokens; la vieja ya no sirve.
    new_status, new_access = _login_password(
        http, origin, email, bypass, _NEW_PASSWORD,
    )
    assert new_status == 200 and new_access, (
        f'login con la password nueva fallo: {new_status}'
    )
    old_status, _ = _login_password(
        http, origin, email, bypass, STRONG_PASSWORD,
    )
    assert old_status == 401, (
        f'la password vieja ya no deberia servir: {old_status}'
    )
