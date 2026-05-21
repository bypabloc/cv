"""
example_service.create_resource: si la invocacion al Lambda downstream
devuelve None (fallo), el service lanza ServiceError con code 5003.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from unittest.mock import patch

import pytest

from services import example_service
from services.example_service import ServiceError
from services.example_service import create_resource


def test_create_service_raises_on_downstream_failure():
    """
    Given un downstream que devuelve None,
    When se invoca create_resource,
    Then se lanza ServiceError con code 5003 y error_code LAMBDA_INVOKE_ERROR.
    """
    with patch.object(example_service, 'invoker_dispatch', return_value=None):
        with pytest.raises(ServiceError) as exc_info:
            create_resource(resource_id='R-1', amount=100, arn='arn:dummy')

    assert exc_info.value.code == 5003
    assert exc_info.value.error_code == 'LAMBDA_INVOKE_ERROR'
