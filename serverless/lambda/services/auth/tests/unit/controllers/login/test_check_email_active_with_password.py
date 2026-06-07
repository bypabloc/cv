"""AC-1: check-email de un user active con password + metodos required.

Given un email que existe active, tiene password y marco password + totp
como required,
When se invoca login.check-email,
Then devuelve {exists:true, has_password:true, temp_token, methods_required}
con la lista de factores a completar (con su config de render). El temp_token
es el precheck (flow='login' step=0) que autoriza login.start.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_register_start


def test_check_email_active_with_password(monkeypatch):
    """AC-1: active -> exists+has_password+temp_token+methods_required."""
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
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('PRECHECK-TEMP-JWT', MagicMock())
    mfa_svc = MagicMock()
    mfa_svc.required_methods_config.return_value = [
        {
            'type': 'password',
            'input': 'password',
            'sent': None,
            'dispatch_action': 'login.verify-password',
        },
        {
            'type': 'totp',
            'input': 'code6',
            'sent': None,
            'dispatch_action': 'login.verify-totp',
        },
    ]

    monkeypatch.setattr(check_email, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        check_email, 'PasswordService', lambda _c: password_svc,
    )
    monkeypatch.setattr(check_email, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(
        check_email, 'MfaMethodService', lambda _c: mfa_svc,
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
    assert result['data'] == {
        'exists': True,
        'has_password': True,
        'temp_token': 'PRECHECK-TEMP-JWT',
        'methods_required': [
            {
                'type': 'password',
                'input': 'password',
                'sent': None,
                'dispatch_action': 'login.verify-password',
            },
            {
                'type': 'totp',
                'input': 'code6',
                'sent': None,
                'dispatch_action': 'login.verify-totp',
            },
        ],
    }
    # El precheck se emite con flow='login' step=0.
    assert jwt_svc.issue_temp.call_args.kwargs['flow'] == 'login'
    assert jwt_svc.issue_temp.call_args.kwargs['step'] == 0
