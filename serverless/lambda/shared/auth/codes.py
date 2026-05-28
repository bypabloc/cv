"""Generador de codigos numericos cortos para email verification.

Codigos de 8 chars con alfabeto Crockford-like (sin O/0/I/1/L). Solo
CSPRNG (`secrets.choice`). Comparacion timing-safe via
`secrets.compare_digest` sobre el hash SHA-256 — el codigo NUNCA se
guarda en plain text en Neon (columna `auth_email_codes.code_hash` es
BYTEA).
"""

import hashlib
import secrets

from shared.auth.constants import CODE_ALPHABET, CODE_LENGTH

__all__ = [
    'CODE_ALPHABET',
    'CODE_LENGTH',
    'compare_code',
    'generate_code',
    'hash_code',
]


def generate_code() -> str:
    """Genera un codigo de `CODE_LENGTH` chars del `CODE_ALPHABET`.

    Usa `secrets.choice` (CSPRNG). Cada char es uniformemente aleatorio
    en el alfabeto Crockford-like (30 simbolos, sin confundibles).
    Espacio total = 30^8 ~ 6.5x10^11.
    """
    return ''.join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def hash_code(code: str) -> bytes:
    """SHA-256 del codigo (32 bytes).

    El hash es lo que se guarda en `auth_email_codes.code_hash` (BYTEA).
    Codigos cortos como `ABCDEF23` necesitan hash para resistir lecturas
    no autorizadas del dump de la DB. NO se usa salt — los codigos son
    efimeros (TTL 15 min) y no se reusan.
    """
    return hashlib.sha256(code.encode('utf-8')).digest()


def compare_code(*, code: str, stored_hash: bytes) -> bool:
    """Compara `hash_code(code) == stored_hash` en tiempo constante.

    `secrets.compare_digest` evita timing attacks: el tiempo de
    ejecucion no depende del numero de bytes que coinciden.
    """
    return secrets.compare_digest(hash_code(code), stored_hash)
