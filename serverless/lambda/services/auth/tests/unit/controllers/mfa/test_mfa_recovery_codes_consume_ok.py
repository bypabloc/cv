"""AC-9/AC-22: recovery-codes-consume con code valido -> 200 access+refresh.

Given un temp JWT step=2 flow='login-mfa' (factor fuerte) + code valido,
When se invoca mfa.recovery-codes-consume,
Then consume el code, blacklistea el temp y emite access+refresh.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_jwt_claims, _make_temp_event


def test_mfa_recovery_codes_consume_ok(monkeypatch):
    """AC-9: code valido + factor fuerte -> 200 con tokens."""
    from controllers.mfa import recovery_codes_consume

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='login-mfa', step=2)

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())
    recovery_svc = MagicMock()
    recovery_svc.consume.return_value = True

    monkeypatch.setattr(
        recovery_codes_consume,
        'JwtService',
        lambda _c: jwt_svc,
    )
    monkeypatch.setattr(
        recovery_codes_consume,
        'RecoveryCodesService',
        lambda _c: recovery_svc,
    )
    monkeypatch.setattr(
        recovery_codes_consume,
        'AuditService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        recovery_codes_consume,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_temp_event(
        data={'temp_token': 'x' * 30, 'code': 'ABCDEFGHJK'},
    )
    result = recovery_codes_consume.RecoveryCodesConsume(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    assert result['data']['expires_in'] == 900
    recovery_svc.consume.assert_called_once_with(
        user_id=uid,
        code='ABCDEFGHJK',
    )
    jwt_svc.blacklist.assert_called_once()
