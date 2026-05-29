"""AC-27: refresh emitido antes de sessions_revoked_at -> 401 TOKEN_FAMILY_REVOKED.

Given un refresh valido (no reuse) cuyo iat es ANTERIOR a
  user.sessions_revoked_at (el user confirmo su primer MFA despues),
When se invoca session.refresh,
Then revoca la familia y devuelve 401 TOKEN_FAMILY_REVOKED (no rota).
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_refresh


def test_session_refresh_sessions_revoked_at(monkeypatch):
    """AC-27: iat < sessions_revoked_at -> 401 TOKEN_FAMILY_REVOKED."""
    from controllers.session import refresh

    uid = uuid4()
    fid = uuid4()
    revoked_at = datetime(2026, 5, 1, tzinfo=UTC)
    # iat ANTERIOR al revoke (1 dia antes en segundos unix).
    iat = int(revoked_at.timestamp()) - 86400
    claims = SimpleNamespace(
        sub=uid,
        jti=uuid4(),
        flow=None,
        step=None,
        exp=9999999999,
        iat=iat,
        typ='refresh',
        family_id=fid,
    )

    jwt_svc = MagicMock()
    jwt_svc.verify_allow_revoked.return_value = claims
    jwt_svc.is_blacklisted.return_value = False
    user = MagicMock()
    user.sessions_revoked_at = revoked_at
    user_svc = MagicMock()
    user_svc.get_by_id.return_value = user

    monkeypatch.setattr(refresh, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(refresh, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(refresh, 'RateLimitService', lambda _c: MagicMock())
    monkeypatch.setattr(refresh, 'UserService', lambda _c: user_svc)

    event = _make_event_refresh()
    result = refresh.Refresh(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4004
    assert result['status'] == 401
    assert result['data']['error'] == 'TOKEN_FAMILY_REVOKED'
    jwt_svc.revoke_family.assert_called_once_with(
        family_id=fid,
        user_id=uid,
        exp=claims.exp,
    )
    jwt_svc.issue_access.assert_not_called()
