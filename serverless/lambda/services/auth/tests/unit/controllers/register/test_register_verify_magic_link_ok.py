"""AC-3: link valido -> consume + activa user + emite access+refresh.

Given un token de magic-link no consumido y no expirado,
When se invoca register.verify-magic-link,
Then consume el link + mark_active + emite access/refresh + devuelve
redirect_url al dashboard.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_with_token, _make_magic_link, _make_user


def test_register_verify_magic_link_ok(monkeypatch):
    """AC-3: magic-link valido -> exito con redirect_url."""
    from controllers.register import verify_magic_link

    link = _make_magic_link()
    user = _make_user(user_id=link.user_id, status='pending')

    link_svc = MagicMock()
    link_svc.verify.return_value = link

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())

    audit_svc = MagicMock()
    rl_svc = MagicMock()

    monkeypatch.setattr(
        verify_magic_link, 'MagicLinkService', lambda _c: link_svc
    )
    monkeypatch.setattr(verify_magic_link, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(verify_magic_link, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_magic_link, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(
        verify_magic_link, 'RateLimitService', lambda _c: rl_svc
    )

    event = _make_event_with_token(token='B' * 32)
    controller = verify_magic_link.VerifyMagicLink(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    assert 'redirect_url' in result['data']
    assert '#access=ACCESS-JWT' in result['data']['redirect_url']
    user_svc.mark_active.assert_called_once_with(user)
