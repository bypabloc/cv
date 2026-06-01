"""AC-25: delete-credential de otro user -> 404 NOT_FOUND (no 403).

Given un user con total_mfa >= 2 y un credential_id que no es suyo
  (delete -> False por el filtro WHERE user_id),
When se invoca webauthn.delete-credential,
Then devuelve 404 NOT_FOUND (no 403, para evitar enumeration).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_webauthn_delete_credential_other_user(monkeypatch):
    """AC-25: credential de otro user -> 404 NOT_FOUND."""
    from controllers.webauthn import delete_credential

    user = _make_user(status='active')

    webauthn_svc = MagicMock()
    webauthn_svc.count_active.return_value = 2
    webauthn_svc.delete.return_value = False

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
        data={'credential_id': '01900000-0000-7000-8000-000000000099'},
    )
    result = delete_credential.DeleteCredential(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
