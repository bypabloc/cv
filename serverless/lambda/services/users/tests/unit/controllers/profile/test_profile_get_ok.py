"""AC-1: profile.get devuelve el perfil del propio user -> 200.

Given un user activo con access JWT valido,
When se invoca profile.get,
Then devuelve 200 con el perfil + mfa_configured desde mfa_summary.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_get_ok(monkeypatch):
    """AC-1: profile.get -> 200 con perfil + mfa_configured."""
    from controllers.profile import get as ctl

    user = _make_user(
        user_id='0193b8a0-0000-7000-8000-000000000001',
        email='visitor@example.com',
        display_name='Visitor',
        locale='en',
        timezone='UTC',
        marketing_consent=False,
    )

    profile_svc = MagicMock()
    profile_svc.mfa_summary.return_value = {'mfa_configured': True}
    profile_svc.has_password.return_value = True

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event()
    result = ctl.Get(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['id'] == '0193b8a0-0000-7000-8000-000000000001'
    assert result['data']['email'] == 'visitor@example.com'
    assert result['data']['display_name'] == 'Visitor'
    assert result['data']['locale'] == 'en'
    assert result['data']['timezone'] == 'UTC'
    assert result['data']['marketing_consent'] is False
    assert result['data']['status'] == 'active'
    assert result['data']['mfa_configured'] is True
    assert result['data']['has_password'] is True
    profile_svc.mfa_summary.assert_called_once_with(user_id=user.id)
    profile_svc.has_password.assert_called_once_with(user_id=user.id)
