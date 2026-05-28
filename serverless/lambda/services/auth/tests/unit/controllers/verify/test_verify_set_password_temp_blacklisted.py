"""AC-10: set-password con temp_token blacklisted -> 401 TOKEN_BLACKLISTED.

Given un temp_token cuyo jti ya esta en la blacklist,
When se invoca verify.set-password,
Then jwt.verify lanza JwtRevokedError y el controller devuelve 401.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_set_password


def test_verify_set_password_temp_blacklisted(monkeypatch):
    """AC-10: temp revocado -> 401 sin persistir password."""
    from controllers.verify import set_password

    from shared.auth import JwtRevokedError

    jwt_svc = MagicMock()
    jwt_svc.verify.side_effect = JwtRevokedError('revoked')

    user_svc = MagicMock()
    audit_svc = MagicMock()

    monkeypatch.setattr(set_password, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(set_password, 'UserService', lambda _c: user_svc)
    monkeypatch.setattr(set_password, 'FlowService', lambda _c: MagicMock())
    monkeypatch.setattr(set_password, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(set_password, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_set_password(password='a-very-strong-pass-1')
    controller = set_password.SetPassword(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4003
    assert result['status'] == 401
    assert result['data']['error'] == 'TOKEN_BLACKLISTED'
    user_svc.set_password_hash.assert_not_called()
