"""shared.lambda_kit.base_controller.BaseController.validate.

Given un controller cuyo event_model.model_validate lanza un error que
     NO es ValidationError,
When se ejecuta validate,
Then devuelve {is_valid: False} con error UNEXPECTED_VALIDATION_ERROR.
"""

from __future__ import annotations

import pytest
from shared.lambda_kit.error_codes import ErrorCode

pytestmark = pytest.mark.unit


class _ExplodingModel:
    """Modelo falso cuyo model_validate lanza un RuntimeError."""

    @staticmethod
    def model_validate(_event: object) -> object:
        raise RuntimeError('boom')


def test_base_controller_validate_maps_unexpected_error(
    make_controller,
) -> None:
    # Arrange
    controller = make_controller(event_model=_ExplodingModel)(event={})

    # Act
    result = controller.validate()

    # Assert
    assert result['is_valid'] is False
    assert result['data']['error'] == 'UNEXPECTED_VALIDATION_ERROR'
    assert result['code'] == ErrorCode.UNEXPECTED_ERROR.value
