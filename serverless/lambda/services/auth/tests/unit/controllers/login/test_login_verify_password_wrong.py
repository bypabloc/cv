"""AC-21: verify-password con password incorrecta -> 401 + failed_attempts++.

Given un temp step=1 valido + password INCORRECTA,
When se invoca login.verify-password,
Then incrementa failed_attempts y devuelve 401 INVALID_PASSWORD.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_jwt_claims, _make_temp_event, _make_user


def test_login_verify_password_wrong(monkeypatch):
    """AC-21: password incorrecta -> 401 + failed_attempts++."""
    from controllers.login import verify_password

    uid = uuid4()
    user = _make_user(user_id=uid, status='active')
    claims = _make_jwt_claims(user_id=uid, flow='login', step=1)

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims
    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    monkeypatch.setattr(verify_password, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_password, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(
        verify_password,
        'MfaMethodService',
        lambda _c: MagicMock(),
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
        lambda **_k: False,
    )

    event = _make_temp_event(
        data={'temp_token': 'x' * 30, 'password': 'wrong-passphrase-1234'},
    )
    result = verify_password.VerifyPassword(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4000
    assert result['status'] == 401
    assert result['data']['error'] == 'INVALID_PASSWORD'
    user_svc.increment_failed_attempts.assert_called_once_with(user)
    jwt_svc.issue_access.assert_not_called()
