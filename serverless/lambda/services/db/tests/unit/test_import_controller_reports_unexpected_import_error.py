"""Util import_controller.import_controller — error inesperado al importar.

Given import_module que lanza una excepcion que no es ImportError ni
     ModuleNotFoundError,
When se invoca import_controller,
Then devuelve {is_valid: False} con error_code IMPORT_ERROR y code
     UNEXPECTED_ERROR.
"""

from unittest.mock import patch

import pytest
from settings.config import ErrorCode

pytestmark = pytest.mark.unit


def test_import_controller_reports_unexpected_import_error():
    from utils.import_controller import import_controller

    # Arrange
    with patch(
        'utils.import_controller.import_module',
        side_effect=RuntimeError('fallo raro al importar'),
    ):
        # Act
        result = import_controller('db', 'migrate')

    # Assert
    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'IMPORT_ERROR',
            'message': 'Unexpected error importing controller',
        },
        'code': ErrorCode.UNEXPECTED_ERROR.value,
        'class': None,
    }
