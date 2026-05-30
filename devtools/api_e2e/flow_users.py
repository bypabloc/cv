"""Flujo users: profile + status + admin.

Reutiliza el access_token del flujo auth (un user `active` recien creado).
profile.get / profile.update / status.get / status.list-sessions son
operaciones del propio user. admin.* se prueba en su variante de error:
un user NO-admin recibe 404 NOT_FOUND (anti-enumeration). Casos sin JWT
valido -> 401.
"""

from __future__ import annotations

from config import admin_origin
from runner import Runner
from runner import make_body
from support import HttpClient


_FAKE_JWT = 'FAKE-TOKEN-API-E2E-NOT-A-REAL-JWT-XXXXXXXXXXXXXXXXXXXXXXXX'
_FAKE_UUID = '00000000-0000-7000-8000-000000000000'


def run_users(
    runner: Runner,
    http: HttpClient,
    env_name: str,
    access_token: str | None,
) -> None:
    """Corre los casos de users (success si hay access_token + errores)."""
    origin = admin_origin(env_name)

    if access_token:
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
            name='admin.list-users (error: no-admin -> 404)',
            method='POST',
            call=lambda: http.post(
                '/users',
                body=make_body('admin', 'list-users'),
                origin=origin,
                bearer=access_token,
            ),
            expected=404,
        )
    else:
        print('  [SKIP] users success: no hay access_token del flujo auth')

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
