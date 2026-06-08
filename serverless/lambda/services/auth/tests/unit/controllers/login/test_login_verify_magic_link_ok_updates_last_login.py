"""AC-15: login.verify-magic-link de entrada (solo passwordless) -> tokens.

Given un magic-link de login valido + el user no tiene mas factores required,
When se invoca login.verify-magic-link,
Then consume el link, satisface 'passwordless', no quedan pendientes ->
emite access+refresh + redirect al callback con tokens + update_last_login.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_with_token, _make_magic_link, _make_user


def test_login_verify_magic_link_ok_updates_last_login(monkeypatch):
    """AC-15: magic-link de entrada (solo passwordless) -> tokens."""
    from controllers.login import _mfa_login, verify_magic_link

    link = _make_magic_link()
    user = _make_user(user_id=link.user_id, status='active')

    link_svc = MagicMock()
    link_svc.verify.return_value = link

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('LOGIN-ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('LOGIN-REFRESH-JWT', MagicMock())

    mfa_svc = MagicMock()
    mfa_svc.required_methods.return_value = ['passwordless']

    monkeypatch.setattr(
        verify_magic_link, 'MagicLinkService', lambda _c: link_svc,
    )
    monkeypatch.setattr(verify_magic_link, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(verify_magic_link, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(
        verify_magic_link, 'MfaMethodService', lambda _c: mfa_svc,
    )
    monkeypatch.setattr(
        verify_magic_link, 'AuditService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        verify_magic_link, 'RateLimitService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        _mfa_login, 'SessionTrackingService', lambda _c: MagicMock(),
    )

    event = _make_event_with_token(token='L' * 32)
    result = verify_magic_link.VerifyMagicLink(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'LOGIN-ACCESS-JWT'
    assert result['data']['refresh_token'] == 'LOGIN-REFRESH-JWT'
    assert result['data']['mfa_complete'] is True
    assert '#access=LOGIN-ACCESS-JWT' in result['data']['redirect_url']
    user_svc.update_last_login.assert_called_once_with(user)
    user_svc.mark_active.assert_not_called()
    # user ya active -> NO se crea email_code (solo en el alta pending->active).
    mfa_svc.ensure_email_code.assert_not_called()
