"""shared.lambda_kit.base_controller.BaseController.run.

Given un controller con event_model y un evento invalido,
When se ejecuta run,
Then devuelve el resultado del validate sin llegar a execute.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel
from shared.lambda_kit.error_codes import ErrorCode

pytestmark = pytest.mark.unit


class _Payload(BaseModel):
    name: str


def test_base_controller_run_stops_on_validate_failure(
    make_controller,
) -> None:
    # Arrange: el evento no trae 'name' requerido
    controller = make_controller(event_model=_Payload)(event={})

    # Act
    result = controller.run()

    # Assert
    assert result['is_valid'] is False
    assert result['code'] == ErrorCode.VALIDATION_ERROR.value
