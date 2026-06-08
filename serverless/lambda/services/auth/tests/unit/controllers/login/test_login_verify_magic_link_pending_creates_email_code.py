"""AC-2: login.verify-magic-link del alta (pending) crea el email_code.

Given un user PENDING que abre su magic-link de alta,
When login.verify-magic-link lo marca active,
Then ademas llama mfa_svc.ensure_email_code (el email queda verificado en el
  alta -> email_code configurado) y emite los tokens normalmente.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_with_token, _make_magic_link, _make_user


def test_login_verify_magic_link_pending_creates_email_code(monkeypatch):
    """El alta por magic-link (pending->active) crea el email_code confirmado."""
    from controllers.login import _mfa_login, verify_magic_link

    link = _make_magic_link()
    user = _make_user(user_id=link.user_id, status='pending')

    link_svc = MagicMock()
    link_svc.verify.return_value = link

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('ACC', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REF', MagicMock())

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
    user_svc.mark_active.assert_called_once_with(user)
    mfa_svc.ensure_email_code.assert_called_once_with(user_id=user.id)
