"""AC-11: failed_attempts >= 5 -> lock_user + 423 ACCOUNT_LOCKED.

Given un user con failed_attempts=4 + code wrong (lleva a 5),
When se invoca register.verify-code,
Then increment lleva a 5, dispara lock_user(until), devuelve 423.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import (
    _make_event_with_code,
    _make_jwt_claims,
    _make_user,
)


def test_register_verify_code_locks_after_5_fail(monkeypatch):
    """AC-11: 5to fallo -> lock + 423 ACCOUNT_LOCKED."""
    from controllers.register import verify_code

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='register')
    user = _make_user(user_id=uid, status='pending', failed_attempts=4)

    flow_svc = MagicMock()
    flow_svc.verify_temp_token.return_value = claims

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user
    user_svc.increment_failed_attempts.return_value = 5

    code_svc = MagicMock()
    code_svc.verify.return_value = False

    monkeypatch.setattr(verify_code, 'FlowService', lambda _c: flow_svc)
    monkeypatch.setattr(verify_code, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(verify_code, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(verify_code, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_with_code(code='WRNGABCD')
    controller = verify_code.VerifyCode(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4005
    assert result['status'] == 423
    assert result['data']['error'] == 'ACCOUNT_LOCKED'
    user_svc.lock_user.assert_called_once()
