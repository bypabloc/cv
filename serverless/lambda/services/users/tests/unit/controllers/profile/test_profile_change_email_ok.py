"""AC-4: change-email con email libre y sin password -> 200 magic-link.

Given un user sin password y un new_email libre,
When se invoca profile.change-email,
Then genera el magic-link, publica el email de confirmacion y devuelve
200 con request_id + expires_in == 900.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_change_email_ok(monkeypatch):
    """AC-4: email libre + sin password -> 200 + publish verify."""
    from controllers.profile import change_email as ctl

    user = _make_user()

    profile_svc = MagicMock()
    profile_svc.get_by_email.return_value = None
    profile_svc.has_password.return_value = False
    profile_svc.create_email_change_link.return_value = ('tok', 900)
    dispatch_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: dispatch_svc,
    )
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'new_email': 'new@example.com'})
    result = ctl.ChangeEmail(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['expires_in'] == 900
    assert 'request_id' in result['data']
    assert dispatch_svc.publish_email_change_verify.call_count == 1
    profile_svc.create_email_change_link.assert_called_once_with(
        user_id=user.id,
        new_email='new@example.com',
        ip='203.0.113.10',
        user_agent='pytest',
    )
