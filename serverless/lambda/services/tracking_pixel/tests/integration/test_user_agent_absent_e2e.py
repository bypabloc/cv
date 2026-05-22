"""E2E — request sin header User-Agent enriquece el item como unknown.

Given un evento API Gateway sin header User-Agent,
When lambda_handler lo procesa end-to-end,
Then devuelve HTTP 204, el item persiste con browser/os/device_type
  =unknown y la columna user_agent se omite (DynamoDB no acepta empty
  strings, el ORM la descarta).
"""

import pytest

from tests.integration._fixtures._builders import (
    api_gw_event,
    lambda_context,
    scan_tracking,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_user_agent_absent_e2e():
    import handler

    # Arrange: user_agent=None omite el header User-Agent del evento.
    event = api_gw_event(body=valid_body(), user_agent=None)

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 204
    items = scan_tracking()
    assert len(items) == 1
    item = items[0]
    assert item['browser'] == 'unknown'
    assert item['os'] == 'unknown'
    assert item['device_type'] == 'unknown'
    # El ORM descarta el user_agent vacio: la columna no existe en el item.
    assert 'user_agent' not in item
