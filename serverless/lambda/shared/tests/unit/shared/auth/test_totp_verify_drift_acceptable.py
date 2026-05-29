"""
Given un code generado para la ventana TOTP anterior (hace 30s),
When se verifica en el instante actual con valid_window=1,
Then retorna True (tolera clock drift de +/- una ventana).
"""

from __future__ import annotations

import time

import pyotp
from shared.auth import verify_totp_code


def test_totp_verify_drift_acceptable() -> None:
    # Arrange — code de la ventana inmediatamente anterior.
    b32 = 'JBSWY3DPEHPK3PXP'
    code_prev_window = pyotp.TOTP(b32).at(int(time.time()) - 30)

    # Act — verify usa el tiempo actual; valid_window=1 cubre la prev.
    ok = verify_totp_code(secret_b32=b32, code=code_prev_window)

    # Assert
    assert ok is True
