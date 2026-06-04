"""AC-2/AC-3: check-email de un email inexistente -> {exists:false, temp_token}.

Given un email que no esta en auth_users,
When se invoca login.check-email,
Then devuelve {exists:false} CON temp_token: la fusion register->login deja
que login.start CREE el pending, asi que el alta tambien necesita el precheck.
El temp se emite con un sub placeholder (aun no hay user).
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_check_email_not_found(monkeypatch):
    """AC-2/AC-3: email inexistente -> exists:false + temp_token (alta)."""
    from controllers.login import check_email

    user_svc = MagicMock()
    user_svc.get_by_email.return_value = None
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('PRECHECK-NEW-EMAIL-JWT', MagicMock())

    monkeypatch.setattr(check_email, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        check_email, 'PasswordService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(check_email, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(check_email, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(check_email, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(
        check_email, 'verify_captcha_or_bypass', lambda *_a, **_k: {},
    )

    event = _make_event_register_start(email='nobody@example.com')
    result = check_email.CheckEmail(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {
        'exists': False,
        'temp_token': 'PRECHECK-NEW-EMAIL-JWT',
    }
    # Email inexistente: SI emite precheck (login.start crea el pending).
    assert jwt_svc.issue_temp.call_args.kwargs['flow'] == 'login'
    assert jwt_svc.issue_temp.call_args.kwargs['step'] == 0
