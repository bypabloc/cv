"""AC-10: recovery-codes-consume con code ya consumido -> 400.

Given un temp JWT step=2 fuerte + un code ya consumido (consume->False),
When se invoca mfa.recovery-codes-consume,
Then devuelve 400 RECOVERY_CODE_CONSUMED.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_jwt_claims, _make_temp_event


def test_mfa_recovery_codes_consume_already(monkeypatch):
    """AC-10: code ya consumido -> 400 RECOVERY_CODE_CONSUMED."""
    from controllers.mfa import recovery_codes_consume

    claims = _make_jwt_claims(user_id=uuid4(), flow='login-mfa', step=2)

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims
    recovery_svc = MagicMock()
    recovery_svc.consume.return_value = False

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

    assert result['is_valid'] is False
    assert result['code'] == 4008
    assert result['status'] == 400
    assert result['data']['error'] == 'RECOVERY_CODE_CONSUMED'
    jwt_svc.issue_access.assert_not_called()
