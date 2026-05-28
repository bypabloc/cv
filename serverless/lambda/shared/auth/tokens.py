"""Generador de tokens opacos para magic-links.

Un magic-link es un secreto de proposito unico (single-use, TTL 15 min).
NO es un JWT — eso permitiria a un atacante con el JWT_SECRET firmar
magic-links arbitrarios. Aqui se usa `secrets.token_urlsafe` (CSPRNG) y
se guarda solo el hash SHA-256 en Neon (`auth_magic_links.token_hash`,
BYTEA UNIQUE).
"""

import hashlib
import secrets

from shared.auth.constants import TOKEN_BYTES

__all__ = [
    'compare_token',
    'generate_opaque_token',
    'hash_token',
]


def generate_opaque_token(num_bytes: int = TOKEN_BYTES) -> str:
    """Token opaco url-safe.

    `secrets.token_urlsafe(32)` produce ~43 chars en base64-url-safe
    sin padding (sin `+`, `/`, `=`). Soporta query strings y fragments
    sin encoding adicional.
    """
    return secrets.token_urlsafe(num_bytes)


def hash_token(token: str) -> bytes:
    """SHA-256 del token (32 bytes). Guardado en `auth_magic_links.token_hash`."""
    return hashlib.sha256(token.encode('utf-8')).digest()


def compare_token(*, token: str, stored_hash: bytes) -> bool:
    """Compara `hash_token(token) == stored_hash` en tiempo constante."""
    return secrets.compare_digest(hash_token(token), stored_hash)
