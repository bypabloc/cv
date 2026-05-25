"""shared.lambda_kit.base_controller.BaseController.run.

Given un controller cuyo execute devuelve is_valid=False,
When se ejecuta run,
Then devuelve ese resultado de error (el ciclo llego hasta execute).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_base_controller_run_reports_execute_business_error(
    make_controller,
) -> None:
    # Arrange
    error = {
        'is_valid': False,
        'data': {'error_code': 'BUSINESS'},
        'code': 4000,
    }
    controller = make_controller(execute_result=error)(event={})

    # Act
    result = controller.run()

    # Assert
    assert result == error
