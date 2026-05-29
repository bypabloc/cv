"""AWS KMS Encrypt/Decrypt con CMK directa.

Para secretos <= 4 KB (limite de `kms:Encrypt`). El `EncryptionContext`
es obligatorio: queda bindeado al ciphertext (audit en CloudTrail +
binding criptografico al `user_id`). El decrypt DEBE pasar el MISMO
`EncryptionContext` o falla.

NO envelope encryption: el secret TOTP es 20 bytes (160 bits), entra
holgado en el limite de 4 KB. Sin `GenerateDataKey`, sin AES-GCM propio,
sin nonce. Ver `.claude/rules/serverless-secrets.md` y la decision 1 del
plan 02-auth-mfa.

El cliente boto3 se crea LAZY (igual que `shared.aws.dynamodb`): crearlo
en module scope lo ataria a las credenciales del import y rompe `moto`
en tests. Lazy + cache da el mismo beneficio en Lambda (el primer uso
ocurre en el cold start) y deja que `moto` intercepte la creacion.

Uso:
    from shared.aws import kms_encrypt, kms_decrypt

    ct = kms_encrypt(
        plaintext=secret_b32.encode('utf-8'),
        key_id='alias/portfolio-lambdas',
        encryption_context={'user_id': str(user.id), 'purpose': 'totp'},
    )
    secret = kms_decrypt(
        ciphertext=ct,
        encryption_context={'user_id': str(user.id), 'purpose': 'totp'},
    ).decode('utf-8')
"""

from __future__ import annotations

import os
from typing import Any

import boto3

from shared.core import ApplicationError


class KmsError(ApplicationError):
    """Fallo en una operacion KMS (Encrypt/Decrypt)."""


# Singleton cacheado. None hasta el primer uso (lazy, para moto en tests).
_kms_client: Any = None


def _client() -> Any:
    """Cliente KMS singleton (creado lazy en el primer uso)."""
    global _kms_client
    if _kms_client is None:
        region = os.environ.get('AWS_REGION', 'us-east-1')
        _kms_client = boto3.client('kms', region_name=region)
    return _kms_client


def reset_kms_cache() -> None:
    """Limpia el cliente cacheado. Solo para aislamiento entre tests."""
    global _kms_client
    _kms_client = None


def kms_encrypt(
    *,
    plaintext: bytes,
    key_id: str,
    encryption_context: dict[str, str],
) -> bytes:
    """Cifra `plaintext` con la CMK `key_id`. Retorna el ciphertext (BYTEA).

    `encryption_context` queda bindeado al ciphertext: el `kms_decrypt`
    debe pasar el MISMO context o falla con `InvalidCiphertextException`.
    Convencion del proyecto: `{'user_id': str(user.id), 'purpose': 'totp'}`.

    Raises:
        KmsError: si la llamada a KMS falla.
    """
    try:
        resp = _client().encrypt(
            KeyId=key_id,
            Plaintext=plaintext,
            EncryptionContext=encryption_context,
        )
    except Exception as exc:
        raise KmsError(f'kms_encrypt failed: {exc}') from exc
    return resp['CiphertextBlob']


def kms_decrypt(
    *,
    ciphertext: bytes,
    encryption_context: dict[str, str],
    key_id: str | None = None,
) -> bytes:
    """Descifra `ciphertext`. `encryption_context` DEBE matchear el del encrypt.

    El `key_id` es opcional (KMS lo deriva del ciphertext); pasarlo cuando
    se conoce es defensa en profundidad.

    Raises:
        KmsError: si la llamada a KMS falla (incluye context mismatch).
    """
    kwargs: dict[str, Any] = {
        'CiphertextBlob': ciphertext,
        'EncryptionContext': encryption_context,
    }
    if key_id is not None:
        kwargs['KeyId'] = key_id
    try:
        resp = _client().decrypt(**kwargs)
    except Exception as exc:
        raise KmsError(f'kms_decrypt failed: {exc}') from exc
    return resp['Plaintext']
