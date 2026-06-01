"""WebauthnService.verify_login OK -> avanza sign_count + devuelve credential_id.

Given una assertion valida (verify_authentication devuelve un sign_count
  mayor),
When se invoca verify_login,
Then update_sign_count es llamado y devuelve el credential_id.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock


@contextmanager
def _fake_session():
    yield MagicMock()


def test_webauthn_service_verify_login_progresses(monkeypatch):
    from services import webauthn_service

    cred = MagicMock()
    cred.credential_id = b'\x10' * 16
    cred.public_key = b'\x20' * 32
    cred.sign_count = 5

    captured = {}

    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [cred],
    )
    monkeypatch.setattr(
        webauthn_service,
        'verify_authentication',
        lambda **_k: {'credential_id': b'\x10' * 16, 'new_sign_count': 6},
    )

    def fake_update(_s, *, credential_id, new_count):
        captured['credential_id'] = credential_id
        captured['new_count'] = new_count

    monkeypatch.setattr(webauthn_service, 'update_sign_count', fake_update)

    cfg = MagicMock(
        webauthn_rp_id='the-full-stack.com',
        webauthn_rp_name='TFS',
        webauthn_origins=['https://the-full-stack.com'],
    )
    svc = webauthn_service.WebauthnService(cfg)
    result = svc.verify_login(
        user_id='user-1',
        state={'s': 1},
        response={'id': 'x'},
    )

    assert result == b'\x10' * 16
    assert captured['new_count'] == 6
