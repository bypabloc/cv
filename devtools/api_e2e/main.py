"""Entry point de api_e2e: orquesta los flujos E2E reales.

Resuelve secretos del entorno (SSM, hermetico), corre los flujos de cada
Lambda (cv, contact_form, tracking_pixel, auth, users) contra el API
Gateway real, limpia los datos sinteticos creados en Neon y reporta
pass/fail + tiempos de respuesta promedio.

Exit codes: 0 (todos PASS), 1 (algun caso FAIL), 2 (error de setup).
"""

from __future__ import annotations

import secrets as _secrets
from typing import Any

from api_e2e.config import api_base
from api_e2e.config import turnstile_bypass_supported
from api_e2e.environment import Environment
from api_e2e.flow_auth import run_auth
from api_e2e.flow_readonly import run_contact
from api_e2e.flow_readonly import run_cv
from api_e2e.flow_readonly import run_tracking
from api_e2e.flow_users import run_users
from api_e2e.reporter import Reporter
from api_e2e.runner import Runner
from api_e2e.support import HttpClient


def main(flags: dict[str, Any]) -> int:
    """Corre el harness api_e2e segun las flags."""
    env_name = flags['env']
    only = flags.get('lambda')
    samples = flags.get('samples', 5)
    keep_data = flags.get('keep_data', False)
    aws_profile = flags.get('aws_profile')

    print('=' * 80)
    print(
        f'api_e2e — tests reales contra {env_name.upper()} '
        f'({api_base(env_name)})'
    )
    print('=' * 80)

    try:
        env = Environment(env_name, aws_profile=aws_profile)
        bypass = (
            env.bypass_secret()
            if turnstile_bypass_supported(env_name)
            else None
        )
    except Exception as exc:  # noqa: BLE001 -- setup
        print(f'[ERROR] setup del entorno: {type(exc).__name__}: {exc}')
        return 2

    if bypass is None and turnstile_bypass_supported(env_name):
        print(
            '[WARN] bypass de Turnstile no disponible: los flujos de '
            'exito de contact/auth se omiten (solo errores).'
        )
    elif not turnstile_bypass_supported(env_name):
        print(
            f'[INFO] {env_name} no soporta bypass de Turnstile: '
            'flujos con Turnstile omitidos (solo errores).'
        )

    run_id = _secrets.token_hex(2)
    http = HttpClient(base_url=api_base(env_name))
    reporter = Reporter()
    runner = Runner(reporter, samples=samples)

    created_emails: list[str] = []
    created_sessions: list[str] = []

    def _want(name: str) -> bool:
        return only is None or only == name

    try:
        if _want('cv'):
            print('\n--- cv ---')
            run_cv(runner, http, env_name)
        if _want('contact_form'):
            print('\n--- contact_form ---')
            run_contact(
                runner,
                http,
                env_name,
                run_id,
                bypass,
                created_emails,
            )
        if _want('tracking_pixel'):
            print('\n--- tracking_pixel ---')
            run_tracking(runner, http, env_name, run_id, created_sessions)

        access_token = None
        if _want('auth') or _want('users'):
            print('\n--- auth ---')
            access_token = run_auth(
                runner,
                http,
                env,
                env_name,
                run_id,
                bypass,
                created_emails,
            )
        if _want('users'):
            print('\n--- users ---')
            run_users(runner, http, env_name, access_token)
    finally:
        http.close()
        if not keep_data:
            _cleanup(env, created_emails, created_sessions)
        else:
            print('\n[INFO] --keep-data: datos sinteticos NO eliminados.')

    reporter.print_timing_summary()
    reporter.print_final()
    return 0 if reporter.all_passed() else 1


def _cleanup(
    env: Environment,
    emails: list[str],
    sessions: list[str],
) -> None:
    """Borra los datos sinteticos creados por la corrida (best-effort)."""
    print('\n--- cleanup (datos sinteticos) ---')
    try:
        users = env.cleanup_users(emails)
        contacts = env.cleanup_contacts(emails)
        tracking = env.cleanup_tracking(sessions)
        print(
            f'  borrados: users={users} contacts={contacts} tracking={tracking}'
        )
    except Exception as exc:  # noqa: BLE001 -- best-effort
        print(f'  [WARN] cleanup parcial: {type(exc).__name__}: {exc}')
