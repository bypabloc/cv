"""AC-5: confirm-email-change con token valido -> 200 confirmed.

Given un token de magic-link valido y vigente,
When se invoca profile.confirm-email-change,
Then aplica el cambio, notifica al email viejo y devuelve 200 con
confirmed=True + email nuevo.
"""

from unittest.mock import MagicMock

from .._helpers import _make_public_event


def test_profile_confirm_email_change_ok(monkeypatch):
    """confirm_email_change retorna (uid, old, new) -> 200 confirmed."""
    from controllers.profile import confirm_email_change as ctl

    profile_svc = MagicMock()
    profile_svc.confirm_email_change.return_value = (
        '0193b8a0-0000-7000-8000-000000000099',
        'old@example.com',
        'new@example.com',
    )
    dispatch_svc = MagicMock()

    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: dispatch_svc,
    )
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_public_event(data={'token': 'a' * 40})
    result = ctl.ConfirmEmailChange(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['data']['confirmed'] is True
    assert result['data']['email'] == 'new@example.com'
    assert dispatch_svc.publish_email_changed.call_count == 1
