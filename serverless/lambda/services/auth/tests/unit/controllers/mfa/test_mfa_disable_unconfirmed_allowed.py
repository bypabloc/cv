"""Un metodo MFA NO confirmado siempre se puede deshabilitar (anti-lockout).

Given un user con un TOTP en setup (confirmed=false, activo) y el guard
  transversal count_active == 1 (el TOTP pendiente no es una via de entrada
  real; el unico metodo confirmado es otro, ej. un passkey que SI cuenta),
When se invoca mfa.disable sobre el TOTP pendiente,
Then NO aplica el guard MUST_KEEP_ONE (un pendiente no protege el invariante)
  y lo deshabilita -> 204. Asi el user no queda atrapado con un setup-totp
  abandonado que no puede confirmar, marcar required, ni eliminar.
"""

from unittest.mock import MagicMock

from .._helpers import _make_authed_event, _make_user


def test_mfa_disable_unconfirmed_method_bypasses_keep_one(monkeypatch):
    """TOTP pendiente (no confirmado) -> disable permitido aunque count<=1."""
    from controllers.mfa import disable

    user = _make_user(status='active')

    mfa_svc = MagicMock()
    mfa_svc.has_active_method.return_value = True
    # El metodo NO esta confirmado: el guard MUST_KEEP_ONE NO debe aplicar.
    mfa_svc.is_confirmed.return_value = False
    # count_active <= 1 NO debe bloquear cuando el metodo es no-confirmado.
    mfa_svc.count_active.return_value = 1

    monkeypatch.setattr(
        disable, 'require_active_user', lambda *_a, **_k: user,
    )
    monkeypatch.setattr(disable, 'MfaMethodService', lambda _c: mfa_svc)
    monkeypatch.setattr(disable, 'AuditService', lambda _c: MagicMock())
    monkeypatch.setattr(disable, 'RateLimitService', lambda _c: MagicMock())

    event = _make_authed_event(data={'kind': 'totp'})
    result = disable.Disable(event=event).run()

    assert result['is_valid'] is True
    assert result['code'] == 0
    assert result['status'] == 204
    mfa_svc.disable.assert_called_once()
