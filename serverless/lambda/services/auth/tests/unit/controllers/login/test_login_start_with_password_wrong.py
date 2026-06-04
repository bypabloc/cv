"""AC-21: login.start con password incorrecta -> 401 + failed_attempts++.

Given un email activo + password INCORRECTA,
When se invoca login.start con {email, password},
Then incrementa failed_attempts y devuelve 401 INVALID_PASSWORD.
"""

from types import SimpleNamespace
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
            'bypass_token': None,
            'origin': 'https://admin.portfolio.dev.the-full-stack.com',
            'authorization': 'Bearer PRECHECK-TEMP',
            'cloudfront_meta': {},
        },
    }


def test_login_start_with_password_wrong(monkeypatch):
    """AC-21: password incorrecta -> 401 + failed_attempts++."""
    from controllers.login import start

    user = _make_user(email='visitor@example.com', status='active')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = SimpleNamespace(
        sub=user.id, jti='precheck-jti', exp=9999999999, flow='login',
        typ='temp',
    )
    mfa_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(start, 'check_password', lambda **_k: False)

    event = _event_with_password('wrong-passphrase-1234')
    result = start.Start(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4000
    assert result['status'] == 401
    assert result['data']['error'] == 'INVALID_PASSWORD'
    user_svc.increment_failed_attempts.assert_called_once_with(user)
    jwt_svc.issue_access.assert_not_called()
