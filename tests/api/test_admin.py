"""E2E admin.* del Lambda users (operation admin, 7 actions).

Porta `devtools/api_e2e/flow_admin.run_admin`: registra un admin
sintetico, lo promueve en la whitelist SSM `/portfolio/{stage}/
admin-emails` (append + cold restart del Lambda users para refrescar el
cache de contenedor), corre los 7 admin.* (list-users, get-user, disable,
enable, force-logout, list-admin-actions, delete-user) contra un user
target aparte y SIEMPRE restaura la whitelist SSM al valor original.

NUNCA toca el admin real de la whitelist (solo APPENDea el sintetico y
restaura el CSV exacto). Requiere bypass (registra users active con
password). Los emails sinteticos se limpian en el teardown del conftest.
"""

from __future__ import annotations

import pytest
from shared.environment import Environment
from shared.http import HttpClient
from shared.reporter import Reporter
from shared.runner import Runner

from . import _flows


@pytest.mark.api
def test_admin_user_management(
    runner: Runner,
    reporter: Reporter,
    http: HttpClient,
    environment: Environment,
    env: str,
    run_id: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given un admin sintetico promovido en la whitelist SSM,
    When corre los 7 admin.* contra un user target (disable/enable/
    force-logout/delete + list/get/list-actions),
    Then todos pasan y la whitelist SSM se restaura al valor original.
    [AC-1, AC-10, AC-11]
    """
    # Arrange
    if lambda_filter is not None and lambda_filter != 'users':
        pytest.skip(f'--lambda={lambda_filter}: admin omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible: admin exige user active')
    since = len(reporter.results)
    origin = _flows.admin_origin(env)

    # Act
    _flows.run_admin(
        runner,
        http,
        environment,
        origin,
        run_id,
        bypass,
        created_emails,
    )

    # Assert
    _flows.assert_cases_passed(reporter, since=since)
