"""Constantes del subpaquete shared.auth.

JWT_ALGORITHM y los TTLs viven aqui para que el codigo de jwt/codes/
tokens los importe sin acoplarse al modulo concreto. Cambiar un valor
aqui (ej. CODE_LENGTH) propaga al generador, al validator y a los tests.
"""

from typing import Final

# --- JWT ---
JWT_ALGORITHM: Final[str] = 'HS256'
TEMP_TTL: Final[int] = 300  # 5 min  (rolling refresh entre pasos)
ACCESS_TTL: Final[int] = 900  # 15 min (stateless, blacklisteable)
REFRESH_TTL: Final[int] = 30 * 24 * 3600  # 30 dias (rotation + family_id)
DEFAULT_ISSUER: Final[str] = 'portfolio-auth'
DEFAULT_AUDIENCE: Final[str] = 'portfolio'

# --- Codes ---
# Alfabeto Crockford-like: A-Z + 0-9 SIN los confundibles `O/0/I/1/L`.
# 30 chars, 8 posiciones -> espacio = 30^8 ~ 6.5x10^11. Con 5 intentos
# max el brute force es inviable.
CODE_ALPHABET: Final[str] = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
CODE_LENGTH: Final[int] = 8
CODE_PATTERN: Final[str] = r'^[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{8}$'

# --- Magic-link tokens ---
TOKEN_BYTES: Final[int] = 32  # secrets.token_urlsafe(32) -> ~43 chars b64url
