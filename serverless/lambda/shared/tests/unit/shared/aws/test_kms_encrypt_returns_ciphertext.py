"""
Given una CMK creada en KMS (moto),
When se llama kms_encrypt con un EncryptionContext,
Then retorna un ciphertext (bytes) distinto del plaintext.
"""

from __future__ import annotations

import boto3
from moto import mock_aws
from shared.aws.kms import kms_encrypt, reset_kms_cache


def test_kms_encrypt_returns_ciphertext() -> None:
    # Arrange
    with mock_aws():
        reset_kms_cache()
        key = boto3.client('kms', region_name='us-east-1').create_key()
        key_id = key['KeyMetadata']['KeyId']
        plaintext = b'JBSWY3DPEHPK3PXP'

        # Act
        ciphertext = kms_encrypt(
            plaintext=plaintext,
            key_id=key_id,
            encryption_context={'user_id': 'u1', 'purpose': 'totp'},
        )

    # Assert
    assert isinstance(ciphertext, bytes)
    assert ciphertext != plaintext
    reset_kms_cache()
