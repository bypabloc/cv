"""AC-11: code WRONG (no llega al 5to) -> 400 INVALID_CODE + attempts++.

Given un code que no matchea + failed_attempts=1 -> 2,
When se invoca register.verify-code,
Then incrementa failed_attempts y devuelve 400 INVALID_CODE con
attempts.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import (
    _make_event_with_code,
    _make_jwt_claims,
    _make_user,
)


def test_register_verify_code_wrong_increments(monkeypatch):
    """AC-11: code wrong -> increment attempts + 400."""
    from controllers.register import verify_code

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='register')
    user = _make_user(user_id=uid, status='pending', failed_attempts=1)

    flow_svc = MagicMock()
    flow_svc.verify_temp_token.return_value = claims

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user
    user_svc.increment_failed_attempts.return_value = 2

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
    assert result['code'] == 4008
    assert result['status'] == 400
    assert result['data']['error'] == 'INVALID_CODE'
    assert result['data']['attempts'] == 2
    user_svc.increment_failed_attempts.assert_called_once_with(user)
    user_svc.lock_user.assert_not_called()
