"""shared.lambda_kit.base_controller.BaseController.run (fase Authorize).

Given un controller SIN required_permission (default None) y un checker
     registrado que falla si se invoca,
When se ejecuta run,
Then la fase Authorize es no-op (el checker NUNCA se invoca) y el ciclo
     completa con el resultado de execute.
"""

from __future__ import annotations

from typing import Any

import pytest
from shared.lambda_kit.base_controller import set_permission_checker

pytestmark = pytest.mark.unit


def test_base_controller_authorize_noop_without_permission(
    make_controller,
) -> None:
    # Arrange
    calls: list[Any] = []

    def _checker(permission: str, meta: dict, *, action: str) -> object:
        calls.append((permission, meta, action))
        msg = 'el checker no debe invocarse sin required_permission'
        raise AssertionError(msg)

    set_permission_checker(_checker)
    expected = {'is_valid': True, 'data': {'ok': 1}, 'code': 0}
    controller = make_controller(execute_result=expected)(event={})

    # Act
    result = controller.run()

    # Assert
    assert result == expected
    assert calls == []
    assert controller.permission_subject is None
