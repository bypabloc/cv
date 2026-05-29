"""
Given un code generado hace 90s (3 ventanas TOTP atras),
When se verifica en el instante actual con valid_window=1,
Then retorna False (fuera de la tolerancia de drift).
"""

from __future__ import annotations

import time

import pyotp
from shared.auth import verify_totp_code


def test_totp_verify_drift_too_old() -> None:
    # Arrange — code de 3 ventanas atras (fuera del valid_window=1).
    b32 = 'JBSWY3DPEHPK3PXP'
    code_90s_ago = pyotp.TOTP(b32).at(int(time.time()) - 90)

    # Act
    ok = verify_totp_code(secret_b32=b32, code=code_90s_ago)

    # Assert
    assert ok is False
