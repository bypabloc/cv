"""E2E del ciclo de vida COMPLETO de los recovery codes (escape anti-lockout).

Centraliza la cobertura de los recovery codes de punta a punta (antes solo
generate + consume + reuso suelto en _flows.py, sin overview ni regenerate):

1. recovery-codes-generate -> 200 con 10 codes (mostrados una sola vez).
2. security.overview refleja recovery_codes total=10, remaining=10.
3. login con un factor FUERTE (password) -> temp step=2 flow='login-mfa'.
4. recovery-codes-consume con un code -> 200 (bypassea TODOS los required,
   emite access+refresh). El recovery es el escape anti-lockout.
5. overview: remaining baja a 9 (un code consumido).
6. reuso del MISMO code (con un temp nuevo) -> 400 RECOVERY_CODE_CONSUMED.
7. regenerate -> 200 con 10 codes NUEVOS; los viejos quedan invalidados (un
   code viejo no consumido ya no matchea -> 400).

El user tiene password + TOTP required (para que el login emita un temp step=2
de factor fuerte, requisito de recovery-codes-consume). Los codes vuelven en
claro SOLO en la respuesta de generate (nunca se reofrecen).

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


def _codes(body: object) -> list[str]:
    """Extrae la lista de recovery codes de la respuesta de generate."""
    if not isinstance(body, dict):
        return []
    data = body.get('data')
    container = data if isinstance(data, dict) else body
    raw = container.get('codes')
    return [c for c in raw if isinstance(c, str)] if isinstance(raw, list) else []


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


def _strong_temp_step2(
    http: HttpClient, origin: str, email: str, bypass: str,
) -> str:
    """Login con MFA hasta el temp step=2 de factor fuerte (password hecho).

    login.start (precheck) -> verify-password: como el user tiene un required
    pendiente (totp), verify-password NO cierra el login; emite un temp step=2
    rolling (flow='login-mfa:password') que recovery-codes-consume acepta.
    """
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
    assert vp.body.get('mfa_complete') is False, (
        f'con totp required, verify-password no deberia cerrar: {vp.body}'
    )
    temp = field(vp.body, 'temp_token')
    assert temp, f'falta temp step=2 tras verify-password: {vp.body}'
    return temp


def _recovery_overview(http: HttpClient, origin: str, access: str) -> dict:
    """security.overview -> la entry de recovery_codes (con su detail)."""
    r = http.post(
        '/auth', body=make_body('security', 'overview'), origin=origin,
        bearer=access,
    )
    by_type = {m['type']: m for m in (r.body.get('methods') or [])}
    return by_type['recovery_codes']


@pytest.mark.api
def test_recovery_codes_full_lifecycle_generate_consume_regenerate(
    http: HttpClient,
    environment: Environment,
    env: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un user active con password + TOTP required,
    When genera recovery codes, consume uno como escape (bypass MFA), reusa el
        mismo (rechazado) y regenera (invalida los viejos),
    Then cada paso responde su contrato: consume emite tokens, reuso 400,
        overview refleja el remaining, regenerate invalida los anteriores.
    """
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible')

    origin = admin_origin(env)
    email = f'success+rclc-{secrets.token_hex(4)}@simulator.amazonses.com'
    created_emails.append(email)
    user_id = create_active_user_with_password(
        http, environment, origin, email, bypass,
    )
    assert user_id is not None
    access = _access_via_password(http, origin, email, bypass)

    # TOTP confirmado + required: el login emite un temp step=2 de factor fuerte.
    setup = http.post(
        '/auth', body=make_body('mfa', 'setup-totp'), origin=origin,
        bearer=access,
    )
    secret = field(setup.body, 'secret_b32')
    assert secret is not None
    assert http.post(
        '/auth', body=make_body('mfa', 'confirm-totp', code=totp_now(secret)),
        origin=origin, bearer=access,
    ).status == 204
    http.post(
        '/auth', body=make_body('mfa', 'set-required', kind='totp', required=True),
        origin=origin, bearer=access,
    )

    # 1. generate -> 10 codes.
    gen = http.post(
        '/auth', body=make_body('mfa', 'recovery-codes-generate'),
        origin=origin, bearer=access,
    )
    assert gen.status == 200, f'recovery-codes-generate fallo: {gen.body}'
    codes = _codes(gen.body)
    assert len(codes) == 10, f'deberian ser 10 codes, fueron {len(codes)}: {gen.body}'

    # 2. overview: total=10, remaining=10.
    ov = _recovery_overview(http, origin, access)
    assert ov['detail'] == {'total': 10, 'remaining': 10}, (
        f'overview recovery inicial: {ov}'
    )

    # 3-4. login factor fuerte -> consume un code -> 200 + tokens (bypass MFA).
    temp = _strong_temp_step2(http, origin, email, bypass)
    consume = http.post(
        '/auth',
        body=make_body(
            'mfa', 'recovery-codes-consume', temp_token=temp, code=codes[0],
        ),
        origin=origin,
    )
    assert consume.status == 200, (
        f'recovery-codes-consume deberia ser 200: {consume.status} {consume.body}'
    )
    assert field(consume.body, 'access_token'), f'falta access_token: {consume.body}'
    assert field(consume.body, 'refresh_token'), f'falta refresh: {consume.body}'

    # 5. overview: remaining baja a 9.
    ov2 = _recovery_overview(http, origin, access)
    assert ov2['detail'] == {'total': 10, 'remaining': 9}, (
        f'overview recovery tras consumir uno: {ov2}'
    )

    # 6. reuso del MISMO code (temp nuevo) -> 400 RECOVERY_CODE_CONSUMED.
    temp2 = _strong_temp_step2(http, origin, email, bypass)
    reuse = http.post(
        '/auth',
        body=make_body(
            'mfa', 'recovery-codes-consume', temp_token=temp2, code=codes[0],
        ),
        origin=origin,
    )
    assert reuse.status == 400, (
        f'reusar un code consumido deberia ser 400: {reuse.status} {reuse.body}'
    )

    # 7. regenerate -> 10 codes nuevos; un code VIEJO no consumido ya no sirve.
    regen = http.post(
        '/auth', body=make_body('mfa', 'recovery-codes-generate'),
        origin=origin, bearer=access,
    )
    assert regen.status == 200, f'regenerate fallo: {regen.body}'
    new_codes = _codes(regen.body)
    assert len(new_codes) == 10
    assert set(new_codes).isdisjoint(set(codes)), (
        'los codes regenerados no deberian repetir los viejos'
    )
    temp3 = _strong_temp_step2(http, origin, email, bypass)
    old_unused = http.post(
        '/auth',
        body=make_body(
            'mfa', 'recovery-codes-consume', temp_token=temp3, code=codes[1],
        ),
        origin=origin,
    )
    assert old_unused.status == 400, (
        f'un code viejo (pre-regenerate) ya no deberia servir: '
        f'{old_unused.status} {old_unused.body}'
    )
