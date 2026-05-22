"""E2E — User-Agent de iPhone enriquece el item como mobile.

Given un evento API Gateway con un User-Agent de Safari sobre iPhone,
When lambda_handler lo procesa end-to-end,
Then el item persistido contiene browser=Safari, os=iOS y
  device_type=mobile derivados del parseo del User-Agent.
"""

import pytest

from tests.integration._fixtures._builders import (
    MOBILE_UA,
    api_gw_event,
    lambda_context,
    scan_tracking,
    valid_body,
)

pytestmark = pytest.mark.integration


def test_user_agent_mobile_e2e():
    import handler

    # Arrange
    event = api_gw_event(body=valid_body(), user_agent=MOBILE_UA)

    # Act
    response = handler.lambda_handler(event, lambda_context())

    # Assert
    assert response['statusCode'] == 204
    items = scan_tracking()
    assert len(items) == 1
    item = items[0]
    assert item['browser'] == 'Safari'
    assert item['browser_version'] == '17'
    assert item['os'] == 'iOS'
    assert item['device_type'] == 'mobile'
