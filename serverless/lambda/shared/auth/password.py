"""Password hashing con argon2id (defaults de argon2-cffi).

argon2id es el ganador de PHC y el algoritmo recomendado por OWASP 2024.
Defaults de `argon2.PasswordHasher()`:
    time_cost=3, memory_cost=64MiB, parallelism=4, hash_len=32, salt_len=16.

El hash incluye salt + parametros embebidos en el formato
`$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>`. Eso permite cambiar los
parametros sin migracion: verify levanta `NeedsRehashError` y el caller
re-hashea con los parametros actuales.
"""

from typing import Final

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from shared.core import ApplicationError

__all__ = [
    'NeedsRehashError',
    'PasswordError',
    'hash_password',
    'verify_password',
]


_HASHER: Final[PasswordHasher] = PasswordHasher()


class PasswordError(ApplicationError):
    """Base de errores de password (mismatch, hash invalido, rehash)."""

    default_code = 'PASSWORD_ERROR'
    status_code = 400


class NeedsRehashError(PasswordError):
    """La password coincide pero los parametros del hash son antiguos.

    El caller debe re-hashear con `hash_password(password)` y persistir
    el nuevo hash. NO es un error de seguridad — el usuario ya pasa la
    verificacion. Es una senial para mantener la base actualizada.
    """

    default_code = 'PASSWORD_NEEDS_REHASH'
    status_code = 200


def hash_password(password: str) -> str:
    """Hashea con argon2id (defaults).

    Retorna el hash en formato `$argon2id$...$` listo para guardar en
    `auth_credentials.password_hash` (TEXT).
    """
    return _HASHER.hash(password)


def verify_password(*, password: str, hashed: str) -> bool:
    """Verifica password contra hash en formato argon2.

    Returns:
        True si la password coincide.
        False si la password NO coincide.

    Raises:
        NeedsRehashError: si la password coincide pero los parametros
            del hash difieren de los actuales (re-hash recomendado).
        PasswordError: si el `hashed` no es un argon2 valido.
    """
    try:
        _HASHER.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except (InvalidHashError, VerificationError) as exc:
        msg = 'Hash invalido o corrupto'
        raise PasswordError(msg, code='INVALID_HASH') from exc

    if _HASHER.check_needs_rehash(hashed):
        msg = 'Hash con parametros antiguos; rehash recomendado'
        raise NeedsRehashError(msg, code='PASSWORD_NEEDS_REHASH')
    return True
