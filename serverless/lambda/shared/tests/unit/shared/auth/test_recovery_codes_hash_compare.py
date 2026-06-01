"""
Given un recovery code y su hash SHA-256,
When se compara el code contra el hash guardado,
Then matchea el correcto (True) y rechaza uno distinto (False).
"""

from __future__ import annotations

from shared.auth.recovery_codes import compare_recovery_code, hash_recovery_code


def test_recovery_codes_hash_compare() -> None:
    # Arrange
    code = 'ABCD234XYZ'
    stored = hash_recovery_code(code)

    # Act / Assert
    assert compare_recovery_code(code=code, stored_hash=stored) is True
    assert compare_recovery_code(code='ZZZZ999AAA', stored_hash=stored) is False
