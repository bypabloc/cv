"""TOTP service: genera/cifra el secret y verifica codes.

Envuelve `shared.auth.totp` (pyotp) + `shared.aws.kms` (CMK directa). El
secret se cifra con `kms:Encrypt` (`EncryptionContext={user_id,
purpose:totp}`) antes de persistir y se descifra con `kms:Decrypt` en
cada verify (cacheable a futuro; decision 1 del plan).

NUNCA loggea el secret (ni el b32 plaintext ni el resultado del decrypt).
"""

from __future__ import annotations

from uuid import UUID

from shared.auth import (
    build_otpauth_url,
    generate_totp_secret_b32,
    verify_totp_code,
)
from shared.aws import kms_decrypt, kms_encrypt


class TotpService:
    """Wrapper de pyotp + cifrado KMS del secret TOTP."""

    def __init__(self, app_config: object) -> None:
        self.app_config = app_config

    def _context(self, user_id: UUID | str) -> dict[str, str]:
        return {'user_id': str(user_id), 'purpose': 'totp'}

    def generate_secret(self) -> str:
        """Genera un secret base32 (160 bits)."""
        return generate_totp_secret_b32()

    def encrypt_secret(self, *, secret_b32: str, user_id: UUID | str) -> bytes:
        """Cifra el secret con la CMK directa (EncryptionContext del user)."""
        return kms_encrypt(
            plaintext=secret_b32.encode('utf-8'),
            key_id=self.app_config.kms_totp_key_id,  # type: ignore[attr-defined]
            encryption_context=self._context(user_id),
        )

    def otpauth_url(self, *, secret_b32: str, email: str) -> str:
        """URL otpauth:// para que el frontend renderice el QR."""
        return build_otpauth_url(
            secret_b32=secret_b32,
            account_email=email,
            issuer='the-full-stack.com',
        )

    def verify(
        self,
        *,
        user_id: UUID | str,
        ciphertext: bytes,
        code: str,
    ) -> bool:
        """Descifra el secret del user y verifica el code de 6 digitos."""
        secret_b32 = kms_decrypt(
            ciphertext=ciphertext,
            encryption_context=self._context(user_id),
        ).decode('utf-8')
        return verify_totp_code(secret_b32=secret_b32, code=code)
