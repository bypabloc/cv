"""
Given filas de device_type, browser y os con sus counts de sesiones,
When se invoca devices_service.breakdown (sin cache, via __wrapped__),
Then devuelve {device_types, browsers, os} ordenadas desc por sessions.
"""

from datetime import date
from unittest.mock import MagicMock

import services.devices_service as devices_service


def test_devices_breakdown_when_data_then_returns_distributions(mocker):
    # Arrange: una fila por distribucion (device_type, browser, os).
    row_desktop = MagicMock(name='RowDesktop')
    row_desktop.device_type = 'desktop'
    row_desktop.sessions = 70
    row_mobile = MagicMock(name='RowMobile')
    row_mobile.device_type = 'mobile'
    row_mobile.sessions = 30

    row_chrome = MagicMock(name='RowChrome')
    row_chrome.browser = 'Chrome'
    row_chrome.sessions = 60

    row_linux = MagicMock(name='RowLinux')
    row_linux.os = 'Linux'
    row_linux.sessions = 55

    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.side_effect = [
        [row_desktop, row_mobile],
        [row_chrome],
        [row_linux],
    ]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(devices_service, 'db_session', return_value=cm)

    # Act: __wrapped__ salta el @cached.
    result = devices_service.breakdown.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )

    # Assert
    assert result == {
        'device_types': [
            {'device_type': 'desktop', 'sessions': 70},
            {'device_type': 'mobile', 'sessions': 30},
        ],
        'browsers': [
            {'browser': 'Chrome', 'sessions': 60},
        ],
        'os': [
            {'os': 'Linux', 'sessions': 55},
        ],
    }
