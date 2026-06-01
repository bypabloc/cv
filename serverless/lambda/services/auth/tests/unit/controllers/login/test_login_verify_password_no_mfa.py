"""AC-20: verify-password con user sin MFA -> access+refresh directo.

Given un temp step=1 valido + password correcta + user SIN MFA,
When se invoca login.verify-password,
Then emite access+refresh directo (skip step 2).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_jwt_claims, _make_temp_event, _make_user


def test_login_verify_password_no_mfa(monkeypatch):
    """AC-20: password OK + sin MFA -> access+refresh directo."""
    from controllers.login import verify_password

    uid = uuid4()
    user = _make_user(user_id=uid, status='active')
    claims = _make_jwt_claims(user_id=uid, flow='login', step=1)

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())
    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user
    mfa_svc = MagicMock()
    mfa_svc.count_active.return_value = 0

    monkeypatch.setattr(verify_password, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_password, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        verify_password,
        'MfaMethodService',
        lambda _c: mfa_svc,
    )
    monkeypatch.setattr(
        verify_password,
        'AuditService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        verify_password,
        'RateLimitService',
        lambda _c: MagicMock(),
    )
    monkeypatch.setattr(
        verify_password,
        'check_password',
        lambda **_k: True,
    )

    event = _make_temp_event(
        data={'temp_token': 'x' * 30, 'password': 'a-strong-passphrase-12'},
    )
    result = verify_password.VerifyPassword(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    assert result['data']['expires_in'] == 900
    jwt_svc.issue_temp.assert_not_called()
