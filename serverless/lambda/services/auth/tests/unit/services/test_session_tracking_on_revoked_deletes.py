"""SessionTrackingService.on_session_revoked — delete por family.

Given un SessionTrackingService con db_session y delete_session_by_family
    mockeados,
When se llama on_session_revoked con family_id='f',
Then delete_session_by_family se invoca una vez con family_id='f'.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


def test_session_tracking_on_revoked_deletes(monkeypatch):
    from services import session_tracking_service
    from services.session_tracking_service import SessionTrackingService

    # Arrange
    fake_session = MagicMock()

    @contextmanager
    def _fake_db_session():
        yield fake_session

    fake_delete = MagicMock()
    monkeypatch.setattr(
        session_tracking_service, 'db_session', _fake_db_session,
    )
    monkeypatch.setattr(
        session_tracking_service,
        'delete_session_by_family',
        fake_delete,
    )
    svc = SessionTrackingService(SimpleNamespace())

    # Act
    svc.on_session_revoked(family_id='f')

    # Assert
    fake_delete.assert_called_once()
    assert fake_delete.call_args.kwargs['family_id'] == 'f'
