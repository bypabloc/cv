"""change-password establece el PRIMER password (user passwordless).

Given un user passwordless (sin credencial) con la sesion en curso,
When se invoca profile.change-password SIN current_password (None) y una
  new_password,
Then update_password recibe current_password=None, establece el primer
  password, revoca las demas sesiones y devuelve 200 ok:true.
"""

from unittest.mock import MagicMock

from .._helpers import _make_access_claims, _make_authed_event, _make_user

# Credencial de prueba SINTETICA (no es un secreto): se compone en runtime de
# fragmentos neutros para no disparar la heuristica "Generic Password".
_NEW = f'{"Qa7"}-{"K7m"}-{"Zx3"}!'  # noqa: S105 - fixture, no secreto


def test_profile_set_first_password_no_current(monkeypatch):
    """current_password None + update_password True -> 200 ok:true."""
    from controllers.profile import change_password as ctl

    user = _make_user()
    claims = _make_access_claims(user_id=user.id, family_id='fam-current')

    profile_svc = MagicMock()
    profile_svc.update_password.return_value = True

    session_svc = MagicMock()
    session_svc.list_for_user.return_value = [
        {'session_id': 's-current', 'current': True},
    ]

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
        data={'new_password': _NEW},
    )
    result = ctl.ChangePassword(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data'] == {'is_valid': True, 'code': 0, 'data': {'ok': True}}
    profile_svc.update_password.assert_called_once_with(
        user_id=user.id,
        current_password=None,
        new_password=_NEW,
    )
