"""AC-9: logout con access valido -> blacklistea jti + 204.

Given un access JWT valido no blacklisted,
When se invoca session.logout (sin refresh),
Then blacklistea el jti del access y devuelve 204.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_logout, _make_session_claims


def test_session_logout_access_ok(monkeypatch):
    """AC-9: logout solo access -> 204."""
    from controllers.session import logout

    jti = uuid4()
    claims = _make_session_claims(typ='access', jti=jti)

    jwt_svc = MagicMock()
    jwt_svc.verify_allow_revoked.return_value = claims
    jwt_svc.is_blacklisted.return_value = False

    audit_svc = MagicMock()

    monkeypatch.setattr(logout, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(logout, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(logout, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_logout()
    controller = logout.Logout(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    jwt_svc.blacklist.assert_called_once()
    jwt_svc.revoke_family.assert_not_called()
