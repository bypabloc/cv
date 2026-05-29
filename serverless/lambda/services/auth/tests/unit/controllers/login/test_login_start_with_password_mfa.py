"""AC-18: login.start con password + MFA -> temp step=2 + methods.

Given un email activo + password correcta + user CON MFA,
When se invoca login.start con {email, password},
Then emite temp JWT step=2 flow='login-mfa' + methods=['totp','webauthn'].
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


def test_login_start_with_password_mfa(monkeypatch):
    """AC-18: password OK + MFA -> temp step=2 + methods."""
    from controllers.login import start

    user = _make_user(email='visitor@example.com', status='active')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('TEMP-STEP2-JWT', MagicMock())
    mfa_svc = MagicMock()
    mfa_svc.count_active.return_value = 1

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
    assert result['data']['temp_token'] == 'TEMP-STEP2-JWT'
    assert result['data']['methods'] == ['totp', 'webauthn']
    assert result['data']['step'] == 2
    jwt_svc.issue_temp.assert_called_once_with(
        user_id=user.id,
        flow='login-mfa',
        step=2,
    )
