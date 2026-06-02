"""Flujos MFA del Lambda auth: TOTP, email-code, recovery codes.

Ejercita el dominio MFA completo del dashboard contra dev/stage:

- TOTP: setup-totp (devuelve secret_b32) -> genera code con stdlib ->
  confirm-totp -> login con MFA (login.start password -> temp step=2 ->
  login.verify-totp -> tokens). Errores: confirm code malo, verify code malo.
- email-code: agrega email-code como 2do metodo, mfa.list muestra ambos,
  set-preferred, disable (mantiene >=1 metodo: el guard MUST_KEEP_ONE).
- recovery codes: generate (10 codes) -> login con MFA -> recovery-codes
  -consume con un code (tokens). Error: consume code ya usado.

Cada sub-flujo crea su propio user active CON password (el factor fuerte
que MFA exige). El TOTP code se genera localmente con `api_e2e.totp`
(RFC 6238 stdlib, equivalente a pyotp) desde el b32 que devuelve
setup-totp — NO se necesita un authenticator real.
"""

from __future__ import annotations

from api_e2e._auth_support import STRONG_PASSWORD
from api_e2e._auth_support import field
from api_e2e._auth_support import register_active_with_password
from api_e2e.config import synthetic_email
from api_e2e.environment import Environment
from api_e2e.runner import Runner
from api_e2e.runner import make_body
from api_e2e.support import HttpClient
from api_e2e.totp import totp_now


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
