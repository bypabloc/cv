"""MfaMethodService.list_active devuelve los metodos como dicts.

Given el repo list_mfa_methods devuelve metodos activos,
When se invoca list_active,
Then devuelve dicts {kind, preferred, required, confirmed} (sin objetos ORM).
"""

from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_mfa_method_service_list_active_returns_dicts(monkeypatch):
    from services import mfa_method_service

    method = MagicMock()
    method.kind = MagicMock(value='totp')
    method.preferred = True
    method.required = False
    method.confirmed_at = datetime.now(tz=UTC)

    monkeypatch.setattr(mfa_method_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        mfa_method_service,
        'list_mfa_methods',
        lambda _s, *, user_id: [method],
    )

    svc = mfa_method_service.MfaMethodService(app_config=object())
    result = svc.list_active(user_id='user-1')

    assert result == [
        {
            'kind': 'totp',
            'preferred': True,
            'required': False,
            'confirmed': True,
        },
    ]
