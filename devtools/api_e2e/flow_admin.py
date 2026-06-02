"""Flujo admin del Lambda users (operation `admin`, 7 actions).

El scope admin.* exige que el email del caller este en la whitelist SSM
`/portfolio/{stage}/admin-emails`. El harness:

1. Registra un user admin sintetico (active + password) -> access JWT.
2. Promueve su email en la whitelist SSM (append al valor actual) y fuerza
   un cold start del Lambda users (la whitelist se cachea por contenedor
   con TTL 300s -> sin reciclar, el contenedor caliente daria 404).
3. Corre los 7 admin.* contra un user TARGET sintetico aparte (disable ->
   enable -> force-logout -> delete) + list-users + get-user +
   list-admin-actions.
4. SIEMPRE restaura la whitelist SSM al valor original y borra el cache
   buster (finally), aunque algo falle.

NO toca el user `pacg1991@gmail.com` real de la whitelist: solo APPENDea
el email sintetico y restaura el CSV exacto al final.
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
    admin_access = _login(http, origin, admin_email, bypass)

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
        print('  [INFO] admin: whitelist promovida + cold restart users...')
        env.bust_users_cache()
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


def _run_admin_cases(
    runner: Runner,
    http: HttpClient,
    origin: str,
    access: str,
    target_id: str,
    target_email: str,
) -> None:
    """Los 7 admin.* con el caller ya promovido a admin."""
    runner.case(
        lambda_name='users',
        name='admin.list-users (success: admin promovido)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('admin', 'list-users', page_size=5),
            origin=origin,
            bearer=access,
        ),
        expected=200,
    )
    runner.case(
        lambda_name='users',
        name='admin.get-user (success: target)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('admin', 'get-user', user_id=target_id),
            origin=origin,
            bearer=access,
        ),
        expected=200,
    )
    runner.step(
        lambda_name='users',
        name='admin.disable-user (success: 204)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body(
                'admin', 'disable-user', user_id=target_id, reason='api-e2e'
            ),
            origin=origin,
            bearer=access,
        ),
        expected=[200, 204],
    )
    runner.step(
        lambda_name='users',
        name='admin.enable-user (success: 204)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('admin', 'enable-user', user_id=target_id),
            origin=origin,
            bearer=access,
        ),
        expected=[200, 204],
    )
    runner.step(
        lambda_name='users',
        name='admin.force-logout (success: 204)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body(
                'admin', 'force-logout', user_id=target_id, reason='api-e2e'
            ),
            origin=origin,
            bearer=access,
        ),
        expected=[200, 204],
    )
    runner.case(
        lambda_name='users',
        name='admin.list-admin-actions (success)',
        method='POST',
        call=lambda: http.post(
            '/users',
            body=make_body('admin', 'list-admin-actions', page_size=10),
            origin=origin,
            bearer=access,
        ),
        expected=200,
    )
    # delete-user: hard delete del target (sentinel = HARD-DELETE-USER-<id>).
    runner.step(
        lambda_name='users',
        name='admin.delete-user (success: hard delete del target)',
        method='POST',
        call=lambda: http.post(
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
    )


def _login(
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
