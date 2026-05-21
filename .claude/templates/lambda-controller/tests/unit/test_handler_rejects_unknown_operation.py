"""
handler.lambda_handler: un evento con una operation no registrada en
OPERATIONS se rechaza con code 1001 (operation invalida).

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from handler import lambda_handler

from tests.unit._helpers import build_event


def test_handler_rejects_unknown_operation():
    """
    Given un evento con operation inexistente,
    When se invoca lambda_handler,
    Then devuelve is_valid False con code 1001.
    """
    event = build_event(
        operation='does_not_exist',
        action='check',
        data={'resource_id': 'R-1'},
    )

    result = lambda_handler(event, {})

    assert result['is_valid'] is False
    assert result['code'] == 1001
