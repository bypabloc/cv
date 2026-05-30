"""Flujo auth: registro completo (exito) + casos de error.

Flujo de exito (con seed de Neon para el paso verify-code):
  register.start -> seed code -> register.verify-code (access+refresh)
  -> session.refresh -> login.start -> verify.set-password
  -> session.logout

Shapes confirmados contra dev (campos anidados bajo `data`):
  register.start      -> 200 {data: {temp_token, user_id, expires_in, ...}}
  register.verify-code-> 200 {data: {access_token, refresh_token, ...}}

Casos de error: login.start de email inexistente (404), tokens falsos en
los verify (4xx), mfa/webauthn sin JWT valido (401/4xx).

Devuelve el `access_token` del user creado para que el flujo de `users`
lo reutilice.
"""

from __future__ import annotations

from api_e2e.config import admin_origin
from api_e2e.config import synthetic_email
from api_e2e.environment import Environment
from api_e2e.runner import Runner
from api_e2e.runner import make_body
from api_e2e.support import HttpClient


_STRONG_PASSWORD = 'api-e2e-Str0ng-Passphrase!'
_FAKE_JWT = 'FAKE-TOKEN-API-E2E-NOT-A-REAL-JWT-XXXXXXXXXXXXXXXXXXXXXXXX'


def run_auth(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    env_name: str,
    run_id: str,
    bypass: str | None,
    created_emails: list[str],
) -> str | None:
    """Corre el flujo auth. Devuelve el access_token del user creado."""
    origin = admin_origin(env_name)
    access_token: str | None = None

    if bypass:
        access_token = _run_success(
            runner,
            http,
            env,
            origin,
            run_id,
            bypass,
            created_emails,
        )
    else:
        print('  [SKIP] flujo auth de exito: bypass Turnstile no disponible')

    _run_errors(runner, http, origin, bypass)
    return access_token


def _run_success(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> str | None:
    """Flujo de registro->sesion completo. Devuelve access_token final."""
    email = synthetic_email(run_id, 'auth')
    created_emails.append(email)

    # 1. register.start -> temp_token, user_id
    r = runner.step(
        lambda_name='auth',
        name='register.start (success)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body(
                'register',
                'start',
                email=email,
                cf_turnstile_response='',
            ),
            origin=origin,
            bypass_secret=bypass,
        ),
        expected=200,
    )
    temp_token = _field(r.body, 'temp_token')
    user_id = _field(r.body, 'user_id') or env.find_user_id(email)
    if not (temp_token and user_id):
        return None

    # 2. seed code + register.verify-code -> access+refresh
    seeded = env.seed_code(
        user_id=user_id,
        kind='register',
        plaintext='ABCDEFGH',
    )
    r = runner.step(
        lambda_name='auth',
        name='register.verify-code (success)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body(
                'register',
                'verify-code',
                code='ABCDEFGH',
                temp_token=temp_token,
            ),
            origin=origin,
        ),
        expected=200,
        note='code sembrado en Neon' if seeded else 'seed FALLO',
    )
    access_token = _field(r.body, 'access_token')
    refresh_token = _field(r.body, 'refresh_token')

    # 3. session.refresh -> rota el refresh
    if refresh_token:
        r = runner.step(
            lambda_name='auth',
            name='session.refresh (success)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body(
                    'session',
                    'refresh',
                    refresh_token=refresh_token,
                ),
                origin=origin,
            ),
            expected=200,
        )
        access_token = _field(r.body, 'access_token') or access_token

    # 4. login.start (success) -> nuevo temp para set-password
    r = runner.step(
        lambda_name='auth',
        name='login.start (success)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body(
                'login',
                'start',
                email=email,
                cf_turnstile_response='',
            ),
            origin=origin,
            bypass_secret=bypass,
        ),
        expected=200,
    )
    login_temp = _field(r.body, 'temp_token')

    # 5. verify.set-password con el temp del login
    if login_temp:
        runner.step(
            lambda_name='auth',
            name='verify.set-password (success)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body(
                    'verify',
                    'set-password',
                    password=_STRONG_PASSWORD,
                    temp_token=login_temp,
                ),
                origin=origin,
            ),
            expected='2xx',
        )

    # 6. session.logout con el access vigente -> 200/204
    if access_token:
        runner.step(
            lambda_name='auth',
            name='session.logout (success)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body('session', 'logout', access_token=access_token),
                origin=origin,
                bearer=access_token,
            ),
            expected=[200, 204],
        )

    return access_token


def _run_errors(
    runner: Runner,
    http: HttpClient,
    origin: str,
    bypass: str | None,
) -> None:
    """Casos de error de auth (no mutan / no requieren estado valido)."""
    if bypass:
        runner.case(
            lambda_name='auth',
            name='login.start (error: email inexistente)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body(
                    'login',
                    'start',
                    email='nadie-api-e2e@simulator.amazonses.com',
                    cf_turnstile_response='',
                ),
                origin=origin,
                bypass_secret=bypass,
            ),
            expected=404,
        )
    runner.case(
        lambda_name='auth',
        name='register.verify-code (error: token falso)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body(
                'register',
                'verify-code',
                code='ABCDEFGH',
                temp_token=_FAKE_JWT,
            ),
            origin=origin,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='auth',
        name='session.refresh (error: token falso)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('session', 'refresh', refresh_token=_FAKE_JWT),
            origin=origin,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='auth',
        name='mfa.list (error: JWT falso)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('mfa', 'list'),
            origin=origin,
            bearer=_FAKE_JWT,
        ),
        expected=401,
    )
    runner.case(
        lambda_name='auth',
        name='webauthn.login-verify (error: payload vacio)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body(
                'webauthn',
                'login-verify',
                email='x@simulator.amazonses.com',
                credential={},
            ),
            origin=origin,
        ),
        expected='4xx',
    )


def _field(body: object, key: str) -> str | None:
    """Extrae body[key] o body['data'][key]; None si no esta o no es str."""
    if not isinstance(body, dict):
        return None
    if isinstance(body.get(key), str):
        return body[key]
    data = body.get('data')
    if isinstance(data, dict) and isinstance(data.get(key), str):
        return data[key]
    return None
