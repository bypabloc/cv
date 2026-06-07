"""E2E del Lambda contact_form (POST /contact) contra el desplegado.

Porta `devtools/api_e2e/flow_readonly.run_contact`: create exitoso (202
via bypass Turnstile) + 2 errores de payload (sin message, email
invalido). El contact creado se limpia en el teardown del conftest.
"""

from __future__ import annotations

import pytest
from shared.http import HttpClient
from shared.reporter import Reporter
from shared.runner import Runner

from . import _flows


@pytest.mark.api
def test_contact_form_create_and_errors(
    runner: Runner,
    reporter: Reporter,
    http: HttpClient,
    env: str,
    run_id: str,
    bypass: str | None,
    created_emails: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given el Lambda contact_form desplegado,
    When se crea un contacto valido (via bypass) y se envian 2 payloads
    invalidos,
    Then el create da 2xx (202) y los invalidos dan 4xx. [AC-1, AC-10,
    AC-11]
    """
    # Arrange
    if lambda_filter is not None and lambda_filter != 'contact_form':
        pytest.skip(f'--lambda={lambda_filter}: contact_form omitido')
    since = len(reporter.results)

    # Act
    _flows.run_contact(runner, http, env, run_id, bypass, created_emails)

    # Assert
    _flows.assert_cases_passed(reporter, since=since)
