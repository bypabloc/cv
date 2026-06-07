"""
Given DBs que fallan en events/distribution y events/heatmap,
When se invocan los services (via __wrapped__, sin cache),
Then traducen el error de DB a ServiceError.
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


def test_events_distribution_and_heatmap_db_error_raises(mocker):
    bad = MagicMock()
    bad.execute.side_effect = RuntimeError('db down')
    mocker.patch.object(events_service, 'db_session', return_value=_cm(bad))

    with pytest.raises(ServiceError):
        events_service.distribution.__wrapped__(
            date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
        )
    with pytest.raises(ServiceError):
        events_service.heatmap.__wrapped__(
            date_from=date(2026, 4, 27), date_to=date(2026, 5, 28)
        )
