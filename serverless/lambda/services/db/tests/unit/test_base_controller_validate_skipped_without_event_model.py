"""Util base_controller.BaseController.validate — sin event_model.

Given un controller que no declara event_model,
When se ejecuta validate,
Then devuelve {is_valid: True} sin intentar validar el evento.
"""

import pytest

pytestmark = pytest.mark.unit


def test_base_controller_validate_skipped_without_event_model():
    from utils.base_controller import BaseController

    class _NoModel(BaseController):
        def execute(self) -> dict:
            return {'is_valid': True, 'data': {}, 'code': 0}

    # Arrange
    controller = _NoModel(event={'anything': 'ignored'})

    # Act
    result = controller.validate()

    # Assert
    assert result == {'is_valid': True, 'data': {}, 'code': 0}
