"""AC-2: check-email de un user pending -> {exists, pending, temp_token}.

Given un email que existe en status pending,
When se invoca login.check-email,
Then devuelve {exists:true, pending:true, has_password:false, temp_token}.
El temp_token es el precheck (flow='login' step=0) que autoriza login.start
para terminar el alta (pending -> active).
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_check_email_pending(monkeypatch):
    """AC-2: pending -> exists+pending+has_password=false+temp_token."""
    from controllers.login import check_email
    from shared.db.models.auth.enums import AuthUserStatus

    user = MagicMock()
    user.id = 'usr-pending-1'
    user.status = AuthUserStatus.PENDING
    user_svc = MagicMock()
    user_svc.get_by_email.return_value = user
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('PRECHECK-PENDING-JWT', MagicMock())

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

    event = _make_event_register_start(email='pending@example.com')
    result = check_email.CheckEmail(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {
        'exists': True,
        'pending': True,
        'has_password': False,
        'temp_token': 'PRECHECK-PENDING-JWT',
    }
    assert jwt_svc.issue_temp.call_args.kwargs['flow'] == 'login'
    assert jwt_svc.issue_temp.call_args.kwargs['step'] == 0
