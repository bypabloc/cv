"""AC-18: temp_token expirado -> 401 TEMP_TOKEN_EXPIRED.

Given un temp_token cuya signature OK pero exp<now,
When se invoca register.verify-code,
Then flow_svc.verify_temp_token levanta JwtExpiredError; el controller
captura y devuelve 401.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_with_code


def test_register_verify_code_temp_token_expired(monkeypatch):
    """AC-18: temp expirado -> 401 TEMP_TOKEN_EXPIRED."""
    from controllers.register import verify_code
    from shared.auth.jwt import JwtExpiredError

    flow_svc = MagicMock()
    flow_svc.verify_temp_token.side_effect = JwtExpiredError('exp')

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
    assert result['code'] == 4018
    assert result['status'] == 401
    assert result['data']['error'] == 'TEMP_TOKEN_EXPIRED'
