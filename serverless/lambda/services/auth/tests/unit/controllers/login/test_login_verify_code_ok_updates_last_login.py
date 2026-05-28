"""AC-22: login.verify-code OK -> emite tokens + update_last_login.

Given un temp_token de login valido + code correcto,
When se invoca login.verify-code,
Then update_last_login (NO mark_active) + blacklistea temp + emite
access+refresh.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import (
    _make_event_with_code,
    _make_jwt_claims,
    _make_user,
)


def test_login_verify_code_ok_updates_last_login(monkeypatch):
    """AC-22: login code OK -> update_last_login + tokens."""
    from controllers.login import verify_code

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='login')
    user = _make_user(user_id=uid, status='active')

    flow_svc = MagicMock()
    flow_svc.verify_temp_token.return_value = claims

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    code_svc = MagicMock()
    code_svc.verify.return_value = True

    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('LOGIN-ACC', MagicMock())
    jwt_svc.issue_refresh.return_value = ('LOGIN-REF', MagicMock())

    monkeypatch.setattr(verify_code, 'FlowService', lambda _c: flow_svc)
    monkeypatch.setattr(verify_code, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(verify_code, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(verify_code, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_code, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_with_code(code='ABCDEFGH')
    controller = verify_code.VerifyCode(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'LOGIN-ACC'
    assert result['data']['refresh_token'] == 'LOGIN-REF'
    user_svc.update_last_login.assert_called_once_with(user)
    user_svc.mark_active.assert_not_called()
    jwt_svc.blacklist.assert_called_once()
