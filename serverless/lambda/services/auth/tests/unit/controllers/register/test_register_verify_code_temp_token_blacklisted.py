"""AC-10: temp_token blacklisted -> 401 TOKEN_BLACKLISTED.

Given un temp_token cuyo jti esta en DDB jwt-blacklist,
When se invoca register.verify-code,
Then flow_svc.verify_temp_token levanta JwtRevokedError; controller
devuelve 401 TOKEN_BLACKLISTED.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_with_code


def test_register_verify_code_temp_token_blacklisted(monkeypatch):
    """AC-10: temp blacklisted -> 401 TOKEN_BLACKLISTED."""
    from controllers.register import verify_code
    from shared.auth.jwt import JwtRevokedError

    flow_svc = MagicMock()
    flow_svc.verify_temp_token.side_effect = JwtRevokedError('revoked')

    monkeypatch.setattr(verify_code, 'FlowService', lambda _c: flow_svc)
    monkeypatch.setattr(verify_code, 'UserService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'CodeService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'JwtService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(verify_code, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_with_code()
    controller = verify_code.VerifyCode(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4003
    assert result['status'] == 401
    assert result['data']['error'] == 'TOKEN_BLACKLISTED'
