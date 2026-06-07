"""AC-11: verify-password con totp aun pendiente -> temp step=2 + methods.

Given un temp step=2 (`flow='login-mfa'`) valido + password correcta +
  required=['password','totp'],
When se invoca login.verify-password,
Then suma 'password' a satisfied, queda 'totp' pendiente -> rota un temp
  step=2 con flow='login-mfa:password' + methods=['totp'].
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_jwt_claims, _make_temp_event, _make_user


def test_login_verify_password_pending_totp(monkeypatch):
    """AC-11: password OK pero falta totp -> temp step=2 + methods=['totp']."""
    from controllers.login import verify_password

    uid = uuid4()
    user = _make_user(user_id=uid, status='active')
    claims = _make_jwt_claims(user_id=uid, flow='login-mfa', step=2)

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims
    jwt_svc.issue_temp.return_value = ('TEMP-STEP2-JWT', MagicMock())
    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user
    mfa_svc = MagicMock()
    mfa_svc.required_methods.return_value = ['password', 'totp']

    monkeypatch.setattr(verify_password, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_password, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        verify_password, 'MfaMethodService', lambda _c: mfa_svc,
    )
    monkeypatch.setattr(
        verify_password, 'AuditService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        verify_password, 'RateLimitService', lambda _c: MagicMock(),
    )
    monkeypatch.setattr(verify_password, 'check_password', lambda **_k: True)

    event = _make_temp_event(
        data={'temp_token': 'x' * 30, 'password': 'a-strong-passphrase-12'},
    )
    result = verify_password.VerifyPassword(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['temp_token'] == 'TEMP-STEP2-JWT'
    assert result['data']['methods'] == ['totp']
    assert result['data']['step'] == 2
    assert result['data']['mfa_complete'] is False
    # El nuevo temp lleva 'password' en los satisfechos del flow.
    assert jwt_svc.issue_temp.call_args.kwargs['flow'] == 'login-mfa:password'
    assert jwt_svc.issue_temp.call_args.kwargs['step'] == 2
    # No emite tokens (faltan factores).
    user_svc.update_last_login.assert_not_called()
