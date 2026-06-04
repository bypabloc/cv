"""profile.get expone has_password=False para un user passwordless.

Given un user activo SIN credencial password,
When se invoca profile.get,
Then la respuesta incluye has_password: False (la UI ofrece "establecer").
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_get_has_password_false(monkeypatch):
    """has_password False -> presente en la respuesta de profile.get."""
    from controllers.profile import get as ctl

    user = _make_user(
        user_id='0193b8a0-0000-7000-8000-000000000002',
        email='nopass@example.com',
    )

    profile_svc = MagicMock()
    profile_svc.mfa_summary.return_value = {'mfa_configured': False}
    profile_svc.has_password.return_value = False

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event()
    result = ctl.Get(event=event).run()

    assert result['is_valid'] is True
    assert result['data']['has_password'] is False
    profile_svc.has_password.assert_called_once_with(user_id=user.id)
