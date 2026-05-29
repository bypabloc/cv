"""change-email con password incorrecta -> 401 INVALID_PASSWORD.

Given un user con password y un new_email libre,
When se invoca profile.change-email con password que no matchea,
Then devuelve 401 con error INVALID_PASSWORD sin generar magic-link.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_change_email_wrong_password(monkeypatch):
    """has_password True + verify_password False -> 401 INVALID_PASSWORD."""
    from controllers.profile import change_email as ctl

    user = _make_user()

    profile_svc = MagicMock()
    profile_svc.get_by_email.return_value = None
    profile_svc.has_password.return_value = True
    profile_svc.verify_password.return_value = False
    dispatch_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: dispatch_svc,
    )
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(
        data={'new_email': 'new@example.com', 'password': 'wrongpassword1'},
    )
    result = ctl.ChangeEmail(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 401
    assert result['data']['error'] == 'INVALID_PASSWORD'
    assert dispatch_svc.publish_email_change_verify.call_count == 0
