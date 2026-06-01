"""TOTP (RFC 6238) wrappers sobre `pyotp`.

Portador unico de `pyotp` para el backend (regla
`.claude/rules/lambda-shared-imports.md`). El secret se genera en
plaintext aqui; el cifrado at-rest lo hace KMS (CMK directa) en
`shared.aws.kms` — `shared.auth.totp` NO conoce KMS.

El QR lo renderiza el FRONTEND desde el `otpauth_url` (decision 8 del
plan 02): el backend NO devuelve SVG. Por eso no hay dep `segno`.
"""

from __future__ import annotations

import pyotp

from shared.core.exceptions import ApplicationError


class TotpError(ApplicationError):
    """Fallo en una operacion TOTP."""


def generate_totp_secret_b32() -> str:
    """20 bytes random codificados en base32 (160 bits, RFC 6238)."""
    return pyotp.random_base32()  # 32 chars base32 = 160 bits


def build_otpauth_url(
    *,
    secret_b32: str,
    account_email: str,
    issuer: str = 'the-full-stack.com',
) -> str:
    """RFC 6238 `otpauth://` URL para el QR del frontend.

    Compatible con Google Authenticator / Authy / 1Password. El label
    queda `<issuer>:<email>` y el `issuer` se repite como query param.
    """
    return pyotp.TOTP(secret_b32).provisioning_uri(
        name=account_email,
        issuer_name=issuer,
    )


def verify_totp_code(
    *,
    secret_b32: str,
    code: str,
    valid_window: int = 1,
) -> bool:
    """Verifica un code TOTP de 6 digitos.

    `valid_window=1` acepta el code actual + el anterior + el siguiente
    (cubre clock drift de hasta 30s en cada direccion).
    """
    return pyotp.TOTP(secret_b32).verify(code, valid_window=valid_window)
