"""
Given un ciphertext producido por kms_encrypt con un EncryptionContext,
When se llama kms_decrypt con el MISMO EncryptionContext,
Then retorna exactamente el plaintext original.
"""

from __future__ import annotations

import boto3
from moto import mock_aws
from shared.aws.kms import kms_decrypt, kms_encrypt, reset_kms_cache


def test_kms_encrypt_decrypt_roundtrip() -> None:
    # Arrange
    with mock_aws():
        reset_kms_cache()
        key_id = boto3.client('kms', region_name='us-east-1').create_key()[
            'KeyMetadata'
        ]['KeyId']
        plaintext = b'JBSWY3DPEHPK3PXP'
        ctx = {'user_id': 'u1', 'purpose': 'totp'}

        # Act
        ciphertext = kms_encrypt(
            plaintext=plaintext,
            key_id=key_id,
            encryption_context=ctx,
        )
        recovered = kms_decrypt(ciphertext=ciphertext, encryption_context=ctx)

    # Assert
    assert recovered == plaintext
    reset_kms_cache()
