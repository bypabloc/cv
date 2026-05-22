"""Util base_controller.BaseController.run — guard validated_data None.

Given un controller con event_model cuyo validate devuelve is_valid True
     pero deja validated_data en None,
When se ejecuta el ciclo run(),
Then el guard detecta el estado invalido y devuelve {is_valid: False}
     con error VALIDATION_STATE_ERROR.
"""

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_base_controller_guards_validated_data_none():
    from models.db import CurrentModel
    from utils.base_controller import BaseController

    class _GhostValidate(BaseController):
        event_model = CurrentModel

        def validate(self) -> dict:
            # is_valid True pero deja validated_data en None a proposito.
            return {'is_valid': True, 'data': {}, 'code': 0}

        def execute(self) -> dict:
            raise AssertionError('execute no debe ejecutarse')

    # Arrange
    controller = _GhostValidate(event={})

    # Act
    result = controller.run()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error': 'VALIDATION_STATE_ERROR',
            'message': 'validated_data not set after validation',
        },
        'code': ErrorCode.UNEXPECTED_ERROR.value,
    }
