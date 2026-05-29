"""confirm-email-change con token invalido -> 400 INVALID_OR_EXPIRED_LINK.

Given un token de magic-link invalido/expirado/consumido,
When se invoca profile.confirm-email-change,
Then devuelve 400 con error INVALID_OR_EXPIRED_LINK sin notificar.
"""

from unittest.mock import MagicMock

from .._helpers import _make_public_event


def test_profile_confirm_email_change_invalid(monkeypatch):
    """confirm_email_change retorna None -> 400 INVALID_OR_EXPIRED_LINK."""
    from controllers.profile import confirm_email_change as ctl

    profile_svc = MagicMock()
    profile_svc.confirm_email_change.return_value = None
    dispatch_svc = MagicMock()

    monkeypatch.setattr(ctl, 'ProfileService', lambda _c: profile_svc)
    monkeypatch.setattr(
        ctl, 'EmailDispatchService', lambda _c: dispatch_svc,
    )
    monkeypatch.setattr(ctl, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(ctl, 'RateLimitService', lambda _c: MagicMock())

    event = _make_public_event(data={'token': 'b' * 40})
    result = ctl.ConfirmEmailChange(event=event).run()

    assert result['is_valid'] is False
    assert result['status'] == 400
    assert result['data']['error'] == 'INVALID_OR_EXPIRED_LINK'
    assert dispatch_svc.publish_email_changed.call_count == 0
