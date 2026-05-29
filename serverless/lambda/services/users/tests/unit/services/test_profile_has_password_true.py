"""ProfileService.has_password — credencial presente.

Given un user con credencial password en auth_credentials,
When se invoca has_password,
Then devuelve True.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_has_password_true_when_credential_exists(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    fake_session.get.return_value = MagicMock()

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.has_password(user_id='user-1')

    assert result is True
