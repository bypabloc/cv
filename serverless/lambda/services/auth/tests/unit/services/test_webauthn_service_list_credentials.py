"""WebauthnService.list_credentials devuelve dicts serializables.

Given el repo get_webauthn_credentials devuelve credentials,
When se invoca list_credentials,
Then devuelve dicts {credential_id, nickname, transports, enabled, required,
  created_at, last_used_at} (sin objetos ORM).
"""

from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_webauthn_service_list_credentials(monkeypatch):
    from services import webauthn_service

    created = datetime(2026, 5, 1, tzinfo=UTC)
    cred = MagicMock()
    cred.id = 'rec-1'
    cred.nickname = 'MacBook'
    cred.transports = ['usb']
    cred.disabled_at = None
    cred.required = False
    cred.created_at = created
    cred.last_used_at = None

    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [cred],
    )

    svc = webauthn_service.WebauthnService(app_config=MagicMock())
    result = svc.list_credentials(user_id='user-1')

    assert result == [
        {
            'credential_id': 'rec-1',
            'nickname': 'MacBook',
            'transports': ['usb'],
            'enabled': True,
            'required': False,
            'created_at': created.isoformat(),
            'last_used_at': None,
        },
    ]
