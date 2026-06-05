"""E2E del Lambda auth (POST/GET /auth) — register/login/verify/session.

Porta `devtools/api_e2e/flow_auth.run_auth`: el flujo de registro->sesion
completo (login.start (alta) -> verify-code -> refresh -> login.start ->
set-password -> logout), el magic-link GET (302) + POST (JSON), el login
con password (directo + 2-step) y los casos de error (email inexistente,
tokens falsos, mfa/webauthn sin JWT). Los flujos MFA viven en
`test_auth_mfa.py` (mismo Lambda, archivo por escenario).

Deja el access_token VIVO (access2) en `auth_token_box` para que
`test_users` lo reutilice (cadena auth -> users de api_e2e). Los emails
sinteticos se limpian en el teardown del conftest.
"""

from __future__ import annotations

import pytest
from shared.environment import Environment
from shared.http import HttpClient
from shared.reporter import Reporter
from shared.runner import Runner

from . import _flows


@pytest.mark.api
def test_auth_register_login_verify_session(
    runner: Runner,
    reporter: Reporter,
    http: HttpClient,
    environment: Environment,
    env: str,
    run_id: str,
    bypass: str | None,
    created_emails: list[str],
    auth_token_box: dict[str, str | None],
    lambda_filter: str | None,
) -> None:
    """
    Given el Lambda auth desplegado y el bypass de Turnstile,
    When se ejercita register/login/verify/session (exito + errores),
    Then todos los casos pasan y queda un access_token vivo para users.
    [AC-1, AC-10, AC-11]
    """
    # Arrange
    if lambda_filter is not None and lambda_filter not in ('auth', 'users'):
        pytest.skip(f'--lambda={lambda_filter}: auth omitido')
    since = len(reporter.results)

    # Act
    access_token = _flows.run_auth(
        runner,
        http,
        environment,
        env,
        run_id,
        bypass,
        created_emails,
    )
    auth_token_box['access_token'] = access_token

    # Assert
    _flows.assert_cases_passed(reporter, since=since)
