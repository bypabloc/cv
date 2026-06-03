"""
Given un evento valido de visits/list con paginacion, filtros y JWT,
When el controller ejecuta (auth no-op + rate-limit no-op),
Then llama al service con el rango, paginacion (page/page_size/offset) y filtros.
"""

from datetime import date

import services.visits_service as visits_service
from controllers.visits.list import List


def test_visits_list_controller_when_valid_then_passes_pagination(
    mocker, mock_require_auth, mock_check_or_raise
):
    # Arrange
    expected = {
        'items': [],
        'page': 2,
        'page_size': 20,
        'total': 0,
        'has_more': False,
    }
    spy = mocker.patch.object(visits_service, 'list', return_value=expected)
    event = {
        'from': '2026-04-27',
        'to': '2026-05-27',
        'page': 2,
        'page_size': 20,
        'niche': 'fintech',
        'country': 'AR',
        '_meta': {'ip': '1.2.3.4', 'authorization': 'Bearer x'},
    }
    controller = List({**event})

    # Act
    controller.validate()
    result = controller.execute()

    # Assert
    assert result == {'is_valid': True, 'data': expected, 'code': 0}
    spy.assert_called_once_with(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        page=2,
        page_size=20,
        offset=20,
        niche='fintech',
        country='AR',
    )
