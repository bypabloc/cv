"""set-preferred con metodo no configurado -> 400 MFA_NOT_CONFIGURED.

Given un user sin el metodo solicitado activo (set_preferred -> False),
When se invoca mfa.set-preferred,
Then devuelve 400 MFA_NOT_CONFIGURED.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_set_preferred_not_configured(monkeypatch):
    """Metodo no configurado -> 400 MFA_NOT_CONFIGURED."""
    from controllers.mfa import set_preferred

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.set_preferred.return_value = False

    monkeypatch.setattr(
        set_preferred,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(set_preferred, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(set_preferred, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(
        set_preferred,
        'RateLimitService',
        lambda _c: MagicMock(),
    )

    event = _make_authed_event(data={'kind': 'totp'})
    result = set_preferred.SetPreferred(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4000
    assert result['status'] == 400
    assert result['data']['error'] == 'MFA_NOT_CONFIGURED'
