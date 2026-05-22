"""Util base_controller.BaseController.validate — ValidationError.

Given un controller con event_model y un evento que rompe el schema
     Pydantic (campo extra prohibido),
When se ejecuta el ciclo run(),
Then validate captura el ValidationError y devuelve {is_valid: False}
     con error INVALID_EVENT_DATA y code VALIDATION_ERROR.
"""

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_base_controller_validate_rejects_invalid_event():
    from models.db import MigrateModel
    from utils.base_controller import BaseController

    class _WithModel(BaseController):
        event_model = MigrateModel

        def execute(self) -> dict:
            raise AssertionError('execute no debe ejecutarse')

    # Arrange: MigrateModel tiene extra='forbid'.
    controller = _WithModel(event={'unknown_field': 'x'})

    # Act
    result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error': 'INVALID_EVENT_DATA',
            'message': 'Event validation failed',
        },
        'code': ErrorCode.VALIDATION_ERROR.value,
    }
