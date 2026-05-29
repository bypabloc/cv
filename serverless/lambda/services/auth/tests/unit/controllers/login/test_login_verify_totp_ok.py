"""AC-19: verify-totp con code correcto -> access+refresh.

Given un temp step=2 flow='login-mfa' + code TOTP correcto,
When se invoca login.verify-totp,
Then blacklistea el temp, marca last_used y emite access+refresh.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_jwt_claims, _make_temp_event


def test_login_verify_totp_ok(monkeypatch):
    """AC-19: code correcto -> access+refresh."""
    from controllers.login import verify_totp
    from shared.db.models.auth import AuthMfaKind

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='login-mfa', step=2)

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())
    mfa_svc = MagicMock()
    mfa_svc.get_totp_ciphertext.return_value = b'\x02' * 32
    totp_svc = MagicMock()
    totp_svc.verify.return_value = True

    monkeypatch.setattr(verify_totp, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_totp, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(verify_totp, 'TotpService', lambda _c: totp_svc)
    monkeypatch.setattr(verify_totp, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        verify_totp,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_temp_event(data={'temp_token': 'x' * 30, 'code': '123456'})
    result = verify_totp.VerifyTotp(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    jwt_svc.blacklist.assert_called_once()
    mfa_svc.mark_used.assert_called_once_with(
        user_id=uid,
        kind=AuthMfaKind.TOTP,
    )
