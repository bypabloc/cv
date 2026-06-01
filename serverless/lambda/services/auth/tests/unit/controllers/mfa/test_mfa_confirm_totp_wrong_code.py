"""AC-3: confirm-totp con code incorrecto -> 400 INVALID_TOTP_CODE + audit.

Given un row TOTP pendiente y un code incorrecto,
When se invoca mfa.confirm-totp,
Then devuelve 400 INVALID_TOTP_CODE y registra audit log failed.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_confirm_totp_wrong_code(monkeypatch):
    """AC-3: code incorrecto -> 400 + audit failed."""
    from controllers.mfa import confirm_totp

    user = _make_user(status='active')

    totp_svc = MagicMock()
    totp_svc.verify.return_value = False
    mfa_svc = MagicMock()
    mfa_svc.get_totp_ciphertext.return_value = b'\x02' * 32
    audit_svc = MagicMock()

    monkeypatch.setattr(
        confirm_totp,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(confirm_totp, 'TotpService', lambda _c: totp_svc)
    monkeypatch.setattr(confirm_totp, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(confirm_totp, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(
        confirm_totp,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(data={'code': '000000'})
    result = confirm_totp.ConfirmTotp(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 1002
    assert result['status'] == 400
    assert result['data']['error'] == 'INVALID_TOTP_CODE'
    mfa_svc.confirm.assert_not_called()
    audit_svc.log.assert_called_once()
    assert audit_svc.log.call_args.kwargs['success'] is False
