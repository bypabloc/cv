"""AC-7: status.get devuelve el estado del propio user + MFA -> 200.

Given un user activo con access JWT valido,
When se invoca status.get,
Then devuelve 200 con status + detalle MFA desde mfa_summary.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_status_get_ok(monkeypatch):
    """AC-7: status.get -> 200 con estado + detalle MFA."""
    from controllers.status import get as ctl

    user = _make_user(
        user_id='0193b8a0-0000-7000-8000-000000000007',
        status='active',
        failed_attempts=0,
    )

    profile_svc = MagicMock()
    profile_svc.mfa_summary.return_value = {
        'mfa_configured': True,
        'mfa_methods': ['totp'],
        'webauthn_count': 1,
        'recovery_codes_remaining': 8,
    }

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event()
    result = ctl.Get(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['status'] == 'active'
    assert result['data']['mfa_configured'] is True
    assert result['data']['mfa_methods'] == ['totp']
    assert result['data']['webauthn_count'] == 1
    assert result['data']['recovery_codes_remaining'] == 8
    assert result['data']['failed_attempts'] == 0
    assert result['data']['locked_until'] is None
    profile_svc.mfa_summary.assert_called_once_with(user_id=user.id)
