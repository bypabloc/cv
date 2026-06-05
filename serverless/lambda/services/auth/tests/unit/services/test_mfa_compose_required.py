"""compose_required: invariante de la lista de factores que el login exige.

Funcion pura del MfaMethodService (sin DB). Cubre:
- AC-2: sin ningun factor explicito -> passwordless es el required default.
- AC-6: password al frente cuando esta required.
- orden fijo + dedup + combinacion password + MFA.
"""

import pytest

from services.mfa_method_service import compose_required


def test_compose_required_no_factors_falls_back_to_passwordless():
    """AC-2: sin password ni MFA required -> ['passwordless']."""
    result = compose_required(password_required=False, mfa_required=[])
    assert result == ['passwordless']


def test_compose_required_password_only():
    """AC-6: password required, sin MFA -> ['password']."""
    result = compose_required(password_required=True, mfa_required=[])
    assert result == ['password']


def test_compose_required_password_and_totp_ordered():
    """AC-1/AC-6: password + totp -> orden fijo ['password', 'totp']."""
    result = compose_required(
        password_required=True, mfa_required=['totp'],
    )
    assert result == ['password', 'totp']


def test_compose_required_mfa_only_no_passwordless_fallback():
    """Con MFA required pero sin password -> NO se agrega passwordless."""
    result = compose_required(
        password_required=False, mfa_required=['totp', 'webauthn'],
    )
    assert result == ['totp', 'webauthn']


def test_compose_required_respects_fixed_order():
    """El orden de salida es _METHOD_ORDER, no el de entrada."""
    result = compose_required(
        password_required=True,
        mfa_required=['webauthn', 'email_code', 'totp'],
    )
    assert result == ['password', 'totp', 'email_code', 'webauthn']


@pytest.mark.parametrize(
    ('password_required', 'mfa_required', 'expected'),
    [
        (False, [], ['passwordless']),
        (True, [], ['password']),
        (False, ['totp'], ['totp']),
        (True, ['email_code'], ['password', 'email_code']),
    ],
)
def test_compose_required_table(password_required, mfa_required, expected):
    """Tabla de combinaciones (password_required, mfa_required) -> lista."""
    result = compose_required(
        password_required=password_required, mfa_required=mfa_required,
    )
    assert result == expected
