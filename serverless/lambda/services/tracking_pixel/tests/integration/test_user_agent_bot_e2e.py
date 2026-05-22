"""E2E — User-Agent de bot enriquece el item como device_type=bot.

Given un evento API Gateway con un User-Agent de Googlebot,
When lambda_handler lo procesa end-to-end,
Then el item persistido contiene device_type=bot, browser/os=unknown y
  sin columna browser_version (el regex no reconoce el crawler como
  navegador ni SO; el ORM omite el browser_version vacio).
"""

import pytest

from tests.integration._fixtures._builders import (
    BOT_UA,
    api_gw_event,
    lambda_context,
    scan_tracking,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_user_agent_bot_e2e():
    import handler

    # Arrange
    event = api_gw_event(body=valid_body(), user_agent=BOT_UA)

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 204
    items = scan_tracking()
    assert len(items) == 1
    item = items[0]
    assert item['device_type'] == 'bot'
    assert item['browser'] == 'unknown'
    assert item['os'] == 'unknown'
    # browser_version es '' (sin version): el ORM omite los empty strings.
    assert 'browser_version' not in item
