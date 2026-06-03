"""AC-D2: email no existe -> crea el user pending + envia el email unificado.

Given un email que no esta en auth_users,
When se invoca login.start (fusion register->login, bloque D),
Then crea el user pending, publica UN email unificado y devuelve un
  temp_token (flow login, step 1) + created=True. (Ya NO devuelve 404.)
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_login_start_email_not_found_creates_pending(monkeypatch):
    """AC-D2: email nuevo -> crea pending + email + created=True."""
    from controllers.login import start

    new_user = MagicMock()
    new_user.id = 'usr-new'
    new_user.email = 'unknown@example.com'
    user_svc = MagicMock()
    user_svc.get_by_email.return_value = None
    user_svc.create_pending.return_value = new_user

    code_svc = MagicMock()
    code_svc.generate_and_persist.return_value = ('CODE1234', MagicMock())
    link_svc = MagicMock()
    link_svc.generate_and_persist.return_value = ('TOKEN-XYZ', MagicMock())
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('TEMP-JWT', MagicMock())
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

    event = _make_event_register_start(email='unknown@example.com')
    result = start.Start(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['temp_token'] == 'TEMP-JWT'
    assert result['data']['created'] is True
    assert result['data']['methods'] == ['magic-link', 'email-code']
    user_svc.create_pending.assert_called_once_with(
        email='unknown@example.com',
    )
    email_svc.publish_unified.assert_called_once()
    jwt_svc.issue_temp.assert_called_once_with(
        user_id='usr-new',
        flow='login',
        step=1,
    )
