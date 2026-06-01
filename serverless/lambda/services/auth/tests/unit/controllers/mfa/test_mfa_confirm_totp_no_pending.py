"""confirm-totp sin row TOTP pendiente -> 404 NO_PENDING_TOTP.

Given un user sin row TOTP pendiente (get_totp_ciphertext devuelve None),
When se invoca mfa.confirm-totp,
Then devuelve 404 NO_PENDING_TOTP.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_confirm_totp_no_pending(monkeypatch):
    """Sin pending -> 404 NO_PENDING_TOTP."""
    from controllers.mfa import confirm_totp

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.get_totp_ciphertext.return_value = None
    totp_svc = MagicMock()

    monkeypatch.setattr(
        confirm_totp,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(confirm_totp, 'TotpService', lambda _c: totp_svc)
    monkeypatch.setattr(confirm_totp, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(confirm_totp, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        confirm_totp,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(data={'code': '123456'})
    result = confirm_totp.ConfirmTotp(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NO_PENDING_TOTP'
    totp_svc.verify.assert_not_called()
