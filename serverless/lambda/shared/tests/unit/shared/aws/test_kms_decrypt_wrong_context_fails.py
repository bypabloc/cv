"""
Given un ciphertext cifrado con un EncryptionContext concreto,
When se llama kms_decrypt con un EncryptionContext DISTINTO,
Then levanta KmsError (el context queda bindeado al ciphertext).
"""

from __future__ import annotations

import boto3
import pytest
from moto import mock_aws
from shared.aws.kms import KmsError, kms_decrypt, kms_encrypt, reset_kms_cache


def test_kms_decrypt_wrong_context_fails() -> None:
    # Arrange
    with mock_aws():
        reset_kms_cache()
        key_id = boto3.client('kms', region_name='us-east-1').create_key()[
            'KeyMetadata'
        ]['KeyId']
        ciphertext = kms_encrypt(
            plaintext=b'secret',
            key_id=key_id,
            encryption_context={'user_id': 'u1', 'purpose': 'totp'},
        )

        # Act / Assert
        with pytest.raises(KmsError):
            kms_decrypt(
                ciphertext=ciphertext,
                encryption_context={'user_id': 'OTHER', 'purpose': 'totp'},
            )
    reset_kms_cache()
