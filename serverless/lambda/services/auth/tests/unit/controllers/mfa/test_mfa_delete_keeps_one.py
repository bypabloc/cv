"""delete del unico metodo MFA CONFIRMADO -> 409 MUST_KEEP_ONE_MFA_METHOD.

Given un user con el metodo confirmado + activo y total_mfa == 1 (cuenta
  transversal),
When se invoca mfa.delete con ese metodo,
Then devuelve 409 MUST_KEEP_ONE_MFA_METHOD (no se queda sin MFA) y NO borra.
  El guard solo aplica a metodos confirmados (un pendiente siempre se borra).
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_delete_keeps_one(monkeypatch):
    """total_mfa == 1 + confirmado -> 409 MUST_KEEP_ONE_MFA_METHOD."""
    from controllers.mfa import delete

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.has_active_method.return_value = True
    # Metodo CONFIRMADO: el guard MUST_KEEP_ONE aplica.
    mfa_svc.is_confirmed.return_value = True
    mfa_svc.count_active.return_value = 1

    monkeypatch.setattr(
        delete,
        'require_active_user',
        lambda *_a, **_k: user,
    )
    monkeypatch.setattr(delete, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(delete, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(delete, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'totp'})
    result = delete.Delete(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 4000
    assert result['status'] == 409
    assert result['data']['error'] == 'MUST_KEEP_ONE_MFA_METHOD'
    mfa_svc.delete.assert_not_called()
