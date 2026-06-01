"""
Given bytes aleatorios que NO son un ciphertext valido de KMS,
When se llama kms_decrypt,
Then levanta KmsError.
"""

from __future__ import annotations

import pytest
from moto import mock_aws
from shared.aws.kms import KmsError, kms_decrypt, reset_kms_cache


def test_kms_decrypt_invalid_ciphertext() -> None:
    # Arrange
    with mock_aws():
        reset_kms_cache()

        # Act / Assert
        with pytest.raises(KmsError):
            kms_decrypt(
                ciphertext=b'not-a-real-ciphertext-blob',
                encryption_context={'user_id': 'u1', 'purpose': 'totp'},
            )
    reset_kms_cache()
