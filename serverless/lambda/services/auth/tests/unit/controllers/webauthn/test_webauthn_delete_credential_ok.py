"""delete-credential con >1 metodo -> 204.

Given un user con total_mfa == 2 y un credential_id valido,
When se invoca webauthn.delete-credential,
Then borra el credential y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_delete_credential_ok(monkeypatch):
    """total_mfa == 2 -> DELETE + 204."""
    from controllers.webauthn import delete_credential

    user = _make_user(status='active')

    webauthn_svc = MagicMock()
    webauthn_svc.count_active.return_value = 2
    webauthn_svc.delete.return_value = True

    monkeypatch.setattr(
        delete_credential,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        delete_credential,
        'WebauthnService',
        lambda _c: webauthn_svc,
    )
    monkeypatch.setattr(
        delete_credential,
        'AuditService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(
        data={'credential_id': '01900000-0000-7000-8000-000000000002'},
    )
    result = delete_credential.DeleteCredential(event=event).run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    webauthn_svc.delete.assert_called_once()
