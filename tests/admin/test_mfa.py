"""MFA TOTP del admin: enroll real (setup-totp -> confirm-totp) + login 2FA.

Cubre el setup REAL de TOTP a traves de una sesion autenticada del admin: el
backend emite el `secret_b32`, el harness genera el code con `shared.totp`
(mismo algoritmo RFC 6238 que el `pyotp` del backend) y `confirm-totp` lo
acepta -> el metodo TOTP queda activo. Esto prueba el enroll completo y que
el generador TOTP del harness empareja con el del backend. [AC-2]

DIFERIDO (anotado): el flujo de login con 2FA enteramente por la UI del
browser. Dos razones concretas, ambas del entorno desplegado:

  1. El submit del form de login esta gateado por Turnstile, que
     en el build DESPLEGADO de dev NO esta en modo E2E (el submit nunca se
     habilita en headless). El login real del browser se bootstrapea por el
     callback del magic-link (ver test_login_magic_link), que NO ejercita el
     step-up de 2FA.
  2. El gate de TOTP en el login depende del FACTOR: medido contra dev,
     `login.verify-code` (factor email-code) devuelve tokens completos SIN
     pedir TOTP; el step-up de TOTP aplica al factor `verify-password`. La UI
     del browser para ese step-up se ejercita mejor cuando el build honre el
     modo E2E (submit habilitado). El step-up de 2FA a nivel API se cubre en
     el modulo `tests/api/test_auth_mfa.py`.
"""

from __future__ import annotations

from shared.totp import totp_now

from .conftest import AdminAuth


def test_mfa_totp_enroll_confirms_with_harness_generated_code(
    auth: AdminAuth,
) -> None:
    """
    Given un user active autenticado,
    When pide setup-totp y confirma con el code TOTP que genera el harness
        desde el secret_b32 devuelto,
    Then el backend acepta la confirmacion (204) — el enroll TOTP completo y
        el generador TOTP del harness empareja con el pyotp del backend.
    """
    # Arrange: user active + su access token (sesion real del backend).
    _email, _user_id, access, _refresh = auth.create_active_user('mfa-enroll')

    # Act: setup-totp -> code TOTP del harness -> confirm-totp.
    status, secret = auth.mfa_setup_totp(access)
    assert status == 200
    assert secret is not None
    confirm_status = auth.mfa_confirm_totp(access, totp_now(secret))

    # Assert: confirmacion aceptada (TOTP activo).
    assert confirm_status == 204
