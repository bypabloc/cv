"""SessionTrackingService.on_session_created — best-effort sad path.

Given un SessionTrackingService cuyo insert_user_session lanza Exception,
When se llama on_session_created,
Then NO se propaga la excepcion (el tracking es best-effort) y
    on_session_created devuelve None.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


def test_session_tracking_on_created_swallows_errors(monkeypatch):
    from services import session_tracking_service
    from services.session_tracking_service import SessionTrackingService

    # Arrange
    fake_session = MagicMock()

    @contextmanager
    def _fake_db_session():
        yield fake_session

    fake_insert = MagicMock(side_effect=Exception('neon down'))
    monkeypatch.setattr(
        session_tracking_service, 'db_session', _fake_db_session,
    )
    monkeypatch.setattr(
        session_tracking_service, 'insert_user_session', fake_insert,
    )
    svc = SessionTrackingService(SimpleNamespace())

    # Act
    result = svc.on_session_created(
        user_id='u',
        family_id='f',
        ip='1.2.3.4',
        country='CL',
        user_agent='Mozilla/5.0',
    )

    # Assert
    assert result is None
