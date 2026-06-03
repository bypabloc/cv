"""
Given filas (dow, hour, count) agregadas en el rango,
When se invoca events_service.heatmap (sin cache, via __wrapped__),
Then devuelve {cells:[{dow, hour, count}]} con dow/hour como int.
"""

from datetime import date
from unittest.mock import MagicMock

import services.events_service as events_service


def test_events_heatmap_when_data_then_returns_cells(mocker):
    # Arrange: dos celdas del heatmap. EXTRACT devuelve Decimal -> int().
    row_a = MagicMock(name='CellA')
    row_a.dow = 1
    row_a.hour = 9
    row_a.count = 12
    row_b = MagicMock(name='CellB')
    row_b.dow = 3
    row_b.hour = 14
    row_b.count = 7

    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.return_value = [row_a, row_b]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(events_service, 'db_session', return_value=cm)

    # Act
    result = events_service.heatmap.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )

    # Assert
    assert result == {
        'cells': [
            {'dow': 1, 'hour': 9, 'count': 12},
            {'dow': 3, 'hour': 14, 'count': 7},
        ]
    }
