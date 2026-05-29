"""ProfileService.confirm_email_change — link invalido/expirado.

Given un token cuyo magic-link no existe (consume devuelve None),
When se invoca confirm_email_change,
Then devuelve None.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_confirm_email_change_invalid_link_returns_none(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(profile_service, 'hash_token', lambda _t: 'h')
    monkeypatch.setattr(
        profile_service,
        'consume_email_change_link',
        lambda _s, *, token_hash: None,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.confirm_email_change(token='tok')

    assert result is None
