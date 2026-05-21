"""Service parse_user_agent — enrichment de un UA de Chrome/Linux.

Given un User-Agent de Chrome sobre Linux,
When se invoca parse_user_agent,
Then devuelve browser=Chrome, os=Linux y device_type=desktop.
"""

import pytest

from tests.unit._helpers import CHROME_UA

pytestmark = pytest.mark.unit


def test_parse_user_agent_extracts_chrome_linux(tracking_aws: None):
    from services.tracking_service import parse_user_agent

    # Act
    info = parse_user_agent(CHROME_UA)

    # Assert
    assert info['browser'] == 'Chrome'
    assert info['browser_version'] == '118'
    assert info['os'] == 'Linux'
    assert info['device_type'] == 'desktop'
