"""E2E del ciclo de vida COMPLETO del metodo WebAuthn (passkeys).

Centraliza la cobertura del factor passkey de punta a punta (antes el register
y el login estaban repartidos entre test_webauthn_register.py (browser) y
test_auth_multifactor_checklist.py; faltaban set-required, list, disable,
enable y delete a nivel API):

1. register-options -> register-verify (firmado con SoftPasskey) -> 201.
2. list-credentials -> el passkey aparece con su record id.
3. set-required del passkey -> 204; overview refleja webauthn required.
4. login completo por el checklist: login.start lista [password, webauthn] ->
   verify-password (intermedio) -> webauthn login-options/login-verify (cierra)
   -> access + refresh.
5. disable el passkey -> 204 (queda el TOTP) -> enable -> 204.
6. delete-credential -> 204; overview ya no lista el passkey como activo.

El passkey se firma con `SoftPasskey` (authenticator de software, UV) — sin
browser ni Virtual Authenticator CDP (flaky). Para que disable/delete del
passkey NO choque con MUST_KEEP_ONE_MFA_METHOD, el user tiene ademas un TOTP
confirmado.

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
from shared.webauthn_device import SoftPasskey


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


def _enroll_totp(http: HttpClient, origin: str, access: str) -> None:
    """Enrola + confirma un TOTP (segundo MFA para no chocar MUST_KEEP_ONE)."""
    setup = http.post(
        '/auth', body=make_body('mfa', 'setup-totp'), origin=origin,
        bearer=access,
    )
    secret = field(setup.body, 'secret_b32')
    assert secret is not None
    confirm = http.post(
        '/auth',
        body=make_body('mfa', 'confirm-totp', code=totp_now(secret)),
        origin=origin, bearer=access,
    )
    assert confirm.status == 204, f'confirm-totp fallo: {confirm.body}'


def _overview_by_type(http: HttpClient, origin: str, access: str) -> dict:
    """security.overview -> {type: entry} indexado por tipo de metodo."""
    r = http.post(
        '/auth', body=make_body('security', 'overview'), origin=origin,
        bearer=access,
    )
    return {m['type']: m for m in (r.body.get('methods') or [])}


@pytest.mark.api
def test_webauthn_full_lifecycle_register_required_login_disable_delete(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user active con password + TOTP confirmado,
    When registra un passkey, lo marca required, inicia sesion completando
        password + passkey, lo deshabilita/reactiva y finalmente lo borra,
    Then cada paso responde su contrato y el login converge con access+refresh.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+walc-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http, environment, origin, email, bypass,
    )
    assert user_id is not None
    access = _access_via_password(http, origin, email, bypass)
    _enroll_totp(http, origin, access)

    # 1. register-options -> register-verify (firmado) -> 201.
    pk = SoftPasskey(origin)
    ro = http.post(
        '/auth', body=make_body('webauthn', 'register-options'),
        origin=origin, bearer=access,
    )
    assert ro.status == 200, f'register-options fallo: {ro.status} {ro.body}'
    rv = http.post(
        '/auth',
        body=make_body(
            'webauthn', 'register-verify',
            challenge_id=ro.body['challenge_id'],
            response=pk.register_response(ro.body['options']),
            nickname='lifecycle',
        ),
        origin=origin, bearer=access,
    )
    assert rv.status == 201, f'register-verify fallo: {rv.status} {rv.body}'
    assert environment.count_webauthn_credentials(user_id) == 1, (
        'el passkey deberia estar persistido en Neon'
    )

    # 2. list-credentials -> el record id del passkey.
    cs = http.post(
        '/auth', body=make_body('webauthn', 'list-credentials'),
        origin=origin, bearer=access,
    )
    assert cs.status == 200, f'list-credentials fallo: {cs.body}'
    record_id = cs.body['credentials'][0]['credential_id']

    # 3. set-required del passkey -> 204; overview webauthn required.
    req = http.post(
        '/auth',
        body=make_body(
            'webauthn', 'set-required', credential_id=record_id, required=True,
        ),
        origin=origin, bearer=access,
    )
    assert req.status == 204, f'webauthn set-required fallo: {req.status} {req.body}'
    overview = _overview_by_type(http, origin, access)
    assert overview['webauthn']['configured'] is True
    assert overview['webauthn']['required'] is True

    # 4. login completo: password (intermedio) -> passkey (cierra).
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth', body=make_body('login', 'start'), origin=origin,
        bearer=precheck,
    )
    methods = set(start.body.get('methods') or [])
    assert 'webauthn' in methods and 'password' in methods, (
        f'login.start deberia exigir password+webauthn: {start.body}'
    )
    temp = field(start.body, 'temp_token')

    vp = http.post(
        '/auth',
        body=make_body(
            'login', 'verify-password', password=STRONG_PASSWORD, temp_token=temp,
        ),
        origin=origin,
    )
    assert vp.body.get('mfa_complete') is False, (
        f'tras password aun falta webauthn: {vp.body}'
    )
    temp2 = field(vp.body, 'temp_token')
    assert temp2, f'falta temp rolling tras password: {vp.body}'

    lo = http.post(
        '/auth', body=make_body('webauthn', 'login-options', email=email),
        origin=origin,
    )
    assert lo.status == 200, f'login-options fallo: {lo.status} {lo.body}'
    lv = http.post(
        '/auth',
        body=make_body(
            'webauthn', 'login-verify',
            challenge_id=lo.body['challenge_id'],
            response=pk.login_response(lo.body['options']),
            temp_token=temp2,
        ),
        origin=origin,
    )
    assert lv.body.get('mfa_complete') is True, (
        f'el passkey deberia cerrar el login: {lv.body}'
    )
    assert field(lv.body, 'access_token'), f'falta access_token final: {lv.body}'
    assert field(lv.body, 'refresh_token'), f'falta refresh_token final: {lv.body}'

    # 5. disable -> 204 (queda el TOTP) -> enable -> 204.
    dis = http.post(
        '/auth', body=make_body('webauthn', 'disable', credential_id=record_id),
        origin=origin, bearer=access,
    )
    assert dis.status == 204, f'webauthn disable fallo: {dis.status} {dis.body}'
    assert environment.count_webauthn_credentials(user_id) == 0, (
        'el passkey deshabilitado no deberia contar como activo'
    )
    ena = http.post(
        '/auth', body=make_body('webauthn', 'enable', credential_id=record_id),
        origin=origin, bearer=access,
    )
    assert ena.status == 204, f'webauthn enable fallo: {ena.status} {ena.body}'
    assert environment.count_webauthn_credentials(user_id) == 1, (
        'el passkey reactivado deberia volver a contar'
    )

    # 6. delete-credential -> 204; ya no figura activo.
    deleted = http.post(
        '/auth',
        body=make_body('webauthn', 'delete-credential', credential_id=record_id),
        origin=origin, bearer=access,
    )
    assert deleted.status == 204, (
        f'delete-credential fallo: {deleted.status} {deleted.body}'
    )
    assert environment.count_webauthn_credentials(user_id) == 0, (
        'el passkey borrado no deberia quedar en Neon'
    )
