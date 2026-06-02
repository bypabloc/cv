"""Flujo users: profile + status + change-email + delete-account + admin.

Reutiliza el access_token del flujo auth (un user `active` recien creado)
para profile.get/update/change-password y status.get/list-sessions.

Encima ejercita el resto del dashboard de cuenta:
- change-email completo (change-email -> seed token -> confirm-email-change
  -> verifica el email actualizado en Neon).
- status.revoke-session success (2 sesiones -> revoca la NO actual).
- profile.delete-account success (user dedicado -> sentinel -> verifica
  soft-delete en Neon).
- admin.* completo (list/get/disable/enable/force-logout/list-actions/
  delete) con un user promovido temporalmente a la whitelist SSM
  (`flow_admin`), restaurada al final.

admin.* sin promote se prueba en su variante de error: un user no-admin
recibe 404 NOT_FOUND (anti-enumeration). Casos sin JWT valido -> 401.
"""

from __future__ import annotations

import secrets

from api_e2e._auth_support import FAKE_JWT
from api_e2e._auth_support import STRONG_PASSWORD
from api_e2e._auth_support import WRONG_PASSWORD
from api_e2e._auth_support import field
from api_e2e._auth_support import register_active_with_password
from api_e2e.config import admin_origin
from api_e2e.config import synthetic_email
from api_e2e.environment import Environment
from api_e2e.flow_admin import run_admin
from api_e2e.runner import Runner
from api_e2e.runner import make_body
from api_e2e.support import HttpClient


_FAKE_JWT = FAKE_JWT
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
        run_admin(runner, http, env, origin, run_id, bypass, created_emails)
        _run_delete_account(
            runner,
            http,
            env,
            origin,
            run_id,
            bypass,
            created_emails,
        )

    _run_errors(runner, http, origin)


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
        call=lambda: _SyntheticUsers(200 if applied else 0),
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
        call=lambda: _SyntheticUsers(200 if deleted else 0),
        expected=200,
        note='deleted_at seteado en Neon' if deleted else 'user NO borrado',
    )


def _run_errors(runner: Runner, http: HttpClient, origin: str) -> None:
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
            bearer=_FAKE_JWT,
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
            bearer=_FAKE_JWT,
        ),
        expected=401,
    )


def _login_password_direct(
    http: HttpClient,
    origin: str,
    email: str,
    bypass: str,
) -> str | None:
    """login.start con password de un user SIN MFA -> access token directo."""
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


class _SyntheticUsers:
    """Response sintetica para asserts derivados (sin llamada HTTP real)."""

    def __init__(self, status: int) -> None:
        self.status = status
        self.body: dict[str, object] = {}
        self.elapsed = 0.0
        self.headers: dict[str, str] = {}

    def header(self, name: str) -> str | None:
        return None
