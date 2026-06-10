"""shared.lambda_kit.base_controller.BaseController.run (fase Authorize).

Given un controller con required_permission='admin' y un checker que
     acepta devolviendo el subject autenticado,
When se ejecuta run,
Then el checker recibe (permission, _meta crudo, action=<ClassName>),
     el subject queda en controller.permission_subject y el ciclo
     completa con el resultado de execute.
"""

from __future__ import annotations

from typing import Any

import pytest
from shared.lambda_kit.base_controller import set_permission_checker

pytestmark = pytest.mark.unit


def test_base_controller_authorize_sets_permission_subject(
    make_controller,
) -> None:
    # Arrange
    calls: list[tuple[str, dict[str, Any], str]] = []
    subject = object()

    def _checker(permission: str, meta: dict, *, action: str) -> object:
        calls.append((permission, meta, action))
        return subject

    set_permission_checker(_checker)
    expected = {'is_valid': True, 'data': {'ok': 1}, 'code': 0}
    meta = {'ip': '203.0.113.7', 'authorization': 'Bearer x'}
    controller_cls = make_controller(
        execute_result=expected,
        required_permission='admin',
    )
    controller = controller_cls(event={'_meta': meta, 'campo': 'valor'})

    # Act
    result = controller.run()

    # Assert
    assert result == expected
    assert controller.permission_subject is subject
    assert calls == [('admin', meta, controller_cls.__name__)]
