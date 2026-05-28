"""AC-7: refresh valido (no blacklisted) -> rota y emite par nuevo.

Given un refresh JWT valido cuyo jti NO esta blacklisted,
When se invoca session.refresh,
Then blacklistea el viejo y emite access+refresh nuevos (mismo family_id).
"""

from unittest.mock import MagicMock
from uuid import uuid4

from .._helpers import _make_event_refresh, _make_session_claims


def test_session_refresh_ok(monkeypatch):
    """AC-7: rotation OK."""
    from controllers.session import refresh

    fid = uuid4()
    claims = _make_session_claims(typ='refresh', family_id=fid)

    jwt_svc = MagicMock()
    jwt_svc.verify_allow_revoked.return_value = claims
    jwt_svc.is_blacklisted.return_value = False
    jwt_svc.issue_access.return_value = ('ACCESS-JWT', MagicMock())
    jwt_svc.issue_refresh.return_value = ('REFRESH-JWT', MagicMock())

    audit_svc = MagicMock()
    rl_svc = MagicMock()

    monkeypatch.setattr(refresh, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(refresh, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(refresh, 'RateLimitService', lambda _c: rl_svc)

    event = _make_event_refresh()
    controller = refresh.Refresh(event=event)
    result = controller.run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['access_token'] == 'ACCESS-JWT'
    assert result['data']['refresh_token'] == 'REFRESH-JWT'
    jwt_svc.blacklist.assert_called_once()
    jwt_svc.revoke_family.assert_not_called()
