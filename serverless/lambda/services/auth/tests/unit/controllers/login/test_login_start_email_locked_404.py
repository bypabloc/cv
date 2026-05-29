"""AC-20: email locked/disabled -> 404 EMAIL_NOT_FOUND, suggest_register=False.

Given un email con status='locked' (mismo flujo para 'disabled'),
When se invoca login.start,
Then anti-enumeration: 404 EMAIL_NOT_FOUND con suggest_register=False
(NO revela que el user existe).
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start, _make_user


def test_login_start_email_locked_404(monkeypatch):
    """AC-20: locked -> 404 anti-enumeration."""
    from controllers.login import start

    user = _make_user(email='visitor@example.com', status='locked')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user

    email_svc = MagicMock()
    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: email_svc)
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        start,
        'verify_turnstile_token',
        lambda *_a, **_k: {'success': True},
    )

    event = _make_event_register_start(email='visitor@example.com')
    controller = start.Start(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'EMAIL_NOT_FOUND'
    assert result['data']['suggest_register'] is False
    email_svc.publish_magic_link.assert_not_called()
