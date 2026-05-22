"""E2E — User-Agent de Chrome/Linux enriquece el item persistido.

Given un evento API Gateway con un User-Agent de Chrome sobre Linux,
When lambda_handler lo procesa end-to-end,
Then el item persistido contiene browser=Chrome, os=Linux y
  device_type=desktop derivados del parseo del User-Agent.
"""

import pytest

from tests.integration._fixtures._builders import (
    CHROME_UA,
    api_gw_event,
    lambda_context,
    scan_tracking,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_user_agent_chrome_linux_e2e():
    import handler

    # Arrange
    event = api_gw_event(body=valid_body(), user_agent=CHROME_UA)

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 204
    items = scan_tracking()
    assert len(items) == 1
    item = items[0]
    assert item['browser'] == 'Chrome'
    assert item['browser_version'] == '118'
    assert item['os'] == 'Linux'
    assert item['device_type'] == 'desktop'
    assert item['user_agent'] == CHROME_UA
