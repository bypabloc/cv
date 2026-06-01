"""_parse_device_info — Chrome en Windows desktop.

Given un user-agent de Chrome 120 sobre Windows NT 10.0,
When se llama _parse_device_info con ese user-agent,
Then devuelve {browser: chrome, os: windows, device_type: desktop}.
"""

from services.session_tracking_service import _parse_device_info


def test_parse_device_info_chrome_windows():
    # Arrange
    user_agent = 'Mozilla/5.0 (Windows NT 10.0) Chrome/120 Safari/537'

    # Act
    result = _parse_device_info(user_agent)

    # Assert
    assert result == {
        'browser': 'chrome',
        'os': 'windows',
        'device_type': 'desktop',
    }
