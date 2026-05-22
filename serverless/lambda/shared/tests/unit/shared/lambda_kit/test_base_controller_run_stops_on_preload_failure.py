"""shared.lambda_kit.base_controller.BaseController.run.

Given un controller con arn_config_key que no resuelve (preload falla),
When se ejecuta run,
Then devuelve el resultado del preload sin llegar a execute.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from shared.lambda_kit import base_controller as bc
from shared.lambda_kit.error_codes import ErrorCode

pytestmark = pytest.mark.unit


def test_base_controller_run_stops_on_preload_failure(
    make_controller,
) -> None:
    # Arrange
    bc.set_app_config(SimpleNamespace())
    controller = make_controller(arn_config_key='missing_arn')(event={})

    # Act
    result = controller.run()

    # Assert
    assert result['is_valid'] is False
    assert result['code'] == ErrorCode.CONFIGURATION_MISSING.value
