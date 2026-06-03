"""E2E MFA del Lambda auth — TOTP, email-code, recovery codes.

Porta `devtools/api_e2e/flow_auth_mfa.run_mfa_flows`: TOTP (setup ->
confirm -> login 2FA con verify-totp), email-code (setup + list +
set-preferred + disable), recovery codes (generate -> consume + reuso).
El TOTP code se genera localmente con `shared.totp` (RFC 6238 stdlib).

Requiere bypass (registra users active con password): si falta, el flujo
no produce casos y el test pasa vacuo (igual que api_e2e omite el exito
sin bypass). Los emails sinteticos se limpian en el teardown del conftest.
"""

from __future__ import annotations

import pytest
from shared.environment import Environment
from shared.http import HttpClient
from shared.reporter import Reporter
from shared.runner import Runner

from . import _flows


@pytest.mark.api
def test_auth_mfa_totp_email_code_recovery(
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
    Given un user active con password y el Lambda auth desplegado,
    When se ejercitan los 3 sub-flujos MFA (TOTP, email-code, recovery),
    Then todos los casos pasan (setup/confirm/login-2FA + errores de code).
    [AC-1, AC-10, AC-11]
    """
    # Arrange
    if lambda_filter is not None and lambda_filter != 'auth':
        pytest.skip(f'--lambda={lambda_filter}: auth (mfa) omitido')
    if not bypass:
        pytest.skip('bypass Turnstile no disponible: MFA exige user active')
    since = len(reporter.results)
    origin = _flows.admin_origin(env)

    # Act
    _flows.run_mfa_flows(
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
