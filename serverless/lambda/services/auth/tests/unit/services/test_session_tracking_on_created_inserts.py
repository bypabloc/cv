"""SessionTrackingService.on_session_created — happy path.

Given un SessionTrackingService con db_session e insert_user_session
    mockeados,
When se llama on_session_created con user/family/ip/country/user_agent,
Then insert_user_session se invoca una vez con user_id, family_id, ip,
    country y device_info como dict.
"""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock


def test_session_tracking_on_created_inserts(monkeypatch):
    from services import session_tracking_service
    from services.session_tracking_service import SessionTrackingService

    # Arrange
    fake_session = MagicMock()

    @contextmanager
    def _fake_db_session():
        yield fake_session

    fake_insert = MagicMock()
    monkeypatch.setattr(
        session_tracking_service, 'db_session', _fake_db_session,
    )
    monkeypatch.setattr(
        session_tracking_service, 'insert_user_session', fake_insert,
    )
    svc = SessionTrackingService(SimpleNamespace())

    # Act
    svc.on_session_created(
        user_id='u',
        family_id='f',
        ip='1.2.3.4',
        country='CL',
        user_agent='Mozilla/5.0 (Windows NT 10.0) Chrome/120 Safari/537',
    )

    # Assert
    fake_insert.assert_called_once()
    kwargs = fake_insert.call_args.kwargs
    assert kwargs['user_id'] == 'u'
    assert kwargs['family_id'] == 'f'
    assert kwargs['ip'] == '1.2.3.4'
    assert kwargs['country'] == 'CL'
    assert kwargs['device_info'] == {
        'browser': 'chrome',
        'os': 'windows',
        'device_type': 'desktop',
    }
