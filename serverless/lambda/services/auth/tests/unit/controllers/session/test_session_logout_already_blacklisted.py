"""AC-23: logout con access ya blacklisted -> 204 idempotente.

Given un access JWT valido cuyo jti YA esta blacklisted,
When se invoca session.logout,
Then devuelve 204 sin re-blacklistear (idempotencia).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_logout, _make_session_claims


def test_session_logout_already_blacklisted(monkeypatch):
    """AC-23: logout idempotente -> 204 sin re-blacklistear."""
    from controllers.session import logout

    jti = uuid4()
    claims = _make_session_claims(typ='access', jti=jti)

    jwt_svc = MagicMock()
    jwt_svc.verify_allow_revoked.return_value = claims
    jwt_svc.is_blacklisted.return_value = True

    audit_svc = MagicMock()

    monkeypatch.setattr(logout, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(logout, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(logout, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_logout()
    controller = logout.Logout(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    jwt_svc.blacklist.assert_not_called()
