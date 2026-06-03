"""
Given visits/list con filtros (niche, country) y DBs que fallan en list y
  en landing_pages,
When se invocan los services,
Then aplica los filtros y traduce los errores de DB a ServiceError.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import services.visits_service as visits_service
from services._errors import ServiceError


def _cm(session):
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    return cm


def test_visits_list_filters_and_landing_pages_db_error(mocker):
    # Caso 1: list con filtros niche + country (ramas de filtro).
    session = MagicMock()
    session.scalar.return_value = 0
    session.execute.return_value.all.return_value = []
    mocker.patch.object(visits_service, 'db_session', return_value=_cm(session))
    result = visits_service.list(
        date_from=date(2026, 4, 27),
        date_to=date(2026, 5, 28),
        page=1,
        page_size=50,
        offset=0,
        niche='fintech',
        country='AR',
    )
    assert result['total'] == 0
    assert result['has_more'] is False

    # Caso 2: list con DB que falla -> ServiceError.
    bad = MagicMock()
    bad.scalar.side_effect = RuntimeError('boom')
    mocker.patch.object(visits_service, 'db_session', return_value=_cm(bad))
    with pytest.raises(ServiceError):
        visits_service.list(
            date_from=date(2026, 4, 27),
            date_to=date(2026, 5, 28),
            page=1,
            page_size=50,
            offset=0,
        )

    # Caso 3: landing_pages con DB que falla -> ServiceError (via __wrapped__).
    bad2 = MagicMock()
    bad2.execute.side_effect = RuntimeError('boom2')
    mocker.patch.object(visits_service, 'db_session', return_value=_cm(bad2))
    with pytest.raises(ServiceError):
        visits_service.landing_pages.__wrapped__(
            date_from=date(2026, 4, 27), date_to=date(2026, 5, 28), limit=10
        )
