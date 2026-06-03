"""
Given sessions=1000, visits=800, contacts=40 en el rango,
When se invoca funnel_service.conversion (sin cache, via __wrapped__),
Then devuelve los 3 counts + los 3 rates redondeados a 3 decimales.
"""

from datetime import date
from unittest.mock import MagicMock

import services.funnel_service as funnel_service


def test_funnel_conversion_when_data_then_returns_rates(mocker):
    # Arrange: mockear db_session en el namespace del service (la
    # referencia local que el service capturo al importar).
    session = MagicMock(name='SQLAlchemySession')
    session.scalar.side_effect = [1000, 800, 40]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(funnel_service, 'db_session', return_value=cm)

    # Act: __wrapped__ salta el @cached (testea el computo puro).
    result = funnel_service.conversion.__wrapped__(
        date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
    )

    # Assert
    assert result == {
        'sessions': 1000,
        'visits': 800,
        'contacts': 40,
        'session_to_visit_rate': 0.8,
        'visit_to_contact_rate': 0.05,
        'session_to_contact_rate': 0.04,
    }
