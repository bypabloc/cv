"""E2E del Lambda tracking_pixel (POST /track) contra el desplegado.

Porta `devtools/api_e2e/flow_readonly.run_tracking`: track exitoso (202)
+ 2 errores de payload (sin event_type_id, viewport invalido). El
session_id sintetico se limpia en el teardown del conftest.
"""

from __future__ import annotations

import pytest
from shared.http import HttpClient
from shared.reporter import Reporter
from shared.runner import Runner

from . import _flows


@pytest.mark.api
def test_tracking_pixel_track_and_errors(
    runner: Runner,
    reporter: Reporter,
    http: HttpClient,
    env: str,
    run_id: str,
    created_sessions: list[str],
    lambda_filter: str | None,
) -> None:
    """
    Given el Lambda tracking_pixel desplegado,
    When se registra un evento valido y 2 payloads invalidos,
    Then el track valido da 2xx (202) y los invalidos dan 4xx. [AC-1,
    AC-10, AC-11]
    """
    # Arrange
    if lambda_filter is not None and lambda_filter != 'tracking_pixel':
        pytest.skip(f'--lambda={lambda_filter}: tracking_pixel omitido')
    since = len(reporter.results)

    # Act
    _flows.run_tracking(runner, http, env, run_id, created_sessions)

    # Assert
    _flows.assert_cases_passed(reporter, since=since)
