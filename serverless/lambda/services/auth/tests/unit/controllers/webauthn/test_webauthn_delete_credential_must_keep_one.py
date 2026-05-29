"""AC-17: delete-credential del unico metodo -> 409 MUST_KEEP_ONE_MFA_METHOD.

Given un user con total_mfa == 1,
When se invoca webauthn.delete-credential,
Then devuelve 409 MUST_KEEP_ONE_MFA_METHOD (no se queda sin MFA).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_delete_credential_must_keep_one(monkeypatch):
    """AC-17: total_mfa == 1 -> 409 MUST_KEEP_ONE_MFA_METHOD."""
    from controllers.webauthn import delete_credential

    user = _make_user(status='active')

    webauthn_svc = MagicMock()
    webauthn_svc.count_active.return_value = 1

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

    assert result['is_valid'] is False
    assert result['code'] == 4000
    assert result['status'] == 409
    assert result['data']['error'] == 'MUST_KEEP_ONE_MFA_METHOD'
    webauthn_svc.delete.assert_not_called()
