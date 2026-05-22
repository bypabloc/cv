"""shared.lambda_kit.import_controller.import_controller.

Given un modulo cuya clase NO hereda de BaseController,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code INVALID_CONTROLLER.
"""

from __future__ import annotations

from types import ModuleType
from unittest.mock import patch

import pytest
from shared.lambda_kit.error_codes import ErrorCode
from shared.lambda_kit.import_controller import import_controller

pytestmark = pytest.mark.unit


class _NotAController:
    """Clase que NO hereda de BaseController."""


def test_import_controller_rejects_non_base_controller_class() -> None:
    # Arrange
    operations = {'demo': {'controller': 'demo', 'arn_key': ''}}
    module = ModuleType('controllers.demo.create')
    module.Create = _NotAController

    # Act
    with patch(
        'shared.lambda_kit.import_controller.import_module',
        return_value=module,
    ):
        result = import_controller('demo', 'create', operations)

    # Assert
    assert result['is_valid'] is False
    assert result['data']['error_code'] == 'INVALID_CONTROLLER'
    assert result['code'] == ErrorCode.VALIDATION_ERROR.value
