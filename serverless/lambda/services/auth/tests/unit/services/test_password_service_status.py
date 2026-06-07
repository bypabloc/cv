"""PasswordService.status devuelve el estado de la password (sin el hash).

Given el repo get_password_status devuelve el estado,
When se invoca status,
Then devuelve {has_password, last_change_at} sin tocar el hash.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_password_service_status_returns_repo_result(monkeypatch):
    """status delega en get_password_status y devuelve su dict."""
    from services import password_service

    expected = {
        'has_password': True,
        'last_change_at': '2026-01-01T00:00:00+00:00',
    }
    monkeypatch.setattr(password_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        password_service,
        'get_password_status',
        lambda _s, *, user_id: expected,
    )

    svc = password_service.PasswordService(app_config=object())
    result = svc.status(user_id='usr-1')

    assert result == expected
