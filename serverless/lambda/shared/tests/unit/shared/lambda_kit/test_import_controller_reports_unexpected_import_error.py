"""shared.lambda_kit.import_controller.import_controller.

Given que importar el modulo controller lanza un error inesperado
     (no ImportError),
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code IMPORT_ERROR.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from shared.lambda_kit.error_codes import ErrorCode
from shared.lambda_kit.import_controller import import_controller

pytestmark = pytest.mark.unit


def test_import_controller_reports_unexpected_import_error() -> None:
    # Arrange
    operations = {'demo': {'controller': 'demo', 'arn_key': ''}}

    def boom(_path: str) -> None:
        raise RuntimeError('unexpected')

    # Act
    with patch(
        'shared.lambda_kit.import_controller.import_module',
        side_effect=boom,
    ):
        result = import_controller('demo', 'create', operations)

    # Assert
    assert result['is_valid'] is False
    assert result['data']['error_code'] == 'IMPORT_ERROR'
    assert result['code'] == ErrorCode.UNEXPECTED_ERROR.value
