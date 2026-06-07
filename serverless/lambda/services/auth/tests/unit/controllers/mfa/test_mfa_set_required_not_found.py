"""mfa.set-required de un metodo inexistente -> 404 NOT_FOUND.

Given un metodo que no existe o esta desactivado (service.set_required=False),
When se invoca mfa.set-required,
Then devuelve 404 NOT_FOUND (anti-enumeration).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_set_required_not_found(monkeypatch):
    """service.set_required -> False -> 404 NOT_FOUND."""
    from controllers.mfa import set_required as mfa_set_required

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.set_required.return_value = False
    audit_svc = MagicMock()

    monkeypatch.setattr(
        mfa_set_required,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(
        mfa_set_required,
        'MfaMethodService',
        lambda _c: mfa_svc,
    )
    monkeypatch.setattr(
        mfa_set_required,
        'AuditService',
        lambda _c: audit_svc,
    )
    monkeypatch.setattr(
        mfa_set_required,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(data={'kind': 'totp', 'required': True})
    result = mfa_set_required.SetRequired(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
    audit_svc.log.assert_not_called()
