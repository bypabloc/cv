"""Recovery codes de MFA: generacion, hash y comparacion.

10 codes de 10 chars en alfabeto Crockford-like (sin O/0/I/1/L) para
evitar ambiguedad al transcribir. Se muestran UNA sola vez al usuario
(response de `mfa.recovery-codes-generate`); el backend solo guarda el
hash SHA-256 en `auth_mfa_recovery_codes`. Espacio: 30^10 ~ 5.9x10^14.

Portador del CSPRNG (`secrets`) y del hash (`hashlib`) — ambos stdlib;
vive aqui por cohesion del dominio auth.
"""

from __future__ import annotations

import hashlib
import secrets

RECOVERY_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
RECOVERY_CODE_LENGTH = 10
RECOVERY_CODE_COUNT = 10


def generate_recovery_codes() -> list[str]:
    """10 codes de 10 chars sin O/0/I/1/L (CSPRNG via `secrets.choice`)."""
    return [
        ''.join(
            secrets.choice(RECOVERY_CODE_ALPHABET)
            for _ in range(RECOVERY_CODE_LENGTH)
        )
        for _ in range(RECOVERY_CODE_COUNT)
    ]


def hash_recovery_code(code: str) -> bytes:
    """SHA-256 del code (espacio 30^10 hace innecesario un KDF lento)."""
    return hashlib.sha256(code.encode('utf-8')).digest()


def compare_recovery_code(*, code: str, stored_hash: bytes) -> bool:
    """Comparacion constant-time del hash del code contra el guardado."""
    return secrets.compare_digest(hash_recovery_code(code), stored_hash)
