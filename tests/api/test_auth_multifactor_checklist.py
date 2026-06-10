"""E2E del login multi-factor (checklist) del Lambda auth — combinaciones.

Verifica DETERMINISTICAMENTE (API pura, sin browser) el contrato del checklist
de login cuando el user tiene >1 factor `required`:

- Cada verify intermedio devuelve `mfa_complete: false` + `methods` con los
  factores que faltan (key explicita de progreso).
- El verify que satisface el ULTIMO factor devuelve `mfa_complete: true` +
  `access_token` + `refresh_token` (el token final que se usara).
- Los factores se completan EN CUALQUIER ORDEN; el backend acumula via el
  `temp_token` rolling (cada verify emite uno nuevo con el factor sumado).

Cubre el bug del passkey en el checklist (webauthn.login-verify ahora acumula
los factores previos del temp en vez de hardcodear ['webauthn']).

Combinaciones probadas:
- password + totp
- password + webauthn          (el caso reportado)
- password + totp + webauthn   (3 factores, orden arbitrario)

Requiere bypass (registra users active): sin el, se omite. El passkey se firma
con `SoftPasskey` (authenticator de software, UV) — sin browser ni Virtual
Authenticator CDP. Emails sinteticos limpiados en el teardown del conftest.
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
from shared.totp import totp_now
from shared.webauthn_device import SoftPasskey


def _enroll_totp(http: HttpClient, origin: str, access: str) -> str:
    """Enrola + confirma TOTP y lo marca required. Devuelve el secret_b32."""
    setup = http.post(
        '/auth',
        body=make_body('mfa', 'setup-totp'),
        origin=origin,
        bearer=access,
    )
    secret = field(setup.body, 'secret_b32')
    assert secret is not None
    http.post(
        '/auth',
        body=make_body('mfa', 'confirm-totp', code=totp_now(secret)),
        origin=origin,
        bearer=access,
    )
    http.post(
        '/auth',
        body=make_body('mfa', 'set-required', kind='totp', required=True),
        origin=origin,
        bearer=access,
    )
    return secret


def _enroll_passkey(
    http: HttpClient,
    origin: str,
    admin: str,
    access: str,
) -> SoftPasskey:
    """Registra un passkey (SoftPasskey) y lo marca required. Devuelve el device."""
    pk = SoftPasskey(admin)
    ro = http.post(
        '/auth',
        body=make_body('webauthn', 'register-options'),
        origin=origin,
        bearer=access,
    )
    rv = http.post(
        '/auth',
        body=make_body(
            'webauthn',
            'register-verify',
            challenge_id=ro.body['challenge_id'],
            response=pk.register_response(ro.body['options']),
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
    cred_id = cs.body['credentials'][0]['credential_id']
    http.post(
        '/auth',
        body=make_body(
            'webauthn',
            'set-required',
            credential_id=cred_id,
            required=True,
        ),
        origin=origin,
        bearer=access,
    )
    return pk


def _verify_factor(
    http: HttpClient,
    origin: str,
    factor: str,
    *,
    temp: str,
    email: str,
    secret: str | None,
    passkey: SoftPasskey | None,
    env_obj: Environment,
    user_id: str,
) -> dict:
    """Completa UN factor del checklist con el `temp` actual. Devuelve el body.

    `password`/`totp` van directo con el temp. `webauthn` hace
    login-options -> firma -> login-verify CON el temp. `email_code` envia el
    code, lo seedea en Neon y lo verifica.
    """
    if factor == 'password':
        r = http.post(
            '/auth',
            body=make_body(
                'login',
                'verify-password',
                password=STRONG_PASSWORD,
                temp_token=temp,
            ),
            origin=origin,
        )
        return r.body
    if factor == 'totp':
        assert secret is not None
        r = http.post(
            '/auth',
            body=make_body(
                'login',
                'verify-totp',
                code=totp_now(secret),
                temp_token=temp,
            ),
            origin=origin,
        )
        return r.body
    if factor == 'webauthn':
        assert passkey is not None
        lo = http.post(
            '/auth',
            body=make_body('webauthn', 'login-options', email=email),
            origin=origin,
        )
        r = http.post(
            '/auth',
            body=make_body(
                'webauthn',
                'login-verify',
                challenge_id=lo.body['challenge_id'],
                response=passkey.login_response(lo.body['options']),
                temp_token=temp,
            ),
            origin=origin,
        )
        return r.body
    raise AssertionError(f'factor no soportado en el helper: {factor}')


def _run_checklist(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str,
    *,
    factors_order: list[str],
    enroll: dict,
) -> dict:
    """Crea el user, completa los factores en `factors_order` y verifica contrato.

    `enroll` trae los artefactos del setup (`secret`, `passkey`, `email`,
    `user_id`). Asercion del contrato en cada paso: los intermedios devuelven
    `mfa_complete: false` + `methods` no vacio; el ultimo `mfa_complete: true` +
    tokens. Devuelve el body final (con los tokens).
    """
    origin = admin_origin(env)
    email = enroll['email']
    user_id = enroll['user_id']
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth',
        body=make_body('login', 'start'),
        origin=origin,
        bearer=precheck,
    )
    # check del set de required: el backend lista TODOS los factores.
    assert set(start.body.get('methods') or []) == set(factors_order)
    assert start.body.get('mfa_complete') is False
    temp = field(start.body, 'temp_token')

    last = len(factors_order) - 1
    final_body: dict = {}
    for i, factor in enumerate(factors_order):
        body = _verify_factor(
            http,
            origin,
            factor,
            temp=temp,
            email=email,
            secret=enroll.get('secret'),
            passkey=enroll.get('passkey'),
            env_obj=environment,
            user_id=user_id,
        )
        if i < last:
            # Contrato intermedio: NO completo, faltan factores, temp rolling.
            assert body.get('mfa_complete') is False, (
                f'factor {factor}: esperaba mfa_complete=false, body={body}'
            )
            pending = body.get('methods') or []
            assert factor not in pending, (
                f'{factor} no deberia seguir pendiente: {pending}'
            )
            assert pending, f'tras {factor} deberian faltar factores: {body}'
            temp = field(body, 'temp_token')
            assert temp, f'falta temp_token rolling tras {factor}: {body}'
        else:
            # Contrato final: completo + token final.
            assert body.get('mfa_complete') is True, (
                f'ultimo factor {factor}: esperaba mfa_complete=true, body={body}'
            )
            assert field(body, 'access_token'), f'falta access_token: {body}'
            assert field(body, 'refresh_token'), f'falta refresh_token: {body}'
            final_body = body
    return final_body


def _setup_user(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str,
    created_emails: list[str],
    *,
    with_totp: bool,
    with_webauthn: bool,
) -> dict:
    """Crea un user active con password + (opcional) totp/webauthn required."""
    origin = admin_origin(env)
    admin = admin_origin(env)
    email = f'success+mfck-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http,
        environment,
        origin,
        email,
        bypass,
    )
    assert user_id is not None
    # access fresco para el enroll (password unico required aun).
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
    enroll: dict = {'email': email, 'user_id': user_id}
    if with_totp:
        enroll['secret'] = _enroll_totp(http, origin, access)
    if with_webauthn:
        enroll['passkey'] = _enroll_passkey(http, origin, admin, access)
    return enroll


@pytest.mark.api
def test_login_checklist_password_and_totp(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user con password + totp `required`,
    When completa ambos factores del checklist (password -> totp),
    Then los intermedios dan mfa_complete=false + methods, y el ultimo da
        mfa_complete=true + access/refresh.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')
    enroll = _setup_user(
        http,
        environment,
        env,
        bypass,
        created_emails,
        with_totp=True,
        with_webauthn=False,
    )
    _run_checklist(
        http,
        environment,
        env,
        bypass,
        factors_order=['password', 'totp'],
        enroll=enroll,
    )


@pytest.mark.api
def test_login_checklist_password_and_webauthn(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user con password + webauthn (passkey) `required`,
    When completa password y luego el passkey (con el temp del checklist),
    Then el login converge (mfa_complete=true + tokens) — el passkey acumula el
        password ya hecho (regresion del bug del checklist multi-factor).
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')
    enroll = _setup_user(
        http,
        environment,
        env,
        bypass,
        created_emails,
        with_totp=False,
        with_webauthn=True,
    )
    _run_checklist(
        http,
        environment,
        env,
        bypass,
        factors_order=['password', 'webauthn'],
        enroll=enroll,
    )


@pytest.mark.api
def test_login_checklist_three_factors_arbitrary_order(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user con password + totp + webauthn `required`,
    When completa los 3 en orden arbitrario (webauthn -> password -> totp),
    Then solo el ULTIMO factor cierra el login (mfa_complete=true + tokens);
        los 2 intermedios dan mfa_complete=false con los pendientes correctos.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')
    enroll = _setup_user(
        http,
        environment,
        env,
        bypass,
        created_emails,
        with_totp=True,
        with_webauthn=True,
    )
    _run_checklist(
        http,
        environment,
        env,
        bypass,
        factors_order=['webauthn', 'password', 'totp'],
        enroll=enroll,
    )
