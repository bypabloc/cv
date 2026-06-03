"""
Given 2 paises con sus sessions/visits y eventos por sesion en el rango,
When se invoca geo_service.by_country (sin cache, via __wrapped__),
Then devuelve {items:[{country, sessions, visits, events}], total} con
     total = suma de sessions y events agregados por pais.
"""

from datetime import date
from unittest.mock import MagicMock

import services.geo_service as geo_service


def test_geo_by_country_when_data_then_returns_items(mocker):
    # Arrange
    # 1a query: sessions/visits por pais (ya ordenada desc, limitada).
    sv_ar = MagicMock()
    sv_ar.country = 'AR'
    sv_ar.sessions = 30
    sv_ar.visits = 45
    sv_us = MagicMock()
    sv_us.country = 'US'
    sv_us.sessions = 10
    sv_us.visits = 12

    # 2a query: session_id -> country (distinct) en el rango.
    sc1 = MagicMock()
    sc1.session_id = 's-ar-1'
    sc1.country = 'AR'
    sc2 = MagicMock()
    sc2.session_id = 's-us-1'
    sc2.country = 'US'

    # 3a query: events por session_id.
    ev1 = MagicMock()
    ev1.session_id = 's-ar-1'
    ev1.events = 200
    ev2 = MagicMock()
    ev2.session_id = 's-us-1'
    ev2.events = 50

    sv_result = MagicMock()
    sv_result.all.return_value = [sv_ar, sv_us]
    sc_result = MagicMock()
    sc_result.all.return_value = [sc1, sc2]
    ev_result = MagicMock()
    ev_result.all.return_value = [ev1, ev2]

    session = MagicMock(name='SQLAlchemySession')
    session.execute.side_effect = [sv_result, sc_result, ev_result]
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    mocker.patch.object(geo_service, 'db_session', return_value=cm)

    # Act
    result = geo_service.by_country.__wrapped__(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        limit=50,
    )

    # Assert
    assert result == {
        'items': [
            {'country': 'AR', 'sessions': 30, 'visits': 45, 'events': 200},
            {'country': 'US', 'sessions': 10, 'visits': 12, 'events': 50},
        ],
        'total': 40,
    }
