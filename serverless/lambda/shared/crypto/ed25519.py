"""Primitivas Ed25519 (firma/verificacion) sobre `cryptography`.

Portador unico de `cryptography` para el backend (regla
`.claude/rules/lambda-shared-imports.md`). Encapsula las 3 operaciones
que el bypass de Turnstile necesita:

- `generate_keypair()`   -> (private_b64, public_b64) — lo usa devtools
  en el keygen (NO el Lambda).
- `sign_message(...)`    -> firma de un mensaje — lo usa tests/shared
  para emitir el token (NO el Lambda).
- `verify_signature(...)` -> bool — lo usa el Lambda al verificar el
  token de bypass.

Las claves viajan como base64 (urlsafe, sin padding) de los 32 bytes raw
Ed25519 (`Ed25519PrivateKey` / `Ed25519PublicKey`).

`cryptography` se importa de forma LAZY dentro de cada funcion: el modulo
se puede importar sin pagar el costo de import de la lib nativa. En los
Lambdas, solo el path de bypass (dev, cf_response vacio) ejercita
estas funciones, asi que prod nunca carga `cryptography` por este modulo.
"""

from __future__ import annotations

import base64


def _b64url_encode(raw: bytes) -> str:
    """Codifica bytes a base64 urlsafe SIN padding."""
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def _b64url_decode(value: str) -> bytes:
    """Decodifica base64 urlsafe SIN padding. Lanza ValueError si invalido."""
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def generate_keypair() -> tuple[str, str]:
    """Genera un par Ed25519 nuevo.

    Returns:
        Tupla `(private_key_b64, public_key_b64)` con los 32 bytes raw de
        cada clave en base64 urlsafe sin padding. La privada NUNCA debe
        loguearse ni salir del entorno local (`dev-cli`).
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _b64url_encode(private_raw), _b64url_encode(public_raw)


def sign_message(private_key_b64: str, message: bytes) -> bytes:
    """Firma `message` con la clave privada Ed25519 (raw, base64).

    Args:
        private_key_b64: 32 bytes raw de la privada en base64 urlsafe.
        message: bytes a firmar.

    Returns:
        La firma (64 bytes).
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    private_key = Ed25519PrivateKey.from_private_bytes(
        _b64url_decode(private_key_b64),
    )
    return private_key.sign(message)


def verify_signature(
    public_key_b64: str,
    message: bytes,
    signature: bytes,
) -> bool:
    """Verifica la firma Ed25519 de `message` con la clave publica.

    Args:
        public_key_b64: 32 bytes raw de la publica en base64 urlsafe.
        message: bytes que se firmaron.
        signature: firma a verificar (64 bytes).

    Returns:
        True si la firma es valida. False ante CUALQUIER fallo (firma
        invalida, clave malformada, longitud incorrecta). NUNCA propaga
        excepcion: el caller decide el error de dominio.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey,
    )

    try:
        public_key = Ed25519PublicKey.from_public_bytes(
            _b64url_decode(public_key_b64),
        )
        public_key.verify(signature, message)
    except (InvalidSignature, ValueError):
        return False
    return True
