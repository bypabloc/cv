"""E2E del Lambda users (POST /users) — profile/status/account.

Porta `devtools/api_e2e/flow_users.run_users`: profile.get/update,
status.get/list-sessions, change-password (error + success),
revoke-session, change-email completo (con verificacion en Neon),
delete-account (con verificacion de soft-delete) y los errores (sin JWT,
JWT falso). El flujo admin.* vive en `test_admin.py` (mismo Lambda,
archivo por escenario).

Reutiliza el access_token VIVO que `test_auth` dejo en `auth_token_box`
(cadena auth -> users de api_e2e). Si auth no corrio o no produjo token,
los casos self-service se omiten (igual que api_e2e). Los emails
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
def test_users_profile_status_account(
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
    Given el access_token vivo del flujo auth y el Lambda users desplegado,
    When se ejercita profile/status/change-password/change-email/
    delete-account (exito + errores),
    Then todos los casos pasan (con verificacion en Neon del email cambiado
    y del soft-delete). [AC-1, AC-10, AC-11]
    """
    # Arrange
    if lambda_filter is not None and lambda_filter != 'users':
        pytest.skip(f'--lambda={lambda_filter}: users omitido')
    access_token = auth_token_box.get('access_token')
    since = len(reporter.results)

    # Act
    _flows.run_users(
        runner,
        http,
        environment,
        env,
        run_id,
        bypass,
        access_token,
        created_emails,
    )

    # Assert
    _flows.assert_cases_passed(reporter, since=since)
