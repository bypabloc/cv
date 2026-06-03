"""Generador TOTP (RFC 6238) con stdlib, para el harness E2E.

El Lambda `auth` usa `pyotp` (6 digitos, periodo 30s, HMAC-SHA1, secret
base32). El harness NO depende de `pyotp`: implementa el mismo algoritmo
con `hmac`/`hashlib`/`base64` para generar el code que confirma el setup
TOTP y completa el login con MFA. NO es un secreto (el secret_b32 lo
devuelve el backend en `setup-totp`).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time


_PERIOD = 30
_DIGITS = 6


def totp_now(secret_b32: str, *, at: int | None = None) -> str:
    """Code TOTP de 6 digitos para `secret_b32` en el instante `at`.

    `at` en segundos epoch (default: ahora). Algoritmo RFC 6238 estandar
    (HMAC-SHA1, periodo 30s), compatible con el `pyotp.TOTP` del backend.
    """
    now = at if at is not None else int(time.time())
    counter = now // _PERIOD
    # base32 sin padding-strict: pyotp genera secrets de 32 chars (160
    # bits) que ya son multiplo de 8; agregamos padding por robustez.
    padded = secret_b32 + '=' * (-len(secret_b32) % 8)
    key = base64.b32decode(padded, casefold=True)
    msg = struct.pack('>Q', counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack('>I', digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(binary % (10**_DIGITS)).zfill(_DIGITS)
