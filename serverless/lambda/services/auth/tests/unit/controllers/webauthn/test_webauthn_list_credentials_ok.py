"""AC-16: list-credentials -> 200 con credentials del user.

Given un user con N credentials,
When se invoca webauthn.list-credentials,
Then devuelve 200 con la lista (el service la ordena last_used DESC).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_list_credentials_ok(monkeypatch):
    """AC-16: 200 con la lista de credentials."""
    from controllers.webauthn import list_credentials

    user = _make_user(status='active')

    creds = [
        {'credential_id': 'c1', 'nickname': 'MacBook', 'transports': ['usb']},
        {'credential_id': 'c2', 'nickname': 'iPhone', 'transports': ['ble']},
    ]
    webauthn_svc = MagicMock()
    webauthn_svc.list_credentials.return_value = creds

    monkeypatch.setattr(
        list_credentials,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        list_credentials,
        'WebauthnService',
        lambda _c: webauthn_svc,
    )

    event = _make_authed_event()
    result = list_credentials.ListCredentials(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['credentials'] == creds
    webauthn_svc.list_credentials.assert_called_once_with(user_id=user.id)
