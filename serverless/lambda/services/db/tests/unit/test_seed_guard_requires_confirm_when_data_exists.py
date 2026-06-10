"""Guard del restore: seed sobre tablas pobladas exige confirm_overwrite.

Given las tablas CV ya tienen filas (_has_cv_data True),
When se invoca seed_service.run_seed sin confirm_overwrite,
Then levanta SeedRequiresConfirmError SIN resolver la fuente del snapshot;
y db_service la traduce a ServiceError code=4000 SEED_REQUIRES_CONFIRM.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


@contextmanager
def _fake_session(_session):
    yield _session


def test_seed_guard_requires_confirm_when_data_exists():
    from services import seed_service
    from services.db_service import ServiceError, run_seed
    from services.seed_service import SeedRequiresConfirmError

    # Arrange: la DB reporta filas en cv_profiles.
    session = MagicMock()
    session.execute.return_value.scalar.return_value = 1

    with (
        patch.object(
            seed_service, 'db_session', lambda: _fake_session(session)
        ),
        patch.object(seed_service, '_resolve_data_dir') as resolve_mock,
    ):
        # Act / Assert (capa seed_service)
        with pytest.raises(SeedRequiresConfirmError):
            seed_service.run_seed()
        assert resolve_mock.call_count == 0

        # Act / Assert (capa db_service: traduccion a ServiceError 4000)
        with pytest.raises(ServiceError) as exc_info:
            run_seed()
        assert exc_info.value.code == 4000
        assert exc_info.value.error_code == 'SEED_REQUIRES_CONFIRM'
