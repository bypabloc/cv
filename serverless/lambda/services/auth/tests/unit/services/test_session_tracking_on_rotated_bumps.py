"""SessionTrackingService.on_session_rotated — bump de actividad.

Given un SessionTrackingService con db_session y rotate_session_family_id
    mockeados,
When se llama on_session_rotated con old_family_id y new_family_id iguales,
Then rotate_session_family_id se invoca una vez con old_family_id='f' y
    new_family_id='f'.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


def test_session_tracking_on_rotated_bumps(monkeypatch):
    from services import session_tracking_service
    from services.session_tracking_service import SessionTrackingService

    # Arrange
    fake_session = MagicMock()

    @contextmanager
    def _fake_db_session():
        yield fake_session

    fake_rotate = MagicMock()
    monkeypatch.setattr(
        session_tracking_service, 'db_session', _fake_db_session,
    )
    monkeypatch.setattr(
        session_tracking_service,
        'rotate_session_family_id',
        fake_rotate,
    )
    svc = SessionTrackingService(SimpleNamespace())

    # Act
    svc.on_session_rotated(old_family_id='f', new_family_id='f')

    # Assert
    fake_rotate.assert_called_once()
    kwargs = fake_rotate.call_args.kwargs
    assert kwargs['old_family_id'] == 'f'
    assert kwargs['new_family_id'] == 'f'
