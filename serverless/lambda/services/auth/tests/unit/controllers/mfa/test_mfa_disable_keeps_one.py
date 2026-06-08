"""AC-5: disable del unico metodo MFA -> 409 MUST_KEEP_ONE_MFA_METHOD.

Given un user con el metodo activo y total_mfa == 1 (cuenta transversal),
When se invoca mfa.disable con ese metodo,
Then devuelve 409 MUST_KEEP_ONE_MFA_METHOD (no se queda sin MFA).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_disable_keeps_one(monkeypatch):
    """AC-5: total_mfa == 1 -> 409 MUST_KEEP_ONE_MFA_METHOD."""
    from controllers.mfa import disable

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.has_active_method.return_value = True
    # Metodo CONFIRMADO: el guard MUST_KEEP_ONE aplica.
    mfa_svc.is_confirmed.return_value = True
    mfa_svc.count_active.return_value = 1

    monkeypatch.setattr(
        disable,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(disable, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(disable, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(disable, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'totp'})
    result = disable.Disable(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4000
    assert result['status'] == 409
    assert result['data']['error'] == 'MUST_KEEP_ONE_MFA_METHOD'
    mfa_svc.disable.assert_not_called()
