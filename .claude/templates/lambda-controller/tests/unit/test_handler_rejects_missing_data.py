"""
handler.lambda_handler: un evento sin el campo 'data' se rechaza en la
validacion del evento con code 1000.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from handler import lambda_handler


def test_handler_rejects_missing_data():
    """
    Given un evento sin el campo 'data',
    When se invoca lambda_handler,
    Then devuelve is_valid False con code 1000.
    """
    event = {'operation': 'example', 'action': 'check'}

    result = lambda_handler(event, {})

    assert result['is_valid'] is False
    assert result['code'] == 1000
