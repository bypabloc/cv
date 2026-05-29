"""ProfileService.has_password — sin credencial.

Given un user sin credencial password,
When se invoca has_password,
Then devuelve False.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_has_password_false_when_no_credential(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    fake_session.get.return_value = None

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.has_password(user_id='user-1')

    assert result is False
