"""AC-8: refresh ya consumido (jti blacklisted) -> revoca familia + 401.

Given un refresh JWT cuyo jti YA esta blacklisted (reuso),
When se invoca session.refresh,
Then revoca toda la familia y devuelve 401 TOKEN_REUSE_DETECTED.
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_refresh, _make_session_claims


def test_session_refresh_reuse_detected(monkeypatch):
    """AC-8: reuso -> familia revocada + 401."""
    from controllers.session import refresh

    uid = uuid4()
    fid = uuid4()
    claims = _make_session_claims(typ='refresh', user_id=uid, family_id=fid)

    jwt_svc = MagicMock()
    jwt_svc.verify_allow_revoked.return_value = claims
    jwt_svc.is_blacklisted.return_value = True

    audit_svc = MagicMock()

    monkeypatch.setattr(refresh, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(refresh, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(refresh, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_refresh()
    controller = refresh.Refresh(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4004
    assert result['status'] == 401
    assert result['data']['error'] == 'TOKEN_REUSE_DETECTED'
    jwt_svc.revoke_family.assert_called_once_with(
        family_id=fid, user_id=uid, exp=claims.exp,
    )
    jwt_svc.issue_access.assert_not_called()
