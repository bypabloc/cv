"""AC-2: email ya registrado activo -> 409 EMAIL_ALREADY_REGISTERED.

Given un email con user.status='active',
When se invoca register.start,
Then NO se publica email + responde is_valid=False con code 4002.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start, _make_user


def test_register_start_email_active_409(monkeypatch):
    """AC-2: email activo -> 409 sin publicar."""
    from controllers.register import start

    existing = _make_user(email='visitor@example.com', status='active')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = existing

    email_svc = MagicMock()
    audit_svc = MagicMock()
    rl_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: email_svc)
    monkeypatch.setattr(start, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: rl_svc)
    monkeypatch.setattr(
        start,
        'verify_captcha_or_bypass',
        lambda *_a, **_k: {'success': True},
    )

    event = _make_event_register_start(email='visitor@example.com')
    controller = start.Start(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4002
    assert result['status'] == 409
    assert result['data']['error'] == 'EMAIL_ALREADY_REGISTERED'
    email_svc.publish_unified.assert_not_called()
    email_svc.publish_magic_link.assert_not_called()
    email_svc.publish_code.assert_not_called()
