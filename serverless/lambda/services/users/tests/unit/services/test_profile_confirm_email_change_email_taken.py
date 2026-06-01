"""ProfileService.confirm_email_change — el nuevo email fue tomado.

Given un magic-link valido cuyo new_email ya pertenece a otro user,
When se invoca confirm_email_change,
Then devuelve None (el link queda consumido).
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_confirm_email_change_email_taken_returns_none(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    link = MagicMock(
        user_id='user-1',
        meta_data={'new_email': 'taken@example.com'},
    )
    other = MagicMock(id='user-2')

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(profile_service, 'hash_token', lambda _t: 'h')
    monkeypatch.setattr(
        profile_service,
        'consume_email_change_link',
        lambda _s, *, token_hash: link,
    )
    monkeypatch.setattr(
        profile_service, 'get_user_by_email', lambda _s, _e: other,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.confirm_email_change(token='tok')

    assert result is None
