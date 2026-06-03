"""
Given dos status de contacto con counts y pct en el rango,
When se invoca contacts_service.by_status (sin cache, via __wrapped__),
Then devuelve {items:[{status, count, pct}]} ordenado por count desc.
"""

from datetime import date
from unittest.mock import MagicMock

import services.contacts_service as contacts_service


def test_contacts_by_status_when_data_then_returns_items(mocker):
    # Arrange: dos filas de la query agregada (status, count, pct).
    row_new = MagicMock(name='RowNew')
    row_new.status = 'new'
    row_new.count = 80
    row_new.pct = 80.0
    row_converted = MagicMock(name='RowConverted')
    row_converted.status = 'converted'
    row_converted.count = 20
    row_converted.pct = 20.0

    session = MagicMock(name='SQLAlchemySession')
    session.execute.return_value.all.return_value = [row_new, row_converted]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(contacts_service, 'db_session', return_value=cm)

    # Act: __wrapped__ salta el @cached.
    result = contacts_service.by_status.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )

    # Assert
    assert result == {
        'items': [
            {'status': 'new', 'count': 80, 'pct': 80.0},
            {'status': 'converted', 'count': 20, 'pct': 20.0},
        ]
    }
