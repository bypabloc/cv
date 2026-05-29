"""
Given un secret y un code que NO corresponde a ninguna ventana valida,
When se verifica con verify_totp_code,
Then retorna False.
"""

from __future__ import annotations

import pyotp
from shared.auth import verify_totp_code


def test_totp_verify_wrong() -> None:
    # Arrange
    b32 = 'JBSWY3DPEHPK3PXP'
    current_code = pyotp.TOTP(b32).now()
    wrong_code = '654321' if current_code != '654321' else '123456'

    # Act
    ok = verify_totp_code(secret_b32=b32, code=wrong_code)

    # Assert
    assert ok is False
