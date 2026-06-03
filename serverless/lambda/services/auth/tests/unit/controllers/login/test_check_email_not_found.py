"""AC-C2: check-email de un email inexistente -> {exists:false}.

Given un email que no esta en auth_users,
When se invoca login.check-email,
Then devuelve {exists:false} (la UI ofrece crear cuenta).
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_check_email_not_found(monkeypatch):
    """AC-C2: email inexistente -> exists:false."""
    from controllers.login import check_email

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = None

    monkeypatch.setattr(check_email, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        check_email, 'PasswordService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(check_email, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(check_email, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        check_email, 'verify_captcha_or_bypass', lambda *_a, **_k: {},
    )

    event = _make_event_register_start(email='nobody@example.com')
    result = check_email.CheckEmail(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {'exists': False}
