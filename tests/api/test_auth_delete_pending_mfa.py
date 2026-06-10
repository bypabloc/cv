"""E2E: mfa.delete borra (hard-delete) un metodo MFA pendiente -> configured:false.

Continuacion del lockout del TOTP pendiente. `mfa.disable` solo hace
soft-disable: el row queda con `disabled_at` y el overview lo sigue mostrando
`configured:true, enabled:false` (un fantasma) y un `setup-totp` posterior
reusa el row viejo (created_at del 2026-06-03). El usuario pidio ELIMINAR de
verdad el TOTP pendiente para reconfigurar limpio.

`mfa.delete` borra el row: tras el delete el overview vuelve a
`configured:false` (No configurado) y el siguiente setup empieza de cero.

Verifica DETERMINISTICAMENTE (API pura):
- setup-totp crea el row PENDIENTE (confirmed=false).
- security.overview lo muestra configured:true antes.
- mfa.delete {kind:totp} -> 204 (un pendiente siempre se puede borrar).
- security.overview vuelve a configured:false (el row desaparecio, NO solo
  disabled como haria mfa.disable).
- delete de nuevo -> 404 NOT_FOUND (ya no existe).

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
    return {m['type']: m for m in (r.body.get('methods') or [])}


@pytest.mark.api
def test_delete_pending_totp_removes_it_from_overview(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user con un TOTP en setup (pendiente, confirmed=false),
    When lo borra con mfa.delete,
    Then -> 204, el TOTP vuelve a configured:false en el overview (hard-delete,
        no solo disabled) y un segundo delete da 404 NOT_FOUND.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+delpend-{secrets.token_hex(4)}@simulator.amazonses.com'
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

    # setup-totp: crea el row TOTP PENDIENTE (confirmed=false).
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

    # delete del TOTP pendiente -> 204 (un pendiente siempre se puede borrar).
    deleted = http.post(
        '/auth',
        body=make_body('mfa', 'delete', kind='totp'),
        origin=origin,
        bearer=access,
    )
    assert deleted.status == 204, (
        f'delete de un TOTP pendiente deberia ser 204, '
        f'fue {deleted.status}: {deleted.body}'
    )

    # el TOTP DESAPARECE: configured vuelve a false (no solo disabled).
    after = _overview(http, origin, access)
    assert after['totp']['configured'] is False, (
        f'el TOTP borrado deberia volver a configured:false (hard-delete), '
        f'no quedar como fantasma: {after["totp"]}'
    )
    assert after['totp']['enabled'] is False

    # segundo delete -> 404 NOT_FOUND (el row ya no existe).
    again = http.post(
        '/auth',
        body=make_body('mfa', 'delete', kind='totp'),
        origin=origin,
        bearer=access,
    )
    assert again.status == 404, (
        f'borrar un TOTP inexistente deberia ser 404, '
        f'fue {again.status}: {again.body}'
    )
    assert again.body.get('error') == 'NOT_FOUND', (
        f'el error deberia ser NOT_FOUND: {again.body}'
    )
