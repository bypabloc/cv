"""
Given un events/list con todos los filtros (niche, event_type, session_id,
  page_path) y, en otro caso, una DB que falla,
When se invoca events_service.list,
Then aplica los filtros (no rompe) y traduce el error de DB a ServiceError.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import services.events_service as events_service
from services._errors import ServiceError


def _cm(session):
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    return cm


def test_events_list_with_filters_applies_and_db_error_raises(mocker):
    # Caso 1: con todos los filtros -> la query corre (ramas de filtro).
    session = MagicMock()
    session.scalar.return_value = 0
    session.execute.return_value.all.return_value = []
    mocker.patch.object(events_service, 'db_session', return_value=_cm(session))
    result = events_service.list(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        page=1,
        page_size=50,
        offset=0,
        niche='fintech',
        event_type='page_view',
        session_id='sess-1',
        page_path='/projects',
    )
    assert result == {
        'items': [],
        'page': 1,
        'page_size': 50,
        'total': 0,
        'has_more': False,
    }

    # Caso 2: la DB falla -> ServiceError.
    bad_session = MagicMock()
    bad_session.scalar.side_effect = RuntimeError('connection lost')
    mocker.patch.object(
        events_service, 'db_session', return_value=_cm(bad_session)
    )
    with pytest.raises(ServiceError):
        events_service.list(
            date_from=date(2026, 4, 27),
            date_to=date(2026, 5, 28),
            page=1,
            page_size=50,
            offset=0,
        )
