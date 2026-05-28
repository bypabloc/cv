"""AC-22: login.verify-magic-link OK -> emite tokens + update_last_login.

Given un magic-link de login valido,
When se invoca login.verify-magic-link,
Then consume el link + update_last_login (NO mark_active porque user
ya es active) + emite access+refresh.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_with_token, _make_magic_link, _make_user


def test_login_verify_magic_link_ok_updates_last_login(monkeypatch):
    """AC-22: login magic-link OK -> update_last_login + tokens."""
    from controllers.login import verify_magic_link

    link = _make_magic_link()
    user = _make_user(user_id=link.user_id, status='active')

    link_svc = MagicMock()
    link_svc.verify.return_value = link

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('LOGIN-ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('LOGIN-REFRESH-JWT', MagicMock())

    monkeypatch.setattr(
        verify_magic_link, 'MagicLinkService', lambda _c: link_svc,
    )
    monkeypatch.setattr(verify_magic_link, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(verify_magic_link, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_magic_link, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        verify_magic_link, 'RateLimitService', lambda _c: MagicMock(),
    )

    event = _make_event_with_token(token='L' * 32)
    controller = verify_magic_link.VerifyMagicLink(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'LOGIN-ACCESS-JWT'
    assert result['data']['refresh_token'] == 'LOGIN-REFRESH-JWT'
    user_svc.update_last_login.assert_called_once_with(user)
    user_svc.mark_active.assert_not_called()
