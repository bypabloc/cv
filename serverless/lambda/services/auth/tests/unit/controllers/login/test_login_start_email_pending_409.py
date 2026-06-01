"""Login con email pending -> 409 PENDING_VERIFICATION.

Given un email con status='pending' (registro no completado),
When se invoca login.start,
Then devuelve 409 para empujar al user a completar el registro
(en vez de pretender login y mandar otro code).
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start, _make_user


def test_login_start_email_pending_409(monkeypatch):
    """Email pending -> 409 PENDING_VERIFICATION."""
    from controllers.login import start

    user = _make_user(email='visitor@example.com', status='pending')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        start,
        'verify_captcha_or_bypass',
        lambda *_a, **_k: {'success': True},
    )

    event = _make_event_register_start(email='visitor@example.com')
    controller = start.Start(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4011
    assert result['status'] == 409
    assert result['data']['error'] == 'PENDING_VERIFICATION'
