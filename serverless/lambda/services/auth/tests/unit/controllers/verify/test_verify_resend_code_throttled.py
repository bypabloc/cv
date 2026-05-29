"""AC-21: resend con < 60s desde el ultimo -> 429 RESEND_THROTTLED.

Given un temp_token valido pero la ultima emision hace 25s,
When se invoca verify.resend-code,
Then devuelve 429 RESEND_THROTTLED con retry_after y NO publica emails.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_resend_code, _make_jwt_claims, _make_user


def test_verify_resend_code_throttled(monkeypatch):
    """AC-21: throttle activo -> 429."""
    from controllers.verify import resend_code

    uid = uuid4()
    claims = _make_jwt_claims(user_id=uid, flow='register')
    user = _make_user(user_id=uid, status='pending')

    jwt_svc = MagicMock()
    jwt_svc.verify.return_value = claims

    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    code_svc = MagicMock()
    code_svc.seconds_until_resend_allowed.return_value = 35

    email_svc = MagicMock()
    audit_svc = MagicMock()

    monkeypatch.setattr(resend_code, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(resend_code, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(resend_code, 'CodeService', lambda _c: code_svc)
    monkeypatch.setattr(resend_code, 'MagicLinkService', lambda _c: MagicMock())
    monkeypatch.setattr(
        resend_code,
        'EmailDispatchService',
        lambda _c: email_svc,
    )
    monkeypatch.setattr(resend_code, 'FlowService', lambda _c: MagicMock())
    monkeypatch.setattr(resend_code, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(resend_code, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_resend_code()
    controller = resend_code.ResendCode(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4010
    assert result['status'] == 429
    assert result['data']['error'] == 'RESEND_THROTTLED'
    assert result['data']['retry_after'] == 35
    email_svc.publish_code.assert_not_called()
