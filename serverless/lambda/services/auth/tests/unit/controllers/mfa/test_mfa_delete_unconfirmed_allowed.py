"""Un metodo MFA NO confirmado siempre se puede BORRAR (anti-lockout).

Given un user con un TOTP en setup (confirmed=false, activo) y el guard
  transversal count_active == 1 (el TOTP pendiente no es una via de entrada
  real),
When se invoca mfa.delete sobre el TOTP pendiente,
Then NO aplica el guard MUST_KEEP_ONE y lo borra (hard-delete) -> 204. Asi el
  TOTP pendiente desaparece del overview (vuelve a configured:false) y el user
  puede reconfigurar de cero sin reusar el row viejo.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_delete_unconfirmed_method_bypasses_keep_one(monkeypatch):
    """TOTP pendiente (no confirmado) -> delete permitido aunque count<=1."""
    from controllers.mfa import delete

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.has_active_method.return_value = True
    # El metodo NO esta confirmado: el guard MUST_KEEP_ONE NO debe aplicar.
    mfa_svc.is_confirmed.return_value = False
    # count_active <= 1 NO debe bloquear cuando el metodo es no-confirmado.
    mfa_svc.count_active.return_value = 1

    monkeypatch.setattr(
        delete, 'require_active_user', lambda *_a, **_k: user,
    )
    monkeypatch.setattr(delete, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(delete, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(delete, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'totp'})
    result = delete.Delete(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    mfa_svc.delete.assert_called_once()
