"""AC-9: status.revoke-session de una sesion inexistente -> 404.

Given una sesion que no existe / no es del user (get_family devuelve None),
When se invoca status.revoke-session,
Then devuelve 404 NOT_FOUND y NO revoca nada.
"""

from unittest.mock import MagicMock

from .._helpers import _make_access_claims, _make_authed_event, _make_user


def test_status_revoke_session_not_found(monkeypatch):
    """get_family None -> 404 NOT_FOUND sin revoke ni blacklist."""
    from controllers.status import revoke_session as ctl

    user = _make_user(user_id='0193b8a0-0000-7000-8000-000000000011')
    claims = _make_access_claims(family_id='fam-current')

    session_svc = MagicMock()
    session_svc.get_family.return_value = None
    jwt_svc = MagicMock()

    monkeypatch.setattr(
        ctl, 'authenticate', lambda *_a, **_k: (user, claims),
    )
    monkeypatch.setattr(ctl, 'SessionService', lambda _c: session_svc)
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'session_id': '0193b8a0-0000-7000-8000-0000000000cc'},
    )
    result = ctl.RevokeSession(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
    assert session_svc.revoke_session.call_count == 0
    assert jwt_svc.revoke_families.call_count == 0
