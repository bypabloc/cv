"""ProfileService.soft_delete — devuelve las families a blacklistear.

Given un user que se auto-elimina (GDPR),
When se invoca soft_delete,
Then delega a soft_delete_user con email anonimizado y devuelve la lista
de family_id.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _ctx(session):
    yield session


def test_profile_soft_delete_returns_families(monkeypatch):
    from services import profile_service

    fake_session = MagicMock()
    calls = {}

    def fake_soft_delete(_session, *, user_id, anonymized_email):
        calls['user_id'] = user_id
        calls['anonymized_email'] = anonymized_email
        return ['fam-1', 'fam-2']

    monkeypatch.setattr(
        profile_service, 'db_session', lambda: _ctx(fake_session),
    )
    monkeypatch.setattr(
        profile_service, 'soft_delete_user', fake_soft_delete,
    )

    svc = profile_service.ProfileService(app_config=object())
    result = svc.soft_delete(user_id='user-1')

    assert result == ['fam-1', 'fam-2']
    assert calls['anonymized_email'] == 'deleted-user-1@invalid.local'
