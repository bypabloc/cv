"""AC-10: refresh con signature invalida -> 401 TOKEN_INVALID.

Given un refresh JWT cuya verificacion lanza JwtInvalidError,
When se invoca session.refresh,
Then devuelve 401 TOKEN_INVALID sin emitir tokens.
"""

from unittest.mock import MagicMock

from .._helpers import _make_event_refresh


def test_session_refresh_invalid_signature(monkeypatch):
    """AC-10: signature invalida -> 401."""
    from controllers.session import refresh
    from shared.auth import JwtInvalidError

    jwt_svc = MagicMock()
    jwt_svc.verify_allow_revoked.side_effect = JwtInvalidError('bad sig')

    audit_svc = MagicMock()

    monkeypatch.setattr(refresh, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(refresh, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(refresh, 'RateLimitService', lambda _c: MagicMock())

    event = _make_event_refresh()
    controller = refresh.Refresh(event=event)
    result = controller.run()

    assert result['is_valid'] is False
    assert result['code'] == 4003
    assert result['status'] == 401
    assert result['data']['error'] == 'TOKEN_INVALID'
    jwt_svc.issue_access.assert_not_called()
    jwt_svc.revoke_family.assert_not_called()
