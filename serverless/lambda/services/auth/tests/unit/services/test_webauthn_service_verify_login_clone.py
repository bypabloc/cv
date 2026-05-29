"""AC-15: WebauthnService.verify_login con clone -> deshabilita + re-raise.

Given una assertion cuyo sign_count regreso (WebauthnCloneError),
When se invoca verify_login,
Then deshabilita el credential (disable_webauthn_credential) y re-lanza
  WebauthnCloneError.
"""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest


@contextmanager
def _fake_session():
    yield MagicMock()


def test_webauthn_service_verify_login_clone(monkeypatch):
    from services import webauthn_service
    from shared.auth.webauthn import WebauthnCloneError

    cred = MagicMock()
    cred.credential_id = b'\x10' * 16
    cred.public_key = b'\x20' * 32
    cred.sign_count = 5

    disabled = {}

    monkeypatch.setattr(webauthn_service, 'db_session', _fake_session)
    monkeypatch.setattr(
        webauthn_service,
        'get_webauthn_credentials',
        lambda _s, *, user_id: [cred],
    )

    def fake_verify(**_k):
        raise WebauthnCloneError('regression', credential_id=b'\x10' * 16)

    monkeypatch.setattr(
        webauthn_service,
        'verify_authentication',
        fake_verify,
    )
    monkeypatch.setattr(
        webauthn_service,
        'disable_webauthn_credential',
        lambda _s, *, credential_id: disabled.update(cid=credential_id),
    )

    cfg = MagicMock(
        webauthn_rp_id='the-full-stack.com',
        webauthn_rp_name='TFS',
        webauthn_origins=['https://the-full-stack.com'],
    )
    svc = webauthn_service.WebauthnService(cfg)

    with pytest.raises(WebauthnCloneError):
        svc.verify_login(user_id='user-1', state={'s': 1}, response={'id': 'x'})

    assert disabled == {'cid': b'\x10' * 16}
