"""Util base_controller.BaseController.validate — error inesperado.

Given un controller cuyo event_model.model_validate lanza una excepcion
     que no es ValidationError,
When se ejecuta validate,
Then devuelve {is_valid: False} con error UNEXPECTED_VALIDATION_ERROR y
     code UNEXPECTED_ERROR.
"""

from unittest.mock import MagicMock

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_base_controller_validate_maps_unexpected_error():
    from utils.base_controller import BaseController

    broken_model = MagicMock()
    broken_model.model_validate.side_effect = RuntimeError('boom')

    class _BrokenModel(BaseController):
        event_model = broken_model

        def execute(self) -> dict:
            raise AssertionError('execute no debe ejecutarse')

    # Arrange
    controller = _BrokenModel(event={})

    # Act
    result = controller.validate()

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error': 'UNEXPECTED_VALIDATION_ERROR',
            'message': 'Error de validacion inesperado: boom',
        },
        'code': ErrorCode.UNEXPECTED_ERROR.value,
    }
