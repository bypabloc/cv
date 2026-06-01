"""AC-9b: recovery-codes-consume con factor debil -> 403.

Given un temp JWT que NO es step=2 flow='login-mfa' (ej. flow='login'
  de un paso passwordless),
When se invoca mfa.recovery-codes-consume,
Then devuelve 403 RECOVERY_REQUIRES_STRONG_FACTOR (decision 10).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_jwt_claims, _make_temp_event


def test_mfa_recovery_codes_consume_weak_factor(monkeypatch):
    """AC-9b: factor debil -> 403 RECOVERY_REQUIRES_STRONG_FACTOR."""
    from controllers.mfa import recovery_codes_consume

    # flow='login' (passwordless) NO es el flow fuerte 'login-mfa'.
    claims = _make_jwt_claims(user_id=uuid4(), flow='login', step=1)

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims
    recovery_svc = MagicMock()

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
    assert result['code'] == 4000
    assert result['status'] == 403
    assert result['data']['error'] == 'RECOVERY_REQUIRES_STRONG_FACTOR'
    recovery_svc.consume.assert_not_called()
