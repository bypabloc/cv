"""AC-7: recovery-codes-generate -> 200 con 10 codes.

Given un user con MFA confirmado,
When se invoca mfa.recovery-codes-generate,
Then devuelve 200 con los 10 codes (mostrar UNA vez).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_recovery_codes_generate_first(monkeypatch):
    """AC-7: 200 con 10 codes."""
    from controllers.mfa import recovery_codes_generate

    user = _make_user(status='active')

    codes = [f'CODE{i:06d}' for i in range(10)]
    recovery_svc = MagicMock()
    recovery_svc.generate.return_value = codes

    monkeypatch.setattr(
        recovery_codes_generate,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        recovery_codes_generate,
        'RecoveryCodesService',
        lambda _c: recovery_svc,
    )
    monkeypatch.setattr(
        recovery_codes_generate,
        'AuditService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        recovery_codes_generate,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event()
    result = recovery_codes_generate.RecoveryCodesGenerate(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['codes'] == codes
    assert len(result['data']['codes']) == 10
