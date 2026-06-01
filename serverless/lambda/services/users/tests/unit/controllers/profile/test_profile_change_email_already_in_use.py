"""change-email con email ya en uso -> 409 EMAIL_ALREADY_IN_USE.

Given un new_email que ya pertenece a otra cuenta,
When se invoca profile.change-email,
Then devuelve 409 con error EMAIL_ALREADY_IN_USE sin generar magic-link.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_profile_change_email_already_in_use(monkeypatch):
    """get_by_email retorna un user -> 409 EMAIL_ALREADY_IN_USE."""
    from controllers.profile import change_email as ctl

    user = _make_user()
    existing = _make_user(email='taken@example.com')

    profile_svc = MagicMock()
    profile_svc.get_by_email.return_value = existing
    dispatch_svc = MagicMock()

    monkeypatch.setattr(ctl, 'require_active_user', lambda *_a, **_k: user)
    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: dispatch_svc,
    )
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'new_email': 'taken@example.com'})
    result = ctl.ChangeEmail(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 409
    assert result['data']['error'] == 'EMAIL_ALREADY_IN_USE'
    assert dispatch_svc.publish_email_change_verify.call_count == 0
