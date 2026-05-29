"""AC-2: confirm-totp con code correcto -> 204 y confirma el metodo.

Given un row TOTP pendiente y un code de 6 digitos correcto,
When se invoca mfa.confirm-totp,
Then verifica + confirma el metodo y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_confirm_totp_ok(monkeypatch):
    """AC-2: code correcto -> 204 + confirm."""
    from controllers.mfa import confirm_totp
    from shared.db.models import AuthMfaKind

    user = _make_user(status='active')

    totp_svc = MagicMock()
    totp_svc.verify.return_value = True
    mfa_svc = MagicMock()
    mfa_svc.get_totp_ciphertext.return_value = b'\x02' * 32
    mfa_svc.confirm.return_value = True

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

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    mfa_svc.confirm.assert_called_once_with(
        user_id=user.id,
        kind=AuthMfaKind.TOTP,
    )
