"""shared.lambda_kit.base_controller.BaseController.run.

Given un controller sin event_model ni arn_config_key cuyo execute
     devuelve un resultado de exito,
When se ejecuta run,
Then corre preload -> validate -> execute y devuelve el resultado de
     execute.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_base_controller_run_executes_full_cycle(make_controller) -> None:
    # Arrange
    expected = {'is_valid': True, 'data': {'ok': 1}, 'code': 0}
    controller = make_controller(execute_result=expected)(event={})

    # Act
    result = controller.run()

    # Assert
    assert result == expected
