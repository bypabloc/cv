"""
Given dos tipos de evento con counts y pct en el rango,
When se invoca events_service.distribution (sin cache, via __wrapped__),
Then devuelve {items:[{event_type, count, pct}]} ordenado por count desc.
"""

from datetime import date
from unittest.mock import MagicMock

import services.events_service as events_service


def test_events_distribution_when_data_then_returns_items(mocker):
    # Arrange: dos filas de la query agregada (event_type, count, pct).
    row_click = MagicMock(name='RowClick')
    row_click.event_type = 'click'
    row_click.count = 80
    row_click.pct = 80.0
    row_view = MagicMock(name='RowView')
    row_view.event_type = 'page_view'
    row_view.count = 20
    row_view.pct = 20.0

    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.return_value = [row_click, row_view]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(events_service, 'db_session', return_value=cm)

    # Act: __wrapped__ salta el @cached.
    result = events_service.distribution.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )

    # Assert
    assert result == {
        'items': [
            {'event_type': 'click', 'count': 80, 'pct': 80.0},
            {'event_type': 'page_view', 'count': 20, 'pct': 20.0},
        ]
    }
