"""E2E del Lambda cv (read-only, GET) contra el entorno desplegado.

Porta `devtools/api_e2e/flow_readonly.run_cv`: las 10 actions read (2xx)
+ 2 errores (action invalida, sin operation). Sin JWT, sin mutacion.
"""

from __future__ import annotations

import pytest
from shared.http import HttpClient
from shared.reporter import Reporter
from shared.runner import Runner

from . import _flows


@pytest.mark.api
def test_cv_read_actions_and_errors(
    runner: Runner,
    reporter: Reporter,
    http: HttpClient,
    env: str,
    lambda_filter: str | None,
) -> None:
    """
    Given el Lambda cv desplegado en dev/stage,
    When se invocan sus 10 read actions + 2 payloads invalidos,
    Then las 10 reads dan 2xx y los 2 invalidos dan 4xx (el Runner registra
    cada caso con su veredicto y timing). [AC-1, AC-11]
    """
    # Arrange
    if lambda_filter is not None and lambda_filter != 'cv':
        pytest.skip(f'--lambda={lambda_filter}: cv omitido')
    since = len(reporter.results)

    # Act
    _flows.run_cv(runner, http, env)

    # Assert
    _flows.assert_cases_passed(reporter, since=since)
