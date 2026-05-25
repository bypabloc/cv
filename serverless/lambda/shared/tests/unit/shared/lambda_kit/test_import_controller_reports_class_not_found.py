"""shared.lambda_kit.import_controller.import_controller.

Given un modulo controller que existe pero NO expone la clase esperada,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code CLASS_NOT_FOUND.
"""

from __future__ import annotations

from types import ModuleType
from unittest.mock import patch

import pytest
from shared.lambda_kit.error_codes import ErrorCode
from shared.lambda_kit.import_controller import import_controller

pytestmark = pytest.mark.unit


def test_import_controller_reports_class_not_found() -> None:
    # Arrange: el modulo existe pero sin la clase Create
    operations = {'demo': {'controller': 'demo', 'arn_key': ''}}
    empty_module = ModuleType('controllers.demo.create')

    # Act
    with patch(
        'shared.lambda_kit.import_controller.import_module',
        return_value=empty_module,
    ):
        result = import_controller('demo', 'create', operations)

    # Assert
    assert result['is_valid'] is False
    assert result['data']['error_code'] == 'CLASS_NOT_FOUND'
    assert result['code'] == ErrorCode.VALIDATION_ERROR.value
