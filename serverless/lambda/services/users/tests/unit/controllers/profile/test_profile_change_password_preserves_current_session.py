"""change-password revoca solo las families != actual (preserva la actual).

Given un user con la sesion en curso family 'fam-current' y una sesion mas
('fam-other'),
When se invoca profile.change-password con la current correcta,
Then la sesion actual NO se revoca (revoke_session NO se llama con su
session_id) y su family NO entra al blacklist (revoke_families recibe solo
['fam-other']).
"""

from unittest.mock import MagicMock

from .._helpers import _make_access_claims, _make_authed_event, _make_user


def test_profile_change_password_preserves_current_session(monkeypatch):
    """Solo la family != actual se blacklistea; la actual se preserva."""
    from controllers.profile import change_password as ctl

    user = _make_user()
    claims = _make_access_claims(user_id=user.id, family_id='fam-current')

    profile_svc = MagicMock()
    profile_svc.update_password.return_value = True

    session_svc = MagicMock()
    session_svc.list_for_user.return_value = [
        {'session_id': 's-current', 'current': True},
        {'session_id': 's-other', 'current': False},
    ]
    session_svc.revoke_session.return_value = 'fam-other'

    jwt_svc = MagicMock()

    monkeypatch.setattr(
        ctl, 'authenticate', lambda *_a, **_k: (user, claims),
    )
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'SessionService', lambda _c: session_svc)
    monkeypatch.setattr(ctl, 'JwtService', lambda _c: jwt_svc)
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: MagicMock(),
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
    # Solo la sesion != actual se revoca (la actual jamas se toca).
    session_svc.revoke_session.assert_called_once_with(
        user_id=user.id, session_id='s-other',
    )
    # La family actual NUNCA entra al blacklist.
    jwt_svc.revoke_families.assert_called_once_with(
        family_ids=['fam-other'], user_id=user.id,
    )
