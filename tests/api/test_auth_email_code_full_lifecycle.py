"""E2E del ciclo de vida COMPLETO del metodo email_code (codigo de 8 chars).

Centraliza la cobertura del factor email_code de punta a punta (antes solo
tenia un setup + list + disable suelto en _flows.py, sin login 2FA ni
set-required):

1. setup-email-code -> 204 (IDEMPOTENTE: el email_code ya lo creo el alta, el
   email se verifico al registrarse; este setup explicito es un no-op seguro).
2. security.overview refleja email_code configured + enabled (ya desde el alta).
3. set-required email_code -> 204 (ahora es un factor exigido al loguear).
4. login completo por el checklist: login.start lista [password, email_code] ->
   verify-password (intermedio) -> send-email-code (envia el code) -> el harness
   seedea el hash del code en Neon -> verify-code (cierra) -> access + refresh.
5. disable email_code -> 204 (queda el TOTP, no dispara MUST_KEEP_ONE).

El code de 8 chars NO vuelve en la respuesta (solo viaja por email); el harness
lo seedea en Neon con `Environment.seed_code(kind='login')` (el mismo patron del
flujo de alta). Para que el disable de email_code NO choque con
MUST_KEEP_ONE_MFA_METHOD, el user tiene ademas un TOTP confirmado.

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

# Code de 8 chars Crockford-like (A-HJ-NP-Z2-9) que el harness seedea en Neon.
_LOGIN_CODE = 'ABCDEFGH'


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
def test_email_code_full_lifecycle_setup_required_login_disable(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user active con password + TOTP confirmado,
    When activa email_code (setup -> set-required), inicia sesion completando
        password + email_code en el checklist, y luego lo deshabilita,
    Then cada paso responde su contrato y el login converge con access+refresh.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+emclc-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http, environment, origin, email, bypass,
    )
    assert user_id is not None
    access = _access_via_password(http, origin, email, bypass)
    # TOTP confirmado: deja >=2 MFA para que el disable de email_code no choque.
    _enroll_totp(http, origin, access)

    # 1. setup-email-code -> 204 (confirmado de inmediato).
    setup = http.post(
        '/auth', body=make_body('mfa', 'setup-email-code'), origin=origin,
        bearer=access,
    )
    assert setup.status == 204, f'setup-email-code fallo: {setup.status} {setup.body}'

    # 2. overview: email_code configured + enabled.
    overview = _overview_by_type(http, origin, access)
    assert overview['email_code']['configured'] is True
    assert overview['email_code']['enabled'] is True

    # 3. set-required email_code -> 204.
    req = http.post(
        '/auth',
        body=make_body('mfa', 'set-required', kind='email_code', required=True),
        origin=origin, bearer=access,
    )
    assert req.status == 204, f'set-required email_code fallo: {req.status} {req.body}'

    # 4. login completo: password (intermedio) -> email_code (cierra).
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth', body=make_body('login', 'start'), origin=origin,
        bearer=precheck,
    )
    methods = set(start.body.get('methods') or [])
    assert 'email_code' in methods and 'password' in methods, (
        f'login.start deberia exigir password+email_code: {start.body}'
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
        f'tras password aun falta email_code: {vp.body}'
    )
    temp2 = field(vp.body, 'temp_token')
    assert temp2, f'falta temp rolling tras password: {vp.body}'

    # send-email-code: dispara el envio (no devuelve el code, viaja por email).
    send = http.post(
        '/auth', body=make_body('login', 'send-email-code', temp_token=temp2),
        origin=origin,
    )
    assert send.status == 200, f'send-email-code fallo: {send.status} {send.body}'
    # el harness seedea el hash del code en Neon (kind='login').
    assert environment.seed_code(
        user_id=user_id, kind='login', plaintext=_LOGIN_CODE,
    ), 'seed_code no actualizo ninguna fila de login code'

    vc = http.post(
        '/auth',
        body=make_body('login', 'verify-code', code=_LOGIN_CODE, temp_token=temp2),
        origin=origin,
    )
    assert vc.body.get('mfa_complete') is True, (
        f'email_code deberia cerrar el login: {vc.body}'
    )
    assert field(vc.body, 'access_token'), f'falta access_token final: {vc.body}'
    assert field(vc.body, 'refresh_token'), f'falta refresh_token final: {vc.body}'

    # 5. disable email_code -> 204 (queda el TOTP).
    disabled = http.post(
        '/auth', body=make_body('mfa', 'disable', kind='email_code'),
        origin=origin, bearer=access,
    )
    assert disabled.status == 204, (
        f'disable email_code deberia ser 204 (TOTP queda): '
        f'{disabled.status} {disabled.body}'
    )
    after = _overview_by_type(http, origin, access)
    assert after['email_code']['enabled'] is False, (
        f'email_code deberia quedar deshabilitado: {after["email_code"]}'
    )
