"""AC-4: code valido + temp_token valido -> exito (access+refresh tokens).

Given un temp_token register-flow valido y el code correcto,
When se invoca register.verify-code,
Then activa user + blacklistea temp + emite access+refresh.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import (
    _make_event_with_code,
    _make_jwt_claims,
    _make_user,
)


def test_register_verify_code_ok(monkeypatch):
    """AC-4: code OK -> exito + tokens."""
    from controllers.register import verify_code

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='register')
    user = _make_user(user_id=uid, status='pending')

    flow_svc = MagicMock()
    flow_svc.verify_temp_token.return_value = claims

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    code_svc = MagicMock()
    code_svc.verify.return_value = True

    jwt_svc = MagicMock()
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())

    audit_svc = MagicMock()
    rl_svc = MagicMock()

    monkeypatch.setattr(verify_code, 'FlowService', lambda _c: flow_svc)
    monkeypatch.setattr(verify_code, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(verify_code, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(verify_code, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(verify_code, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(verify_code, 'RateLimitService', lambda _c: rl_svc)

    event = _make_event_with_code(code='ABCDEFGH')
    controller = verify_code.VerifyCode(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    user_svc.mark_active.assert_called_once_with(user)
    jwt_svc.blacklist.assert_called_once()
