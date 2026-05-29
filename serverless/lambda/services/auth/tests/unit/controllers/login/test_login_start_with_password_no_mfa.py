"""AC-20: login.start con password correcta + sin MFA -> access+refresh.

Given un email activo + password correcta + user SIN MFA,
When se invoca login.start con {email, password},
Then emite access+refresh directo (skip step 2).
"""

from unittest.mock import MagicMock

from .._helpers import _make_user


def _event_with_password(password: str) -> dict:
    return {
        'email': 'visitor@example.com',
        'cf_turnstile_response': 'TURNSTILE-OK',
        'password': password,
        'niche': None,
        '_meta': {
            'ip': '203.0.113.10',
            'country': 'CL',
            'user_agent': 'pytest',
            'bypass_secret': None,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'cloudfront_meta': {},
        },
    }


def test_login_start_with_password_no_mfa(monkeypatch):
    """AC-20: password OK + sin MFA -> access+refresh directo."""
    from controllers.login import start

    user = _make_user(email='visitor@example.com', status='active')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())
    mfa_svc = MagicMock()
    mfa_svc.count_active.return_value = 0

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(
        start,
        'verify_turnstile_token',
        lambda *_a, **_k: {'success': True},
    )
    monkeypatch.setattr(start, 'check_password', lambda **_k: True)

    event = _event_with_password('a-strong-passphrase-12')
    result = start.Start(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    assert result['data']['expires_in'] == 900
    user_svc.update_last_login.assert_called_once_with(user)
    jwt_svc.issue_temp.assert_not_called()
