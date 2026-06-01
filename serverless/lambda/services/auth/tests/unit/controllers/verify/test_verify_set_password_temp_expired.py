"""AC-18: set-password con temp_token expirado -> 401 TEMP_TOKEN_EXPIRED.

Given un temp_token cuyo exp ya paso,
When se invoca verify.set-password,
Then jwt.verify lanza JwtExpiredError y el controller devuelve 401.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_set_password


def test_verify_set_password_temp_expired(monkeypatch):
    """AC-18: temp expirado -> 401 sin persistir password."""
    from controllers.verify import set_password
    from shared.auth.jwt import JwtExpiredError

    jwt_svc = MagicMock()
    jwt_svc.verify.side_effect = JwtExpiredError('expired')

    user_svc = MagicMock()
    audit_svc = MagicMock()

    monkeypatch.setattr(set_password, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(set_password, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(set_password, 'FlowService', lambda _c: MagicMock())
    monkeypatch.setattr(set_password, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(
        set_password, 'RateLimitService', lambda _c: MagicMock()
    )

    event = _make_event_set_password(password='a-very-strong-pass-1')
    controller = set_password.SetPassword(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4018
    assert result['status'] == 401
    assert result['data']['error'] == 'TEMP_TOKEN_EXPIRED'
    user_svc.set_password_hash.assert_not_called()
