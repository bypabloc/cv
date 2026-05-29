"""ProfileService.admin_detail — user inexistente.

Given un user_id que no existe,
When se invoca admin_detail,
Then devuelve None.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_admin_detail_none_when_user_missing(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service, 'get_user_by_id', lambda _s, *, user_id: None,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.admin_detail(user_id='ghost')

    assert result is None
