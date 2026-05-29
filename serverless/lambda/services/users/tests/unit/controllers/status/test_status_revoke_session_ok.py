"""AC-9: status.revoke-session cierra una sesion que no es la actual -> 204.

Given una sesion del user cuyo family ('fam-other') NO es el del access JWT
en curso ('fam-current'),
When se invoca status.revoke-session,
Then borra la sesion, blacklistea su family y devuelve 204.
"""

from unittest.mock import MagicMock

from .._helpers import _make_access_claims, _make_authed_event, _make_user


def test_status_revoke_session_ok(monkeypatch):
    """AC-9: family != current -> revoke + blacklist + 204."""
    from controllers.status import revoke_session as ctl

    user = _make_user(user_id='0193b8a0-0000-7000-8000-000000000009')
    claims = _make_access_claims(family_id='fam-current')

    session_svc = MagicMock()
    session_svc.get_family.return_value = 'fam-other'
    jwt_svc = MagicMock()

    monkeypatch.setattr(
        ctl, 'authenticate', lambda *_a, **_k: (user, claims),
    )
    monkeypatch.setattr(ctl, 'SessionService', lambda _c: session_svc)
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'session_id': '0193b8a0-0000-7000-8000-0000000000aa'},
    )
    result = ctl.RevokeSession(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    session_svc.revoke_session.assert_called_once_with(
        user_id=user.id,
        session_id='0193b8a0-0000-7000-8000-0000000000aa',
    )
    jwt_svc.revoke_families.assert_called_once_with(
        family_ids=['fam-other'], user_id=user.id,
    )
