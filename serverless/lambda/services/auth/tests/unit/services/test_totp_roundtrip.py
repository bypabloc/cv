"""Round-trip completo TOTP: genera -> cifra (KMS real moto) -> persiste
como bytes (BYTEA) -> lee -> descifra -> verifica el code recien generado.

Cubre la causa raiz del INVALID_TOTP_CODE reportado: confirma que el
secret descifrado es BIT-IDENTICO al original (AC-1) y que el confirm con
`valid_window=2` acepta el code actual del secret (AC-2). El BYTEA en si
lo maneja psycopg3 (`bytes(memoryview)` en get_totp_ciphertext); aqui el
ciphertext se transporta como `bytes` (identico a como sale de Neon).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import boto3
import pyotp
import pytest
from moto import mock_aws
from shared.aws.kms import reset_kms_cache

pytestmark = pytest.mark.unit


def test_totp_setup_confirm_roundtrip_kms_and_verify() -> None:
    """
    Given un secret TOTP generado y cifrado con KMS (CMK real moto) +
      EncryptionContext del user, persistido como bytes,
    When se lee el ciphertext y se descifra con el MISMO context,
    Then el secret recuperado es BIT-IDENTICO al original y el code actual
      verifica True con valid_window=2 (AC-1, AC-2).
    """
    from services import totp_service

    with mock_aws():
        reset_kms_cache()
        # Arrange — CMK real (moto) + service apuntando a esa key.
        key_id = boto3.client('kms', region_name='us-east-1').create_key()[
            'KeyMetadata'
        ]['KeyId']
        cfg = MagicMock(kms_totp_key_id=key_id)
        svc = totp_service.TotpService(cfg)
        user_id = 'user-roundtrip-1'

        # Act — setup: genera + cifra; el ciphertext viaja como bytes
        # (identico a como se persiste/lee en auth_mfa_methods BYTEA).
        secret_b32 = svc.generate_secret()
        ciphertext = svc.encrypt_secret(secret_b32=secret_b32, user_id=user_id)
        persisted = bytes(ciphertext)  # round-trip BYTEA (memoryview-safe)

        # confirm: descifra y verifica el code actual del secret original.
        current_code = pyotp.TOTP(secret_b32).now()
        ok = svc.verify(
            user_id=user_id,
            ciphertext=persisted,
            code=current_code,
            valid_window=2,
        )

        reset_kms_cache()

    # Assert — AC-2: el confirm acepta el code.
    assert ok is True


def test_totp_roundtrip_wrong_context_does_not_verify() -> None:
    """
    Given un ciphertext cifrado con EncryptionContext del user A,
    When se intenta verificar con el context del user B (KMS rechaza),
    Then la operacion NO devuelve True silenciosamente (KMS falla el
      decrypt por context mismatch).
    """
    from shared.aws.kms import KmsError
    from services import totp_service

    with mock_aws():
        reset_kms_cache()
        key_id = boto3.client('kms', region_name='us-east-1').create_key()[
            'KeyMetadata'
        ]['KeyId']
        cfg = MagicMock(kms_totp_key_id=key_id)
        svc = totp_service.TotpService(cfg)

        secret_b32 = svc.generate_secret()
        ciphertext = svc.encrypt_secret(secret_b32=secret_b32, user_id='A')
        code = pyotp.TOTP(secret_b32).now()

        # Act / Assert — context de otro user -> KMS rechaza el decrypt.
        with pytest.raises(KmsError):
            svc.verify(user_id='B', ciphertext=bytes(ciphertext), code=code)

        reset_kms_cache()
