"""Flujo auth: registro + login (passwordless, magic-link, password) + MFA.

Flujo de exito base (con seed de Neon para los pasos verify):
  register.start -> seed code -> register.verify-code (access1+refresh1)
  -> session.refresh (access2+refresh2) -> login.start
  -> verify.set-password -> session.logout(access1)

Encima de eso, este harness ejercita TODO el dominio auth del dashboard:
- register.verify-magic-link por GET (302 al admin/callback) y por POST
  (JSON con tokens) — el fix del magic-link.
- login con password directo (login.start con password -> tokens) +
  variante 2-step (login.verify-password).
- MFA TOTP completo: setup -> confirm -> login con 2FA (en flow_auth_mfa).
- MFA email-code, recovery codes (generate -> consume), set-preferred,
  disable (en flow_auth_mfa).

Detalle critico del token: el logout base se hace sobre `access1` (el de
verify-code), NO sobre `access2` (el de refresh). logout sin refresh_token
solo blacklistea el jti del access, no la familia — asi `access2` sigue
vivo y se devuelve para que el flujo de `users` lo reutilice.

Casos de error: login.start de email inexistente (404), tokens falsos en
los verify (4xx), mfa/webauthn sin JWT valido (401/4xx).
"""

from __future__ import annotations

import secrets

from api_e2e._auth_support import FAKE_JWT
from api_e2e._auth_support import STRONG_PASSWORD
from api_e2e._auth_support import Synthetic
from api_e2e._auth_support import field
from api_e2e._auth_support import register_active_with_password
from api_e2e.config import admin_origin
from api_e2e.config import synthetic_email
from api_e2e.environment import Environment
from api_e2e.flow_auth_mfa import run_mfa_flows
from api_e2e.runner import Runner
from api_e2e.runner import make_body
from api_e2e.support import HttpClient


def run_auth(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    env_name: str,
    run_id: str,
    bypass: str | None,
    created_emails: list[str],
) -> str | None:
    """Corre el flujo auth. Devuelve un access_token VIVO para users."""
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
        _run_magic_link_get(
            runner,
            http,
            env,
            origin,
            run_id,
            bypass,
            created_emails,
        )
        _run_login_with_password(
            runner,
            http,
            env,
            origin,
            run_id,
            bypass,
            created_emails,
        )
        run_mfa_flows(
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
    """Flujo registro->sesion completo. Devuelve access2 (vivo) para users."""
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
            bypass_token=bypass,
        ),
        expected=200,
    )
    temp_token = field(r.body, 'temp_token')
    user_id = field(r.body, 'user_id') or env.find_user_id(email)
    if not (temp_token and user_id):
        return None

    # 2. seed code + register.verify-code -> access1 + refresh1
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
    access1 = field(r.body, 'access_token')
    refresh1 = field(r.body, 'refresh_token')

    # 3. session.refresh(refresh1) -> access2 + refresh2 (rota la familia)
    access2 = access1
    if refresh1:
        r = runner.step(
            lambda_name='auth',
            name='session.refresh (success)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body('session', 'refresh', refresh_token=refresh1),
                origin=origin,
            ),
            expected=200,
        )
        access2 = field(r.body, 'access_token') or access1

    # 4. login.start (success) -> temp del login
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
            bypass_token=bypass,
        ),
        expected=200,
    )
    login_temp = field(r.body, 'temp_token')

    # 5. verify.set-password con el temp del login (user nuevo sin password)
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
                    password=STRONG_PASSWORD,
                    temp_token=login_temp,
                ),
                origin=origin,
            ),
            expected='2xx',
        )

    # 6. session.logout(access1) -> blacklistea SOLO ese jti (no la familia,
    #    no se pasa refresh_token). access2 queda vivo para users.
    if access1:
        runner.step(
            lambda_name='auth',
            name='session.logout (success)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body('session', 'logout', access_token=access1),
                origin=origin,
                bearer=access1,
            ),
            expected=[200, 204],
        )

    return access2


def _run_magic_link_get(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """register.start -> seed magic-link -> verify-magic-link GET (302) + POST.

    Prueba el fix del magic-link: el GET (click en el email) responde 302
    Location al admin/callback con los tokens en el fragment; el POST (el
    admin por fetch) responde 200 JSON. Usa 2 magic-links sembrados (uno
    por metodo: el link es single-use).
    """
    email = synthetic_email(run_id, 'mlink')
    created_emails.append(email)

    r = runner.step(
        lambda_name='auth',
        name='register.start (magic-link GET setup)',
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
            bypass_token=bypass,
        ),
        expected=200,
    )
    user_id = field(r.body, 'user_id') or env.find_user_id(email)
    if not user_id:
        print('  [SKIP] magic-link GET: no user_id')
        return

    # GET: 302 con Location al admin/callback (consume el link single-use).
    token_get = secrets.token_urlsafe(32)
    seeded = env.seed_magic_link(
        user_id=user_id,
        kind='register',
        plaintext=token_get,
    )
    rg = runner.step(
        lambda_name='auth',
        name='register.verify-magic-link (success: GET 302)',
        method='GET',
        call=lambda: http.get(
            '/auth',
            params={
                'operation': 'register',
                'action': 'verify-magic-link',
                'token': token_get,
            },
            origin=origin,
        ),
        expected=302,
        note='link sembrado' if seeded else 'seed FALLO',
    )
    location = rg.header('Location')
    ok_location = bool(location and '/callback#access=' in location)
    runner.step(
        lambda_name='auth',
        name='register.verify-magic-link (GET Location -> admin/callback)',
        method='GET',
        call=lambda: Synthetic(200 if ok_location else 0),
        expected=200,
        note=(
            'Location apunta al callback con #access'
            if ok_location
            else f'Location inesperado: {location!r}'
        ),
    )

    # POST: JSON 200 con los tokens (el admin lo llama por fetch). Necesita
    # un magic-link VIGENTE (sin consumir). El del user anterior ya se
    # consumio en el GET, asi que usamos un user nuevo (su register.start
    # deja una fila fresca register/consumed_at IS NULL para sembrar).
    email_post = synthetic_email(run_id, 'mlinkp')
    created_emails.append(email_post)
    rp = http.post(
        '/auth',
        body=make_body(
            'register',
            'start',
            email=email_post,
            cf_turnstile_response='',
        ),
        origin=origin,
        bypass_token=bypass,
    )
    user_post = field(rp.body, 'user_id') or env.find_user_id(email_post)
    token_post = secrets.token_urlsafe(32)
    if user_post:
        env.seed_magic_link(
            user_id=user_post,
            kind='register',
            plaintext=token_post,
        )
    runner.step(
        lambda_name='auth',
        name='register.verify-magic-link (success: POST JSON)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('register', 'verify-magic-link', token=token_post),
            origin=origin,
        ),
        expected=200,
    )


def _run_login_with_password(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """Registra + setea password + login.start con password -> tokens directos.

    Cubre el login con password (sin MFA): login.start con `password` en el
    body devuelve access+refresh de inmediato (AC-20). Tambien prueba la
    variante 2-step login.verify-password + el error de password incorrecta.
    """
    email = synthetic_email(run_id, 'pwd')
    created_emails.append(email)
    user_id = register_active_with_password(http, env, origin, email, bypass)
    if not user_id:
        print('  [SKIP] login con password: registro fallo')
        return

    # login.start con password -> tokens directos (sin MFA).
    runner.step(
        lambda_name='auth',
        name='login.start con password (success: tokens directos)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body(
                'login',
                'start',
                email=email,
                password=STRONG_PASSWORD,
                cf_turnstile_response='',
            ),
            origin=origin,
            bypass_token=bypass,
        ),
        expected=200,
    )

    # 2-step: login.start sin password -> temp; verify-password -> tokens.
    r = runner.step(
        lambda_name='auth',
        name='login.start (2-step setup)',
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
            bypass_token=bypass,
        ),
        expected=200,
    )
    temp = field(r.body, 'temp_token')
    if temp:
        runner.step(
            lambda_name='auth',
            name='login.verify-password (success: 2-step tokens)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body(
                    'login',
                    'verify-password',
                    temp_token=temp,
                    password=STRONG_PASSWORD,
                ),
                origin=origin,
            ),
            expected=200,
        )

    # login con password incorrecta -> 401 INVALID_PASSWORD.
    runner.case(
        lambda_name='auth',
        name='login.start con password (error: incorrecta -> 401)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body(
                'login',
                'start',
                email=email,
                password='wrong-Passphrase-123',  # noqa: S106
                cf_turnstile_response='',
            ),
            origin=origin,
            bypass_token=bypass,
        ),
        expected=401,
        samples=2,
    )


def _run_errors(
    runner: Runner,
    http: HttpClient,
    origin: str,
    bypass: str | None,
) -> None:
    """Casos de error de auth (no mutan / no requieren estado valido)."""
    if bypass:
        # Email aleatorio garantizado-inexistente (un email fijo podria
        # quedar pending de una corrida previa -> 409 en vez de 404).
        ghost = f'success+ghost-{secrets.token_hex(4)}@simulator.amazonses.com'
        runner.case(
            lambda_name='auth',
            name='login.start (error: email inexistente)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body(
                    'login',
                    'start',
                    email=ghost,
                    cf_turnstile_response='',
                ),
                origin=origin,
                bypass_token=bypass,
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
                temp_token=FAKE_JWT,
            ),
            origin=origin,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='auth',
        name='register.verify-magic-link (error: token falso -> JSON 400)',
        method='GET',
        call=lambda: http.get(
            '/auth',
            params={
                'operation': 'register',
                'action': 'verify-magic-link',
                'token': secrets.token_urlsafe(32),
            },
            origin=origin,
        ),
        expected=400,
    )
    runner.case(
        lambda_name='auth',
        name='session.refresh (error: token falso)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('session', 'refresh', refresh_token=FAKE_JWT),
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
            bearer=FAKE_JWT,
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
