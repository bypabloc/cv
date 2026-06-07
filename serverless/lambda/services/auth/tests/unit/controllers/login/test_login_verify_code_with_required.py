"""AC-14: verify-code de un user active con required adicional -> no tokens.

Given un temp step=2 (`flow='login-mfa'`) + code correcto + el user tiene
  required=['email_code','totp'],
When se invoca login.verify-code,
Then satisface 'email_code', queda 'totp' pendiente -> rota un temp step=2 +
  methods=['totp'] (NO emite tokens: el code/email no saltea los required).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_with_code, _make_jwt_claims, _make_user


def test_login_verify_code_with_required_pending(monkeypatch):
    """AC-14: code OK pero falta totp -> temp step=2 + methods=['totp']."""
    from controllers.login import verify_code

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='login-mfa', step=2)
    user = _make_user(user_id=uid, status='active')

    flow_svc = MagicMock()
    flow_svc.verify_temp_token.return_value = claims
    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user
    code_svc = MagicMock()
    code_svc.verify.return_value = True
    jwt_svc = MagicMock()
    jwt_svc.issue_temp.return_value = ('TEMP-STEP2-NEW', MagicMock())
    mfa_svc = MagicMock()
    mfa_svc.required_methods.return_value = ['email_code', 'totp']

    monkeypatch.setattr(verify_code, 'FlowService', lambda _c: flow_svc)
    monkeypatch.setattr(verify_code, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(verify_code, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(verify_code, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_code, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(verify_code, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_with_code(code='ABCDEFGH')
    result = verify_code.VerifyCode(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['temp_token'] == 'TEMP-STEP2-NEW'
    assert result['data']['methods'] == ['totp']
    assert result['data']['mfa_complete'] is False
    # email_code es el factor satisfecho (estaba en required, no passwordless).
    assert (
        jwt_svc.issue_temp.call_args.kwargs['flow'] == 'login-mfa:email_code'
    )
    # NO emite tokens ni actualiza last_login (faltan factores).
    jwt_svc.issue_access.assert_not_called()
    user_svc.update_last_login.assert_not_called()
