"""verify-totp con code incorrecto -> 401 INVALID_TOTP_CODE.

Given un temp step=2 valido + code TOTP incorrecto,
When se invoca login.verify-totp,
Then devuelve 401 INVALID_TOTP_CODE (no emite tokens).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_jwt_claims, _make_temp_event


def test_login_verify_totp_wrong(monkeypatch):
    """Code incorrecto -> 401 INVALID_TOTP_CODE."""
    from controllers.login import verify_totp

    claims = _make_jwt_claims(user_id=uuid4(), flow='login-mfa', step=2)

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims
    mfa_svc = MagicMock()
    mfa_svc.get_totp_ciphertext.return_value = b'\x02' * 32
    totp_svc = MagicMock()
    totp_svc.verify.return_value = False

    monkeypatch.setattr(verify_totp, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_totp, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(verify_totp, 'TotpService', lambda _c: totp_svc)
    monkeypatch.setattr(verify_totp, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        verify_totp,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_temp_event(data={'temp_token': 'x' * 30, 'code': '000000'})
    result = verify_totp.VerifyTotp(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4008
    assert result['status'] == 401
    assert result['data']['error'] == 'INVALID_TOTP_CODE'
    jwt_svc.issue_access.assert_not_called()
