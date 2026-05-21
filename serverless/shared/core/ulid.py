"""
UUIDv7 generator: identificadores ordenados lexicograficamente por tiempo.

UUIDv7 (RFC 9562, mayo 2024) incrusta un timestamp en milliseconds en los
bits altos del UUID, lo que produce IDs sorted naturally cuando se ordenan
como strings (lex sort = chronological sort). Esto es clave para DynamoDB
y PostgreSQL: pagination por PK ordena por orden de creacion sin necesidad
de una columna `created_at`.

PostgreSQL 18 tiene `uuidv7()` nativo (extension `uuid-ossp` no requerida).
En Lambda Python generamos el UUIDv7 antes de PutItem para que el ID este
disponible inmediatamente (no esperamos a la DB).

Formato:
    xxxxxxxx-xxxx-7xxx-yxxx-xxxxxxxxxxxx
                |    |
                version 7 marker
                     variant marker (RFC 4122: 0b10xx)
"""

from __future__ import annotations

import os
import time


def new_uuidv7() -> str:
    """
    Genera un UUIDv7 en formato canonical (hex con dashes, 36 chars).

    Implementacion manual (no usamos uuid stdlib porque Python 3.13 aun no
    tiene uuid7 nativo - llegara en 3.14). Spec: RFC 9562 seccion 5.7.

    Estructura (128 bits total):
    - 48 bits: timestamp en ms desde Unix epoch
    - 4 bits: version (0b0111 = 7)
    - 12 bits: random_a (entropia adicional, evita colision en mismo ms)
    - 2 bits: variant (0b10)
    - 62 bits: random_b

    Sortable property: si t1 < t2, entonces uuid7(t1) < uuid7(t2) lex.

    Returns:
        UUID v7 en formato '20240101...-7xxx-yxxx-...' (string)
    """
    # 48-bit Unix timestamp en milliseconds
    ts_ms = int(time.time() * 1000)
    if ts_ms < 0 or ts_ms >= (1 << 48):
        # Defensive: Unix epoch en ms cabe en 48 bits hasta el ano 10000
        msg = f'timestamp overflow: {ts_ms}'
        raise ValueError(msg)

    # 12 bits random (random_a)
    rand_a = int.from_bytes(os.urandom(2), 'big') & 0x0FFF

    # 62 bits random (random_b)
    rand_b = int.from_bytes(os.urandom(8), 'big') & ((1 << 62) - 1)

    # Construir los 128 bits
    # [ ts_ms (48) | ver (4) | rand_a (12) | var (2) | rand_b (62) ]
    uuid_int = ts_ms << 80
    uuid_int |= 0x7 << 76
    uuid_int |= rand_a << 64
    uuid_int |= 0b10 << 62
    uuid_int |= rand_b

    # Format como hex con dashes (RFC 4122 5.0)
    hex_str = f'{uuid_int:032x}'
    return f'{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}'
