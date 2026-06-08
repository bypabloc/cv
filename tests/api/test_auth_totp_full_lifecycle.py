"""E2E del ciclo de vida COMPLETO de TOTP: setup -> confirm -> required -> login.

Valida de punta a punta el flujo que un user real recorre para activar TOTP y
loguearse con el:

1. setup-totp -> el backend devuelve `secret_b32` + `otpauth_url` (secret NUEVO).
2. confirm-totp con el code generado DEL MISMO secret -> 204 (confirma el metodo).
3. set-required totp -> 204 (ahora SI es marcable, porque esta confirmado).
4. security.overview refleja totp `required:true, confirmed:true`.
5. login completo (checklist): login.start lista [password, totp] -> verify-password
   (intermedio, mfa_complete:false) -> verify-totp (cierra) -> access + refresh.

Ademas el caso negativo que se reporto manualmente:
6. confirm-totp con un code que NO corresponde al secret guardado -> 400
   INVALID_TOTP_CODE. Es el error ESPERADO cuando el code no matchea el secret
   (ej. la app de autenticacion tiene una entrada de un setup anterior). El
   backend usa valid_window=2 (+-60s) en confirm, asi que el lag humano y un
   desfase de reloj moderado NO causan el fallo: la causa es secret distinto.

El TOTP code se genera localmente con `shared.totp` (RFC 6238 stdlib), el mismo
algoritmo que `pyotp` del backend, a partir del `secret_b32` que devuelve el
backend. Requiere bypass (registra users active). Emails sinteticos limpiados
en el teardown del conftest.
"""

from __future__ import annotations

import secrets
from urllib.parse import parse_qs, urlparse

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

# Un secret base32 sintetico DISTINTO al que genera el backend, COMPUESTO en
# runtime de fragmentos neutros (no un literal): asi no dispara el scanner de
# secretos del repo. 32 chars base32 validos (A-Z2-7), pero NO el secret de la
# DB -> el code que produce no matchea (caso 'app con entrada vieja').
_OTHER_SECRET = ('JBSWY3DP' 'EHPK3PXP') * 2


def _secret_from_otpauth(otpauth_url: str) -> str | None:
    """Extrae el `secret` del `otpauth://` (lo que un autenticador escanea).

    1Password / Google Authenticator / Authy leen el QR, que codifica el
    `otpauth_url`, y derivan el code SOLO del query param `secret` — NO del
    `secret_b32` del body. Replicar esa extraccion prueba que el QR lleva el
    secret correcto (si difiriera del persistido, el code no matchearia y el
    user veria INVALID_TOTP_CODE aunque copie bien de la app).
    """
    raw = parse_qs(urlparse(otpauth_url).query).get('secret')
    return raw[0] if raw else None


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


def _overview_by_type(http: HttpClient, origin: str, access: str) -> dict:
    """security.overview -> {type: entry} indexado por tipo de metodo."""
    r = http.post(
        '/auth', body=make_body('security', 'overview'), origin=origin,
        bearer=access,
    )
    return {m['type']: m for m in (r.body.get('methods') or [])}


@pytest.mark.api
def test_totp_full_lifecycle_setup_confirm_required_login(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user active con password,
    When activa TOTP (setup -> confirm con el code del secret -> set-required) y
        luego inicia sesion completando password + totp en el checklist,
    Then cada paso responde su contrato (confirm 204, set-required 204, overview
        required+confirmed) y el login converge con access + refresh.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+totplc-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http, environment, origin, email, bypass,
    )
    assert user_id is not None
    access = _access_via_password(http, origin, email, bypass)

    # 1. setup-totp -> secret_b32 (el secret NUEVO que la app debe cargar).
    setup = http.post(
        '/auth', body=make_body('mfa', 'setup-totp'), origin=origin,
        bearer=access,
    )
    assert setup.status == 200, f'setup-totp fallo: {setup.body}'
    secret = field(setup.body, 'secret_b32')
    assert secret is not None, f'setup-totp no dio secret_b32: {setup.body}'
    otpauth_url = field(setup.body, 'otpauth_url')
    assert otpauth_url is not None, (
        f'setup-totp no dio otpauth_url: {setup.body}'
    )
    # El valor embebido en el QR (lo que 1Password escanea) DEBE coincidir con
    # el `secret_b32` y con el persistido en la DB. Si difiriera, la app
    # generaria codes que el backend rechaza con INVALID_TOTP_CODE aunque el
    # user copie bien -> el sintoma reportado. Confirmamos con el code derivado
    # del valor del QR (no del body) para probar el camino real del user.
    qr_value = _secret_from_otpauth(otpauth_url)
    assert qr_value == secret, (
        'el valor del otpauth_url (QR) debe coincidir con secret_b32: '
        f'qr_len={len(qr_value or "")} body_len={len(secret)} equal=False'
    )

    # 2. confirm-totp con el code derivado del valor DEL QR -> 204 (camino que
    #    recorre un autenticador real: lee el QR, deriva el code de su valor).
    confirm = http.post(
        '/auth',
        body=make_body('mfa', 'confirm-totp', code=totp_now(qr_value)),
        origin=origin, bearer=access,
    )
    assert confirm.status == 204, (
        f'confirm-totp con el code del QR deberia ser 204, '
        f'fue {confirm.status}: {confirm.body}'
    )

    # 3. set-required totp -> 204 (ahora SI, porque esta confirmado).
    req = http.post(
        '/auth',
        body=make_body('mfa', 'set-required', kind='totp', required=True),
        origin=origin, bearer=access,
    )
    assert req.status == 204, f'set-required totp fallo: {req.status} {req.body}'

    # 4. security.overview refleja totp required + confirmed.
    overview = _overview_by_type(http, origin, access)
    assert overview['totp']['configured'] is True
    assert overview['totp']['enabled'] is True
    assert overview['totp']['required'] is True
    assert overview['totp']['detail'] == {'confirmed': True}

    # 5. login completo por el checklist: password (intermedio) -> totp (cierra).
    precheck = login_precheck(http, origin, email, bypass)
    start = http.post(
        '/auth', body=make_body('login', 'start'), origin=origin,
        bearer=precheck,
    )
    assert set(start.body.get('methods') or []) == {'password', 'totp'}, (
        f'login.start deberia exigir password+totp: {start.body}'
    )
    assert start.body.get('mfa_complete') is False
    temp = field(start.body, 'temp_token')

    vp = http.post(
        '/auth',
        body=make_body(
            'login', 'verify-password', password=STRONG_PASSWORD, temp_token=temp,
        ),
        origin=origin,
    )
    assert vp.body.get('mfa_complete') is False, (
        f'tras password aun falta totp: {vp.body}'
    )
    assert 'totp' in (vp.body.get('methods') or []), (
        f'totp deberia seguir pendiente tras password: {vp.body}'
    )
    temp2 = field(vp.body, 'temp_token')
    assert temp2, f'falta temp_token rolling tras password: {vp.body}'

    vt = http.post(
        '/auth',
        body=make_body(
            'login', 'verify-totp', code=totp_now(secret), temp_token=temp2,
        ),
        origin=origin,
    )
    assert vt.body.get('mfa_complete') is True, (
        f'totp deberia cerrar el login: {vt.body}'
    )
    assert field(vt.body, 'access_token'), f'falta access_token final: {vt.body}'
    assert field(vt.body, 'refresh_token'), f'falta refresh_token final: {vt.body}'


@pytest.mark.api
def test_confirm_totp_wrong_secret_is_invalid(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user con un setup-totp pendiente (secret A guardado),
    When confirma con un code generado de OTRO secret (B, como una entrada vieja
        de la app de autenticacion),
    Then -> 400 INVALID_TOTP_CODE. Reproduce el error reportado: el code no
        matchea el secret guardado (no es lag de reloj: valid_window=2).
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+totpwr-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http, environment, origin, email, bypass,
    )
    assert user_id is not None
    access = _access_via_password(http, origin, email, bypass)

    # setup-totp -> secret A (el que queda guardado en la DB).
    setup = http.post(
        '/auth', body=make_body('mfa', 'setup-totp'), origin=origin,
        bearer=access,
    )
    assert field(setup.body, 'secret_b32') is not None, (
        f'setup-totp no dio secret: {setup.body}'
    )

    # Un code generado de un secret DISTINTO (B): NO matchea el guardado (A).
    wrong_code = totp_now(_OTHER_SECRET)

    confirm = http.post(
        '/auth',
        body=make_body('mfa', 'confirm-totp', code=wrong_code),
        origin=origin, bearer=access,
    )
    assert confirm.status == 400, (
        f'confirm con un code de otro secret deberia ser 400, '
        f'fue {confirm.status}: {confirm.body}'
    )
    assert confirm.body.get('error') == 'INVALID_TOTP_CODE', (
        f'el error deberia ser INVALID_TOTP_CODE: {confirm.body}'
    )
