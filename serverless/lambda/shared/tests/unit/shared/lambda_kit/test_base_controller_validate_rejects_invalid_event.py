"""shared.lambda_kit.base_controller.BaseController.validate.

Given un controller con event_model y un evento que no cumple el modelo,
When se ejecuta validate,
Then devuelve {is_valid: False} con error INVALID_EVENT_DATA.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel
from shared.lambda_kit.error_codes import ErrorCode

pytestmark = pytest.mark.unit


class _Payload(BaseModel):
    name: str


def test_base_controller_validate_rejects_invalid_event(
    make_controller,
) -> None:
    # Arrange: el evento no trae 'name' requerido
    controller = make_controller(event_model=_Payload)(event={})

    # Act
    result = controller.validate()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error': 'INVALID_EVENT_DATA',
            'message': 'Event validation failed',
        },
        'code': ErrorCode.VALIDATION_ERROR.value,
    }
