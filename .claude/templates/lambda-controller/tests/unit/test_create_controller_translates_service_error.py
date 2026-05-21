"""
controllers.example.create.Create: cuando el service lanza ServiceError,
el controller lo traduce a la respuesta normalizada {is_valid: False,...}.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from unittest.mock import patch

from controllers.example.create import Create
from services.example_service import ServiceError


def test_create_controller_translates_service_error():
    """
    Given un service que lanza ServiceError,
    When el controller Create ejecuta run(),
    Then devuelve is_valid False con el code y error_code del ServiceError.
    """
    controller = Create(event={'resource_id': 'R-1', 'amount': 100})

    error = ServiceError('boom', code=5003, error_code='LAMBDA_INVOKE_ERROR')
    with patch(
        'controllers.example.create.create_resource',
        side_effect=error,
    ):
        result = controller.run()

    assert result == {
        'is_valid': False,
        'data': {
            'error_code': 'LAMBDA_INVOKE_ERROR',
            'message': 'boom',
        },
        'code': 5003,
    }
