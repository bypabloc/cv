"""shared.lambda_kit.base_controller.BaseController.validate.

Given un controller sin event_model,
When se ejecuta validate,
Then devuelve {is_valid: True} sin validar nada.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_base_controller_validate_skipped_without_event_model(
    make_controller,
) -> None:
    # Arrange
    controller = make_controller(event_model=None)(event={})

    # Act
    result = controller.validate()

    # Assert
    assert result == {'is_valid': True, 'data': {}, 'code': 0}
