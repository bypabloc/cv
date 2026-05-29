"""
Given un secret y el code TOTP vigente (pyotp.TOTP(secret).now()),
When se verifica con verify_totp_code,
Then retorna True.
"""

from __future__ import annotations

import pyotp
from shared.auth import verify_totp_code


def test_totp_verify_correct() -> None:
    # Arrange
    b32 = 'JBSWY3DPEHPK3PXP'
    current_code = pyotp.TOTP(b32).now()

    # Act
    ok = verify_totp_code(secret_b32=b32, code=current_code)

    # Assert
    assert ok is True
