"""AC-9: login.start de un user active abre el checklist de factores.

Given un precheck valido cuyo `sub` resuelve un user active,
When se invoca login.start (sin email ni password en el body),
Then NO envia email y devuelve un temp step=2 (`flow='login-mfa'`) con
  `methods` = los factores required + `mfa_complete:false`.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from .._helpers import _make_event_register_start, _make_user


def test_login_start_email_active_opens_checklist(monkeypatch):
    """AC-9: active -> temp step=2 + methods, sin email."""
    from controllers.login import start

    user = _make_user(email='visitor@example.com', status='active')

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('TEMP-MFA-JWT', MagicMock())
    jwt_svc.verify.return_value = SimpleNamespace(
        sub=user.id, jti='precheck-jti', exp=9999999999, flow='login',
        typ='temp',
    )
    mfa_svc = MagicMock()
    mfa_svc.required_methods.return_value = ['password', 'totp']
    email_svc = MagicMock()

    monkeypatch.setattr(start, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(start, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(start, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(start, 'EmailDispatchService', lambda _c: email_svc)
    monkeypatch.setattr(start, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(start, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_register_start(email='visitor@example.com')
    event['_meta']['authorization'] = 'Bearer PRECHECK-TEMP'
    result = start.Start(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['temp_token'] == 'TEMP-MFA-JWT'
    assert result['data']['methods'] == ['password', 'totp']
    assert result['data']['step'] == 2
    assert result['data']['mfa_complete'] is False
    # El temp del checklist es step=2 flow='login-mfa' (sin satisfechos).
    assert jwt_svc.issue_temp.call_args.kwargs['flow'] == 'login-mfa'
    assert jwt_svc.issue_temp.call_args.kwargs['step'] == 2
    # active NO envia email (eso es solo para alta/pending passwordless).
    email_svc.publish_unified.assert_not_called()
