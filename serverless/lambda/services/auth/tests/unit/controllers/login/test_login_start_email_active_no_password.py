"""AC-6: email activo -> 200 con temp_token + methods (sin password).

Given un email con user.status='active',
When se invoca login.start,
Then publica code + magic-link + devuelve temp_token con methods.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start, _make_user


def test_login_start_email_active_no_password(monkeypatch):
    """AC-6: email activo -> 200 con temp_token y methods."""
    from controllers.login import start

    user = _make_user(email='visitor@example.com', status='active')

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    code_svc = MagicMock()
    code_svc.generate_and_persist.return_value = ('ABCDEFGH', b'\x00' * 32)
    link_svc = MagicMock()
    link_svc.generate_and_persist.return_value = ('T' + 'X' * 31, b'\x01' * 32)
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('TEMP-LOGIN-JWT', MagicMock())
    email_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: link_svc)
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: email_svc)
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

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['temp_token'] == 'TEMP-LOGIN-JWT'
    assert result['data']['methods'] == ['magic-link', 'email-code']
    assert result['data']['expires_in'] == 300
    # UN solo email unificado (magic-link + code), no dos.
    email_svc.publish_unified.assert_called_once()
    email_svc.publish_magic_link.assert_not_called()
    email_svc.publish_code.assert_not_called()
    assert email_svc.publish_unified.call_args.kwargs['kind'] == 'login-unified'
