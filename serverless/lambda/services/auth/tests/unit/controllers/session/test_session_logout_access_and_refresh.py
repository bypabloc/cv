"""AC-9: logout con access + refresh -> blacklistea jti + revoca familia.

Given un access JWT valido y un refresh JWT con family_id,
When se invoca session.logout con ambos,
Then blacklistea el access y revoca toda la familia del refresh, 204.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_logout, _make_session_claims

_FAKE_REFRESH = 'FAKE-REFRESH-' + ('X' * 16)


def test_session_logout_access_and_refresh(monkeypatch):
    """AC-9: logout con ambos tokens -> familia revocada."""
    from controllers.session import logout

    uid = uuid4()
    fid = uuid4()
    access_claims = _make_session_claims(typ='access', user_id=uid)
    refresh_claims = _make_session_claims(
        typ='refresh', user_id=uid, family_id=fid,
    )

    jwt_svc = MagicMock()
    jwt_svc.verify_allow_revoked.side_effect = [access_claims, refresh_claims]
    jwt_svc.is_blacklisted.return_value = False

    audit_svc = MagicMock()

    monkeypatch.setattr(logout, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(logout, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(logout, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_logout(refresh_token=_FAKE_REFRESH)
    controller = logout.Logout(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['status'] == 204
    jwt_svc.blacklist.assert_called_once()
    jwt_svc.revoke_family.assert_called_once_with(
        family_id=fid, user_id=uid, exp=refresh_claims.exp,
    )
