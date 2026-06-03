"""AC-C1: check-email de un user active con password -> {exists, has_password}.

Given un email que existe active y tiene password,
When se invoca login.check-email,
Then devuelve {exists:true, has_password:true} SIN la lista de metodos MFA.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_check_email_active_with_password(monkeypatch):
    """AC-C1: active con password -> exists+has_password, sin metodos."""
    from controllers.login import check_email
    from shared.db.models.auth.enums import AuthUserStatus

    user = MagicMock()
    user.id = 'usr-1'
    user.status = AuthUserStatus.ACTIVE
    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    password_svc = MagicMock()
    password_svc.status.return_value = {
        'has_password': True,
        'last_change_at': '2026-01-01T00:00:00+00:00',
    }

    monkeypatch.setattr(check_email, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        check_email, 'PasswordService', lambda _c: password_svc,
    )
    monkeypatch.setattr(check_email, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(check_email, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        check_email, 'verify_captcha_or_bypass', lambda *_a, **_k: {},
    )

    event = _make_event_register_start(email='u@example.com')
    result = check_email.CheckEmail(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {'exists': True, 'has_password': True}
    assert 'methods' not in result['data']
