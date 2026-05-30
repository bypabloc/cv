"""AC-1: nuevo email -> 200 con temp_token y user_id (registro happy path).

Given un email que no existe en `auth_users`,
When se invoca register.start con Turnstile valido,
Then crea user pending + genera code + magic-link + publica 2 SQS +
emite temp_token (5 min) y devuelve `is_valid=True`.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start, _make_user


def test_register_start_new_email_ok(monkeypatch):
    """AC-1: email nuevo -> 200 con temp_token."""
    from controllers.register import start

    new_user = _make_user(email='visitor@example.com', status='pending')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = None
    user_svc.create_pending.return_value = new_user

    code_svc = MagicMock()
    code_svc.generate_and_persist.return_value = ('ABCDEFGH', b'\x00' * 32)

    link_svc = MagicMock()
    link_svc.generate_and_persist.return_value = (
        'TOKEN' + 'A' * 27,
        b'\x01' * 32,
    )

    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('TEMP-JWT-FAKE', MagicMock())

    email_svc = MagicMock()
    audit_svc = MagicMock()
    rl_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: link_svc)
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
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

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['temp_token'] == 'TEMP-JWT-FAKE'
    assert result['data']['user_id'] == str(new_user.id)
    assert result['data']['expires_in'] == 300
    user_svc.create_pending.assert_called_once()
    email_svc.publish_magic_link.assert_called_once()
    email_svc.publish_code.assert_called_once()
