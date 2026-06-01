"""mfa.list devuelve los metodos activos del user -> 200.

Given un user con metodos activos,
When se invoca mfa.list,
Then devuelve 200 con la lista de metodos.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_list_returns_active(monkeypatch):
    """mfa.list -> 200 con metodos del user."""
    from controllers.mfa import list as mfa_list

    user = _make_user(status='active')

    methods = [{'kind': 'totp', 'preferred': True, 'confirmed': True}]
    mfa_svc = MagicMock()
    mfa_svc.list_active.return_value = methods

    monkeypatch.setattr(
        mfa_list,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(mfa_list, 'MfaMethodService', lambda _c: mfa_svc)

    event = _make_authed_event()
    result = mfa_list.List(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['methods'] == methods
    mfa_svc.list_active.assert_called_once_with(user_id=user.id)
