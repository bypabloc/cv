"""Flujos imperativos del modulo api (port verbatim de `devtools/api_e2e`).

Estrategia C-A del plan: cada flow de `api_e2e/flow_*.py` se porta aqui
1:1 (misma cobertura, mismos casos PASS/FAIL, mismos samples), pero
importando del portador `shared.*` (`tests/shared/`) en vez de
`api_e2e.*`. Cada `test_*.py` del modulo invoca UNA de estas funciones
contra el `Runner`/`Reporter` de sesion; pytest aporta descubrimiento,
markers y `-k`, mientras el detalle de samples + la tabla de tiempos
viven en el `Runner`/`Reporter` (la fuente del resumen, igual que
`api_e2e/main.py`).

El prefijo `_` evita que pytest recolecte este modulo como tests.
"""

from __future__ import annotations

from collections.abc import Callable
import secrets
import time

from shared.auth_support import FAKE_JWT
from shared.auth_support import STRONG_PASSWORD
from shared.auth_support import WRONG_PASSWORD
from shared.auth_support import Synthetic
from shared.auth_support import field
from shared.auth_support import register_active_with_password
from shared.config import NICHE
from shared.config import TRACKING_EVENT_TYPE_ID
from shared.config import admin_origin
from shared.config import apex_origin
from shared.config import cv_origin
from shared.config import synthetic_email
from shared.environment import Environment
from shared.http import HttpClient
from shared.http import Response
from shared.reporter import Reporter
from shared.runner import Runner
from shared.runner import make_body
from shared.runner import matches_status
from shared.totp import totp_now


# =========================================================================
# Helper de assert: el Runner clasifica PASS/FAIL por caso (mismo veredicto
# que api_e2e). Cada test verifica que TODOS los casos de SU Lambda pasaron.
# =========================================================================


def assert_cases_passed(reporter: Reporter, *, since: int) -> None:
    """Falla el test si algun caso registrado DESDE `since` no paso.

    El Runner ya marco PASS/FAIL por caso contra el status esperado (int,
    lista o rango). Este helper lo eleva al nivel de pytest: mira SOLO los
    casos que este test agrego (los de indice >= `since`), para no acoplar
    un test a los casos de otro (ej. test_auth y test_auth_mfa comparten el
    lambda_name 'auth'). Mensaje con los fallos (codes vs esperado).
    """
    added = reporter.results[since:]
    fails = [r for r in added if not r.passed]
    detail = '\n'.join(
        f'{r.lambda_name}.{r.name}: codes={r.status_codes} '
        f'esperado={r.expected}'
        for r in fails
    )
    assert not fails, f'{len(fails)}/{len(added)} casos FAIL\n{detail}'


# =========================================================================
# Port de flow_readonly -> cv (read) + contact_form + tracking_pixel
# =========================================================================

_CV_ACTIONS = (
    'get',
    'profile',
    'experiences',
    'projects',
    'certificates',
    'awards',
    'education',
    'languages',
    'references',
    'skills',
)


def run_cv(runner: Runner, http: HttpClient, env: str) -> None:
    """cv: las 10 actions read (2xx) + 2 errores (action/operation)."""
    origin = cv_origin(env)
    for action in _CV_ACTIONS:
        params = {'operation': 'cv', 'action': action, 'locale': 'es'}
        if action != 'profile':
            params['niche'] = NICHE
        runner.case(
            lambda_name='cv',
            name=f'cv.{action} (success)',
            method='GET',
            call=lambda p=params: http.get('/cv', params=p, origin=origin),
            expected='2xx',
        )
    runner.case(
        lambda_name='cv',
        name='cv.nope (error: action invalida)',
        method='GET',
        call=lambda: http.get(
            '/cv',
            params={'operation': 'cv', 'action': 'nope', 'locale': 'es'},
            origin=origin,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='cv',
        name='cv (error: sin operation)',
        method='GET',
        call=lambda: http.get(
            '/cv',
            params={'action': 'get'},
            origin=origin,
        ),
        expected='4xx',
    )


def run_contact(
    runner: Runner,
    http: HttpClient,
    env: str,
    run_id: str,
    bypass: str | None,
    created_emails: list[str],
) -> None:
    """contact_form: create exitoso (202 via bypass) + errores de payload."""
    origin = apex_origin(env)
    if bypass:
        email = synthetic_email(run_id, 'contact')
        created_emails.append(email)
        runner.case(
            lambda_name='contact_form',
            name='contact.create (success)',
            method='POST',
            call=lambda: http.post(
                '/contact',
                body=make_body(
                    'contact',
                    'create',
                    name='API E2E',
                    email=email,
                    message='Mensaje de prueba E2E del harness api_e2e.',
                    cf_token='',
                ),
                origin=origin,
                bypass_token=bypass,
            ),
            expected='2xx',
            samples=2,
            note='via bypass Turnstile',
        )
    else:
        print('  [SKIP] contact.create (success): bypass no disponible')

    runner.case(
        lambda_name='contact_form',
        name='contact.create (error: sin message)',
        method='POST',
        call=lambda: http.post(
            '/contact',
            body=make_body(
                'contact',
                'create',
                name='API E2E',
                email='success+e2e@simulator.amazonses.com',
                cf_token='',
            ),
            origin=origin,
            bypass_token=bypass,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='contact_form',
        name='contact.create (error: email invalido)',
        method='POST',
        call=lambda: http.post(
            '/contact',
            body=make_body(
                'contact',
                'create',
                name='API E2E',
                email='no-es-un-email',
                message='mensaje suficientemente largo para pasar',
                cf_token='',
            ),
            origin=origin,
            bypass_token=bypass,
        ),
        expected='4xx',
    )


def run_tracking(
    runner: Runner,
    http: HttpClient,
    env: str,
    run_id: str,
    created_sessions: list[str],
) -> None:
    """tracking_pixel: track exitoso (202) + errores de payload."""
    origin = apex_origin(env)
    session_id = f'sess-{run_id}-track-000000000000'
    created_sessions.append(session_id)

    def _track_body(**over: object) -> dict:
        base: dict[str, object] = {
            'session_id': session_id,
            'event_id': 'a1b2c3d4e5f60718293a4b5c6d7e8f90',
            'event_type_id': TRACKING_EVENT_TYPE_ID,
            'page_url': 'https://the-full-stack.com/projects',
            'page_title': 'Projects',
            'page_path': '/projects',
            'utm_source': 'e2e',
            'utm_medium': 'api',
            'utm_campaign': 'verify',
            'utm_content': 'run',
            'viewport_width': 1920,
            'viewport_height': 1080,
            'niche': NICHE,
        }
        base.update(over)
        return make_body('tracking', 'track', **base)

    runner.case(
        lambda_name='tracking_pixel',
        name='tracking.track (success)',
        method='POST',
        call=lambda: http.post('/track', body=_track_body(), origin=origin),
        expected='2xx',
        samples=3,
    )
    runner.case(
        lambda_name='tracking_pixel',
        name='tracking.track (error: sin event_type_id)',
        method='POST',
        call=lambda: http.post(
            '/track',
            body=make_body(
                'tracking',
                'track',
                session_id=session_id,
                event_id='a1b2c3d4e5f60718293a4b5c6d7e8f90',
                page_url='https://the-full-stack.com/p',
                page_title='P',
                page_path='/p',
                utm_source='e2e',
                utm_medium='api',
                utm_campaign='verify',
                utm_content='run',
                viewport_width=1920,
                viewport_height=1080,
                niche=NICHE,
            ),
            origin=origin,
        ),
        expected='4xx',
    )
    runner.case(
        lambda_name='tracking_pixel',
        name='tracking.track (error: viewport invalido)',
        method='POST',
        call=lambda: http.post(
            '/track',
            body=_track_body(viewport_width=999999),
            origin=origin,
        ),
        expected='4xx',
    )


# =========================================================================
# Port de flow_auth -> register + login (passwordless/magic-link/password)
# =========================================================================


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
        access_token = _run_auth_success(
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
        # MFA: NO se invoca aqui — lo corre `test_auth_mfa.py` (porta
        # `flow_auth_mfa.run_mfa_flows`). En api_e2e este `run_auth`
        # encadenaba `run_mfa_flows`; el split a un archivo por escenario
        # (un test por flow) lo separa para que cada caso corra UNA vez.
    else:
        print('  [SKIP] flujo auth de exito: bypass Turnstile no disponible')

    _run_auth_errors(runner, http, origin, bypass)
    return access_token


def _run_auth_success(
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
                password=WRONG_PASSWORD,
                cf_turnstile_response='',
            ),
            origin=origin,
            bypass_token=bypass,
        ),
        expected=401,
        samples=2,
    )


def _run_auth_errors(
    runner: Runner,
    http: HttpClient,
    origin: str,
    bypass: str | None,
) -> None:
    """Casos de error de auth (no mutan / no requieren estado valido)."""
    if bypass:
        # Email aleatorio garantizado-inexistente. Tras la fusion
        # register->login (plan admin-security-overview), login.start con un
        # email NUEVO ya NO da 404: CREA el user pending y envia el entry
        # email -> 200 (created:true). El 404 EMAIL_NOT_FOUND queda solo para
        # disabled/locked (anti-enumeration).
        ghost = f'success+ghost-{secrets.token_hex(4)}@simulator.amazonses.com'
        runner.case(
            lambda_name='auth',
            name='login.start (email nuevo -> crea user)',
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
            expected=200,
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


# =========================================================================
# flow_auth_mfa: MFA TOTP, email-code, recovery codes
# =========================================================================


def run_mfa_flows(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """Corre los 3 sub-flujos MFA (TOTP, email-code, recovery codes)."""
    _run_totp(runner, http, env, origin, run_id, bypass, created_emails)
    _run_email_code(runner, http, env, origin, run_id, bypass, created_emails)
    _run_recovery_codes(
        runner,
        http,
        env,
        origin,
        run_id,
        bypass,
        created_emails,
    )


def _setup_totp_confirmed(
    runner: Runner,
    http: HttpClient,
    access: str,
    origin: str,
    *,
    report: bool,
) -> str | None:
    """setup-totp -> genera code -> confirm-totp. Devuelve el b32 generado.

    Si `report`, registra setup+confirm como casos del runner; si no, los
    hace silenciosos (setup de otro sub-flujo). El b32 se usa luego para
    generar codes en el login con MFA.
    """
    if report:
        r = runner.step(
            lambda_name='auth',
            name='mfa.setup-totp (success)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body('mfa', 'setup-totp'),
                origin=origin,
                bearer=access,
            ),
            expected=200,
        )
    else:
        r = http.post(
            '/auth',
            body=make_body('mfa', 'setup-totp'),
            origin=origin,
            bearer=access,
        )
    b32 = field(r.body, 'secret_b32')
    if not b32:
        return None

    code = totp_now(b32)
    if report:
        runner.step(
            lambda_name='auth',
            name='mfa.confirm-totp (success: code valido)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body('mfa', 'confirm-totp', code=code),
                origin=origin,
                bearer=access,
            ),
            expected=204,
        )
    else:
        http.post(
            '/auth',
            body=make_body('mfa', 'confirm-totp', code=code),
            origin=origin,
            bearer=access,
        )
    return b32


def _run_totp(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """TOTP completo: setup -> confirm -> login con 2FA + errores."""
    email = synthetic_email(run_id, 'totp')
    created_emails.append(email)
    user_id = register_active_with_password(http, env, origin, email, bypass)
    access = _login_password_direct(http, origin, email, bypass)
    if not (user_id and access):
        print('  [SKIP] mfa TOTP: setup del user fallo')
        return

    # confirm con code malo -> 400 INVALID_TOTP_CODE (antes de confirmar OK).
    http.post(
        '/auth',
        body=make_body('mfa', 'setup-totp'),
        origin=origin,
        bearer=access,
    )
    runner.case(
        lambda_name='auth',
        name='mfa.confirm-totp (error: code malo -> 400)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('mfa', 'confirm-totp', code='000000'),
            origin=origin,
            bearer=access,
        ),
        expected=400,
        samples=2,
    )

    b32 = _setup_totp_confirmed(runner, http, access, origin, report=True)
    if not b32:
        print('  [SKIP] mfa TOTP: setup-totp no devolvio b32')
        return

    # login con MFA: login.start password -> temp step=2 -> verify-totp.
    temp = _login_start_mfa(runner, http, origin, email, bypass)
    if temp:
        runner.case(
            lambda_name='auth',
            name='login.verify-totp (error: code malo -> 401)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body(
                    'login',
                    'verify-totp',
                    temp_token=temp,
                    code='000000',
                ),
                origin=origin,
            ),
            expected=401,
            samples=2,
        )
        # El temp es rolling: tras un verify fallido sigue vivo (no se
        # blacklistea). Generamos un code fresco y cerramos el login.
        code = totp_now(b32)
        runner.step(
            lambda_name='auth',
            name='login.verify-totp (success: 2FA -> tokens)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body(
                    'login',
                    'verify-totp',
                    temp_token=temp,
                    code=code,
                ),
                origin=origin,
            ),
            expected=200,
        )


def _run_email_code(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """email-code como 2do metodo + list + set-preferred + disable."""
    email = synthetic_email(run_id, 'emfa')
    created_emails.append(email)
    user_id = register_active_with_password(http, env, origin, email, bypass)
    access = _login_password_direct(http, origin, email, bypass)
    if not (user_id and access):
        print('  [SKIP] mfa email-code: setup del user fallo')
        return

    # 1er metodo: TOTP confirmado (silencioso). Asi disable email-code deja
    # el TOTP vivo y el guard MUST_KEEP_ONE no dispara.
    _setup_totp_confirmed(runner, http, access, origin, report=False)

    runner.case(
        lambda_name='auth',
        name='mfa.setup-email-code (success: 2do metodo)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('mfa', 'setup-email-code'),
            origin=origin,
            bearer=access,
        ),
        expected=204,
    )
    runner.case(
        lambda_name='auth',
        name='mfa.list (success: 2 metodos activos)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('mfa', 'list'),
            origin=origin,
            bearer=access,
        ),
        expected=200,
    )
    runner.case(
        lambda_name='auth',
        name='mfa.set-preferred (success: email_code)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('mfa', 'set-preferred', kind='email_code'),
            origin=origin,
            bearer=access,
        ),
        expected='2xx',
        samples=2,
    )
    # samples=1: disable NO es idempotente (tras el 1er 204, el metodo ya
    # no existe -> 404 NOT_FOUND en un 2do intento).
    runner.case(
        lambda_name='auth',
        name='mfa.disable (success: email_code, TOTP queda)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('mfa', 'disable', kind='email_code'),
            origin=origin,
            bearer=access,
        ),
        expected=[200, 204],
        samples=1,
    )


def _run_recovery_codes(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """recovery-codes-generate -> login con MFA -> recovery-codes-consume."""
    email = synthetic_email(run_id, 'rcov')
    created_emails.append(email)
    user_id = register_active_with_password(http, env, origin, email, bypass)
    access = _login_password_direct(http, origin, email, bypass)
    if not (user_id and access):
        print('  [SKIP] mfa recovery: setup del user fallo')
        return

    # MFA activo requerido para que login.start password emita temp step=2.
    _setup_totp_confirmed(runner, http, access, origin, report=False)

    r = runner.case(
        lambda_name='auth',
        name='mfa.recovery-codes-generate (success: 10 codes)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body('mfa', 'recovery-codes-generate'),
            origin=origin,
            bearer=access,
        ),
        expected=200,
    )
    codes = _codes(r.body)
    if len(codes) < 2:
        print('  [SKIP] mfa recovery: no se obtuvieron codes')
        return

    # login con MFA -> temp step=2 -> consume un recovery code.
    temp = _login_start_mfa(runner, http, origin, email, bypass)
    if not temp:
        return
    runner.step(
        lambda_name='auth',
        name='mfa.recovery-codes-consume (success: bypass MFA -> tokens)',
        method='POST',
        call=lambda: http.post(
            '/auth',
            body=make_body(
                'mfa',
                'recovery-codes-consume',
                temp_token=temp,
                code=codes[0],
            ),
            origin=origin,
        ),
        expected=200,
    )

    # Reusar el MISMO code con un temp nuevo -> 400 RECOVERY_CODE_CONSUMED.
    temp2 = _login_start_mfa(runner, http, origin, email, bypass)
    if temp2:
        runner.step(
            lambda_name='auth',
            name='mfa.recovery-codes-consume (error: code ya usado -> 400)',
            method='POST',
            call=lambda: http.post(
                '/auth',
                body=make_body(
                    'mfa',
                    'recovery-codes-consume',
                    temp_token=temp2,
                    code=codes[0],
                ),
                origin=origin,
            ),
            expected=400,
        )


def _login_password_direct(
    http: HttpClient,
    origin: str,
    email: str,
    bypass: str,
) -> str | None:
    """login.start con password de un user SIN MFA -> access token directo.

    Setup silencioso (sin runner): obtiene un access JWT para configurar
    MFA. Se llama ANTES de activar MFA, asi devuelve tokens directos.
    """
    r = http.post(
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
    )
    return field(r.body, 'access_token')


def _login_start_mfa(
    runner: Runner,
    http: HttpClient,
    origin: str,
    email: str,
    bypass: str,
) -> str | None:
    """login.start con password de un user CON MFA -> temp step=2.

    Registra el caso (el login con password de un user con MFA devuelve un
    temp_token step=2, no tokens directos — AC-18).
    """
    r = runner.step(
        lambda_name='auth',
        name='login.start con password+MFA (success: temp step=2)',
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
    return field(r.body, 'temp_token')


def _codes(body: object) -> list[str]:
    """Extrae la lista de recovery codes de la respuesta."""
    if not isinstance(body, dict):
        return []
    data = body.get('data')
    container = data if isinstance(data, dict) else body
    raw = container.get('codes')
    if not isinstance(raw, list):
        return []
    return [c for c in raw if isinstance(c, str)]


# =========================================================================
# Port de flow_users -> profile + status + change-email + delete-account
# =========================================================================

_FAKE_UUID = '00000000-0000-7000-8000-000000000000'
# Credencial nueva para change-password: derivada de STRONG_PASSWORD
# (distinta de la base) cambiando un fragmento, sin ser un literal nuevo.
_NEW_PASSWORD = STRONG_PASSWORD.replace('K7m', 'N3w')


def run_users(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    env_name: str,
    run_id: str,
    bypass: str | None,
    access_token: str | None,
    created_emails: list[str],
) -> None:
    """Corre los casos de users (success si hay access_token + errores)."""
    origin = admin_origin(env_name)

    if access_token:
        _run_self_service(runner, http, origin, access_token)
    else:
        print('  [SKIP] users success: no hay access_token del flujo auth')

    if bypass:
        _run_revoke_session(
            runner,
            http,
            env,
            origin,
            run_id,
            bypass,
            created_emails,
        )
        _run_change_email(
            runner,
            http,
            env,
            origin,
            run_id,
            bypass,
            created_emails,
        )
        # admin.*: NO se invoca aqui — lo corre `test_admin.py` (porta
        # `flow_admin.run_admin`). En api_e2e este `run_users` encadenaba
        # `run_admin`; el split a un archivo por escenario lo separa para
        # que cada caso corra UNA vez.
        _run_delete_account(
            runner,
            http,
            env,
            origin,
            run_id,
            bypass,
            created_emails,
        )

    _run_users_errors(runner, http, origin)


def _run_self_service(
    runner: Runner,
    http: HttpClient,
    origin: str,
    access_token: str,
) -> None:
    """profile.get/update + status.get/list-sessions + change-password."""
    runner.case(
        lambda_name='users',
        name='profile.get (success)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('profile', 'get'),
            origin=origin,
            bearer=access_token,
        ),
        expected='2xx',
    )
    runner.case(
        lambda_name='users',
        name='profile.update (success)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body(
                'profile',
                'update',
                display_name='API E2E User',
                locale='es',
            ),
            origin=origin,
            bearer=access_token,
        ),
        expected='2xx',
        samples=2,
    )
    runner.case(
        lambda_name='users',
        name='status.get (success)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('status', 'get'),
            origin=origin,
            bearer=access_token,
        ),
        expected='2xx',
    )
    runner.case(
        lambda_name='users',
        name='status.list-sessions (success)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('status', 'list-sessions'),
            origin=origin,
            bearer=access_token,
        ),
        expected='2xx',
    )
    runner.case(
        lambda_name='users',
        name='profile.change-password (error: current incorrecta -> 401)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body(
                'profile',
                'change-password',
                current_password=WRONG_PASSWORD,
                new_password=_NEW_PASSWORD,
            ),
            origin=origin,
            bearer=access_token,
        ),
        expected=401,
    )
    # samples=1: el cambio NO es idempotente (tras el 1er 200, la current
    # password ya cambio y un 2do intento daria 401).
    runner.case(
        lambda_name='users',
        name='profile.change-password (success)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body(
                'profile',
                'change-password',
                current_password=STRONG_PASSWORD,
                new_password=_NEW_PASSWORD,
            ),
            origin=origin,
            bearer=access_token,
        ),
        expected='2xx',
        samples=1,
    )


def _run_revoke_session(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """Crea un user con 2 sesiones, revoca la NO-actual (success)."""
    email = synthetic_email(run_id, 'sess')
    created_emails.append(email)
    user_id = register_active_with_password(http, env, origin, email, bypass)
    if not user_id:
        print('  [SKIP] revoke-session: registro fallo')
        return

    # 1er login -> sesion A (la "otra"). 2do login -> sesion B (la actual,
    # cuyo access usamos para el revoke).
    _login_password_direct(http, origin, email, bypass)
    access_b = _login_password_direct(http, origin, email, bypass)
    sessions = env.session_ids(user_id)
    if not (access_b and len(sessions) >= 2):
        print(f'  [SKIP] revoke-session: sesiones={len(sessions)}')
        return

    # La sesion mas vieja (sessions[0]) es de un login previo, no la del
    # access_b en curso -> revocable.
    target = sessions[0]
    runner.case(
        lambda_name='users',
        name='status.revoke-session (success: revoca otra sesion)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('status', 'revoke-session', session_id=target),
            origin=origin,
            bearer=access_b,
        ),
        expected=[200, 204],
        samples=1,
    )


def _run_change_email(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """change-email -> seed token -> confirm-email-change -> verifica en DB."""
    email = synthetic_email(run_id, 'chmail')
    created_emails.append(email)
    user_id = register_active_with_password(http, env, origin, email, bypass)
    access = _login_password_direct(http, origin, email, bypass)
    if not (user_id and access):
        print('  [SKIP] change-email: setup del user fallo')
        return

    new_email = synthetic_email(run_id, 'chmail-new')
    created_emails.append(new_email)
    runner.step(
        lambda_name='users',
        name='profile.change-email (success: inicia el flujo)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body(
                'profile',
                'change-email',
                new_email=new_email,
                password=STRONG_PASSWORD,
            ),
            origin=origin,
            bearer=access,
        ),
        expected=200,
    )

    # El token del magic-link email-change no vuelve (viaja al email NUEVO).
    # Reescribimos su hash a uno conocido para confirmar sin leer el email.
    token = secrets.token_urlsafe(32)
    seeded = env.seed_magic_link(
        user_id=user_id,
        kind='email-change',
        plaintext=token,
    )
    runner.step(
        lambda_name='users',
        name='profile.confirm-email-change (success: aplica el cambio)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('profile', 'confirm-email-change', token=token),
            origin=origin,
        ),
        expected=200,
        note='link sembrado' if seeded else 'seed FALLO',
    )

    # Verifica en Neon que el email del user es el nuevo.
    applied = (env.user_email(user_id) or '').lower() == new_email.lower()
    runner.step(
        lambda_name='users',
        name='profile.change-email (verifica: email actualizado en DB)',
        method='POST',
        call=lambda: Synthetic(200 if applied else 0),
        expected=200,
        note='email = new_email en Neon' if applied else 'email NO cambio',
    )


def _run_delete_account(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """delete-account con el sentinel -> verifica soft-delete en Neon."""
    email = synthetic_email(run_id, 'del')
    created_emails.append(email)
    user_id = register_active_with_password(http, env, origin, email, bypass)
    access = _login_password_direct(http, origin, email, bypass)
    if not (user_id and access):
        print('  [SKIP] delete-account: setup del user fallo')
        return

    runner.step(
        lambda_name='users',
        name='profile.delete-account (success: sentinel valido)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body(
                'profile',
                'delete-account',
                confirm='DELETE-MY-ACCOUNT',
            ),
            origin=origin,
            bearer=access,
        ),
        expected=[200, 204],
    )

    deleted = env.user_status(user_id) in ('deleted', None)
    runner.step(
        lambda_name='users',
        name='profile.delete-account (verifica: soft-delete en DB)',
        method='POST',
        call=lambda: Synthetic(200 if deleted else 0),
        expected=200,
        note='deleted_at seteado en Neon' if deleted else 'user NO borrado',
    )


def _run_users_errors(runner: Runner, http: HttpClient, origin: str) -> None:
    """Casos de error de users (sin estado valido)."""
    runner.case(
        lambda_name='users',
        name='profile.get (error: sin JWT)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('profile', 'get'),
            origin=origin,
        ),
        expected=401,
    )
    runner.case(
        lambda_name='users',
        name='status.get (error: JWT falso)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('status', 'get'),
            origin=origin,
            bearer=FAKE_JWT,
        ),
        expected=401,
    )
    runner.case(
        lambda_name='users',
        name='status.revoke-session (error: JWT falso)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('status', 'revoke-session', session_id=_FAKE_UUID),
            origin=origin,
            bearer=FAKE_JWT,
        ),
        expected=401,
    )


# =========================================================================
# flow_admin: admin.* del Lambda users (promote/restore whitelist SSM)
# =========================================================================


def run_admin(
    runner: Runner,
    http: HttpClient,
    env: Environment,
    origin: str,
    run_id: str,
    bypass: str,
    created_emails: list[str],
) -> None:
    """Promueve un admin sintetico, corre admin.*, restaura la whitelist."""
    admin_email = synthetic_email(run_id, 'admin')
    created_emails.append(admin_email)
    admin_id = register_active_with_password(
        http,
        env,
        origin,
        admin_email,
        bypass,
    )
    admin_access = _login_admin(http, origin, admin_email, bypass)

    target_email = synthetic_email(run_id, 'target')
    created_emails.append(target_email)
    target_id = register_active_with_password(
        http,
        env,
        origin,
        target_email,
        bypass,
    )
    if not (admin_id and admin_access and target_id):
        print('  [SKIP] admin: setup de users fallo')
        return

    original = env.read_admin_emails()
    promoted = f'{original},{admin_email}' if original else admin_email
    try:
        env.write_admin_emails(promoted)
        # SSM put_parameter es eventualmente consistente: confirmar que un
        # get_parameter ya devuelve el email promovido ANTES del bust, para
        # que el cold start del Lambda (que lee SSM) no cachee el valor viejo.
        # (Solo este wait; NO el sondeo de readiness post-bust, que crea
        # contenedores nuevos durante la ventana del cold y da 404 perpetuo.)
        _wait_ssm_promoted(env, admin_email)
        print('  [INFO] admin: whitelist promovida + cold restart users...')
        # Converge el cache de la whitelist a la version promovida ANTES de los
        # casos. El Lambda `users` cachea la whitelist module-level (TTL 300s);
        # bajo carga hay varios contenedores calientes y un solo bust no drena
        # todos de forma fiable (medido: 7/7 o 0/7 segun cuantos contenedores
        # haya). Patron determinista: sondear list-users -> si 404, re-bustear
        # (recicla contenedores) -> repetir hasta `stable_hits` 200 seguidos.
        _converge_admin_recognized(http, env, origin, admin_access)
        _run_admin_cases(
            runner,
            http,
            origin,
            admin_access,
            target_id,
            target_email,
        )
    finally:
        env.write_admin_emails(original)
        env.clear_users_cache_buster()
        print('  [INFO] admin: whitelist SSM restaurada + cache buster off')


def _wait_ssm_promoted(
    env: Environment,
    admin_email: str,
    *,
    attempts: int = 10,
    delay: float = 2.0,
) -> None:
    """Bloquea hasta que la whitelist SSM ya devuelva el email promovido.

    `put_parameter` (SecureString) es eventualmente consistente: un
    `get_parameter` inmediato puede seguir devolviendo el valor viejo unos
    segundos. Si el cold start del Lambda `users` (disparado por el bust) lee
    SSM en esa ventana, cachea el valor VIEJO module-level por su TTL (300s)
    -> el caller queda como no-admin (404). Confirmar aqui que
    `read_admin_emails()` ya incluye el email garantiza que el cold start lea
    la whitelist promovida. Hermetico: compara emails (no imprime el CSV, que
    es SecureString).
    """
    needle = admin_email.strip().lower()
    for attempt in range(1, attempts + 1):
        if needle in env.read_admin_emails().lower():
            return
        if attempt < attempts:
            time.sleep(delay)
    print(
        '  [WARN] admin: SSM no refleja el email promovido tras '
        f'{attempts} lecturas; el cold start podria cachear la whitelist vieja.'
    )


def _converge_admin_recognized(
    http: HttpClient,
    env: Environment,
    origin: str,
    access: str,
    *,
    bust_rounds: int = 6,
    stable_hits: int = 10,
    confirm_rounds: int = 40,
    delay: float = 2.0,
) -> None:
    """Bloquea hasta que list-users de 200 de forma ESTABLE antes de los casos.

    El Lambda `users` cachea la whitelist module-level (TTL 300s) y AWS reparte
    los requests entre VARIOS contenedores: tras promover, unos ya tienen la
    whitelist nueva y otros la vieja hasta que su cache expira. No se puede
    forzar 1 contenedor (la cuenta no permite reserved-concurrency=1).

    Dos fases (el orden es CRITICO):
    1. BUST: re-bustear hasta lograr el primer 200, reciclando los contenedores
       viejos. `update_function_configuration` crea contenedores nuevos FRIOS.
    2. CONFIRM (sin bustear): exigir `stable_hits` 200 consecutivos. Un 404 aqui
       NO re-bustea (eso crearia mas frios justo antes de los casos -> el primer
       caso pegaria a uno sin la whitelist -> 404); solo espera y resetea el
       contador, dando tiempo a que los frios del ultimo bust lean SSM. La
       ULTIMA operacion del warm-up NUNCA es un bust, asi el primer caso real ya
       encuentra todos los contenedores convergidos. Hermetico.
    """
    # Fase 1: bustear hasta el primer 200 (reciclar contenedores viejos).
    for _ in range(bust_rounds):
        resp = http.post(
            '/users',
            body=make_body('admin', 'list-users', page_size=1),
            origin=origin,
            bearer=access,
        )
        if resp.status == 200:
            break
        env.bust_users_cache()
        time.sleep(delay)

    # Fase 2: confirmar estabilidad SIN bustear (no crear frios nuevos).
    hits = 0
    for _ in range(confirm_rounds):
        resp = http.post(
            '/users',
            body=make_body('admin', 'list-users', page_size=1),
            origin=origin,
            bearer=access,
        )
        if resp.status == 200:
            hits += 1
            if hits >= stable_hits:
                return
        else:
            hits = 0
        time.sleep(delay)


def _admin_call(
    call: Callable[[], Response],
    *,
    expected: object,
    retries: int = 24,
    delay: float = 4.0,
) -> Response:
    """Envuelve una llamada admin con retry (solo espera) hasta el esperado.

    El Lambda `users` cachea la whitelist module-level (TTL 300s) y AWS reparte
    los requests entre VARIOS contenedores: tras promover un admin, unos ya
    tienen la whitelist nueva y otros la vieja (404) hasta que su cache expira.
    No es posible forzar 1 contenedor (la cuenta no permite
    reserved-concurrency=1). Aqui SOLO se reintenta esperando: cada reintento
    puede pegar a un contenedor distinto y eventualmente a uno fresco. NO se
    re-bustea durante los casos: cada `update_function_configuration` crea
    contenedores nuevos FRIOS que arrancan sin la whitelist cacheada -> mas
    404 (medido). El unico bust vive en el warm-up (`_converge_admin_recognized`)
    ANTES de los casos. Devuelve la primera Response que matchea, o la ultima.
    Hermetico: no imprime tokens.
    """
    last: Response | None = None
    for attempt in range(1, retries + 1):
        last = call()
        if matches_status(last.status, expected):
            return last
        if attempt < retries:
            time.sleep(delay)
    return last  # type: ignore[return-value]


def _run_admin_cases(
    runner: Runner,
    http: HttpClient,
    origin: str,
    access: str,
    target_id: str,
    target_email: str,
) -> None:
    """Los 7 admin.* con el caller ya promovido a admin.

    Cada caso usa `_admin_call` (retry hasta el status esperado) porque el
    reconocimiento de admin es eventualmente consistente entre contenedores
    del Lambda `users` (ver `_admin_call`). Asi el sample que registra el
    Runner ya viene estabilizado, sin falsos 404 por load balancing.
    """
    runner.case(
        lambda_name='users',
        name='admin.list-users (success: admin promovido)',
        method='POST',
        call=lambda: _admin_call(
            lambda: http.post(
                '/users',
                body=make_body('admin', 'list-users', page_size=5),
                origin=origin,
                bearer=access,
            ),
            expected=200,
        ),
        expected=200,
    )
    runner.case(
        lambda_name='users',
        name='admin.get-user (success: target)',
        method='POST',
        call=lambda: _admin_call(
            lambda: http.post(
                '/users',
                body=make_body('admin', 'get-user', user_id=target_id),
                origin=origin,
                bearer=access,
            ),
            expected=200,
        ),
        expected=200,
    )
    runner.step(
        lambda_name='users',
        name='admin.disable-user (success: 204)',
        method='POST',
        call=lambda: _admin_call(
            lambda: http.post(
                '/users',
                body=make_body(
                    'admin', 'disable-user', user_id=target_id, reason='api-e2e'
                ),
                origin=origin,
                bearer=access,
            ),
            expected=[200, 204],
        ),
        expected=[200, 204],
    )
    runner.step(
        lambda_name='users',
        name='admin.enable-user (success: 204)',
        method='POST',
        call=lambda: _admin_call(
            lambda: http.post(
                '/users',
                body=make_body('admin', 'enable-user', user_id=target_id),
                origin=origin,
                bearer=access,
            ),
            expected=[200, 204],
        ),
        expected=[200, 204],
    )
    runner.step(
        lambda_name='users',
        name='admin.force-logout (success: 204)',
        method='POST',
        call=lambda: _admin_call(
            lambda: http.post(
                '/users',
                body=make_body(
                    'admin', 'force-logout', user_id=target_id, reason='api-e2e'
                ),
                origin=origin,
                bearer=access,
            ),
            expected=[200, 204],
        ),
        expected=[200, 204],
    )
    runner.case(
        lambda_name='users',
        name='admin.list-admin-actions (success)',
        method='POST',
        call=lambda: _admin_call(
            lambda: http.post(
                '/users',
                body=make_body('admin', 'list-admin-actions', page_size=10),
                origin=origin,
                bearer=access,
            ),
            expected=200,
        ),
        expected=200,
    )
    # delete-user: hard delete del target (sentinel = HARD-DELETE-USER-<id>).
    runner.step(
        lambda_name='users',
        name='admin.delete-user (success: hard delete del target)',
        method='POST',
        call=lambda: _admin_call(
            lambda: http.post(
                '/users',
                body=make_body(
                    'admin',
                    'delete-user',
                    user_id=target_id,
                    confirm=f'HARD-DELETE-USER-{target_id}',
                ),
                origin=origin,
                bearer=access,
            ),
            expected=[200, 204],
        ),
        expected=[200, 204],
    )


def _login_admin(
    http: HttpClient,
    origin: str,
    email: str,
    bypass: str,
) -> str | None:
    """login.start con password -> access token directo (sin MFA)."""
    r = http.post(
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
    )
    return field(r.body, 'access_token')
