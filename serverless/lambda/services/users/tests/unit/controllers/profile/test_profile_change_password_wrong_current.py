"""change-password con current incorrecta -> 401 INVALID_PASSWORD.

Given un user cuya current_password NO matchea el hash,
When se invoca profile.change-password,
Then devuelve 401 INVALID_PASSWORD, NO revoca sesiones ni notifica.
"""

from unittest.mock import MagicMock

from .._helpers import _make_access_claims, _make_authed_event, _make_user


def test_profile_change_password_wrong_current(monkeypatch):
    """update_password False -> 401 INVALID_PASSWORD sin side effects."""
    from controllers.profile import change_password as ctl

    user = _make_user()
    claims = _make_access_claims(user_id=user.id, family_id='fam-current')

    profile_svc = MagicMock()
    profile_svc.update_password.return_value = False

    session_svc = MagicMock()
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
            'current_password': 'wrong-current-pass',
            'new_password': 'brand-new-pass-12',
        },
    )
    result = ctl.ChangePassword(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 401
    assert result['code'] == 4005
    assert result['data'] == {'error': 'INVALID_PASSWORD', 'code': 4005}
    assert session_svc.revoke_session.call_count == 0
    assert jwt_svc.revoke_families.call_count == 0
    assert dispatch_svc.publish_password_changed.call_count == 0
