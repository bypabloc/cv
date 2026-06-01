"""change-password con current correcta -> actualiza hash + revoca otras.

Given un user con la sesion en curso family 'fam-current' y dos sesiones
mas ('fam-other-1', 'fam-other-2'),
When se invoca profile.change-password con la current correcta,
Then actualiza el hash, revoca las dos sesiones != actual (blacklist de sus
families) y devuelve 200 con {is_valid, code:0, data:{ok:true}}.
"""

from unittest.mock import MagicMock

from .._helpers import _make_access_claims, _make_authed_event, _make_user


def test_profile_change_password_ok(monkeypatch):
    """update_password True -> revoca otras families + 200 ok:true."""
    from controllers.profile import change_password as ctl

    user = _make_user()
    claims = _make_access_claims(user_id=user.id, family_id='fam-current')

    profile_svc = MagicMock()
    profile_svc.update_password.return_value = True

    session_svc = MagicMock()
    session_svc.list_for_user.return_value = [
        {'session_id': 's-current', 'current': True},
        {'session_id': 's-other-1', 'current': False},
        {'session_id': 's-other-2', 'current': False},
    ]
    session_svc.revoke_session.side_effect = ['fam-other-1', 'fam-other-2']

    jwt_svc = MagicMock()
    dispatch_svc = MagicMock()

    monkeypatch.setattr(
        ctl, 'authenticate', lambda *_a, **_k: (user, claims),
    )
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'SessionService', lambda _c: session_svc)
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: dispatch_svc,
    )
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={
            'current_password': 'current-pass-12',
            'new_password': 'brand-new-pass-12',
        },
    )
    result = ctl.ChangePassword(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {'is_valid': True, 'code': 0, 'data': {'ok': True}}
    profile_svc.update_password.assert_called_once_with(
        user_id=user.id,
        current_password='current-pass-12',
        new_password='brand-new-pass-12',
    )
    jwt_svc.revoke_families.assert_called_once_with(
        family_ids=['fam-other-1', 'fam-other-2'],
        user_id=user.id,
    )
    assert dispatch_svc.publish_password_changed.call_count == 1
