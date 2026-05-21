"""
handler.lambda_handler: un evento valido de example/check se enruta al
controller Check y devuelve is_valid True con el resultado del service.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from handler import lambda_handler

from tests.unit._helpers import build_event


def test_handler_routes_check_to_controller():
    """
    Given un evento valido example/check,
    When se invoca lambda_handler,
    Then devuelve is_valid True con el status del recurso.
    """
    event = build_event(
        operation='example',
        action='check',
        data={'resource_id': 'R-1'},
    )

    result = lambda_handler(event, {})

    assert result == {
        'is_valid': True,
        'data': {'resource_id': 'R-1', 'status': 'ok'},
    }
