"""_parse_device_info — user-agent None.

Given un user-agent None,
When se llama _parse_device_info con None,
Then devuelve un dict vacio.
"""

from services.session_tracking_service import _parse_device_info


def test_parse_device_info_none_returns_empty():
    # Arrange
    user_agent = None

    # Act
    result = _parse_device_info(user_agent)

    # Assert
    assert result == {}
