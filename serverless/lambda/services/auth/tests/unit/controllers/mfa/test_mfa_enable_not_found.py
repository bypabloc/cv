"""mfa.enable de un metodo inexistente -> 404 NOT_FOUND.

Given un metodo que no existe para el user (service.enable=False),
When se invoca mfa.enable,
Then devuelve 404 NOT_FOUND (anti-enumeration).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_enable_not_found(monkeypatch):
    """service.enable -> False -> 404 NOT_FOUND."""
    from controllers.mfa import enable as mfa_enable

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.enable.return_value = False
    audit_svc = MagicMock()

    monkeypatch.setattr(
        mfa_enable,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(mfa_enable, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(mfa_enable, 'AuditService', lambda _c: audit_svc)
    monkeypatch.setattr(mfa_enable, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'totp'})
    result = mfa_enable.Enable(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4001
    assert result['status'] == 404
    assert result['data']['error'] == 'NOT_FOUND'
    audit_svc.log.assert_not_called()
