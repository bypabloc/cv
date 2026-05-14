"""
Serializers: convierte valores Python a string para DynamoDB y viceversa.

Estrategia:
- Si el valor es JSON-serializable (dict, list, str, int, float, bool, None):
  encoding='json', value=json.dumps(value)
- Si es bytes:
  encoding='bytes_b64', value=base64.b64encode(value).decode()

Decision: NO usar pickle (CVE risk + version-coupled). Mantener serializacion
solo en tipos primitivos + bytes. Si el usuario necesita serializar objetos
complejos, debe hacerlo el mismo antes de cache.set().
"""

from __future__ import annotations

import base64
import json
from typing import Any

from common.cache.types import CacheEntry


class SerializationError(ValueError):
    """Raised cuando un valor no es serializable o decode falla."""


def serialize(value: Any) -> tuple[str, str]:
    """
    Serializa value a (string_value, encoding).

    Args:
        value: cualquier Python type JSON-serializable o bytes.

    Returns:
        Tuple (string serializado, encoding marker).

    Raises:
        SerializationError: si value no es serializable.
    """
    if isinstance(value, bytes):
        return base64.b64encode(value).decode('ascii'), 'bytes_b64'

    try:
        return json.dumps(value, ensure_ascii=False, separators=(',', ':')), 'json'
    except (TypeError, ValueError) as e:
        msg = f'Cannot serialize type {type(value).__name__}: {e}'
        raise SerializationError(msg) from e


def deserialize(value: str, encoding: str) -> Any:
    """
    Deserializa string + encoding al value Python original.

    Args:
        value: string crudo de DynamoDB.
        encoding: marker 'json' | 'bytes_b64'.

    Returns:
        Valor Python deserializado.

    Raises:
        SerializationError: encoding desconocido o decode falla.
    """
    if encoding == 'json':
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            msg = f'Invalid JSON: {e}'
            raise SerializationError(msg) from e

    if encoding == 'bytes_b64':
        try:
            return base64.b64decode(value, validate=True)
        except (ValueError, TypeError) as e:
            msg = f'Invalid base64: {e}'
            raise SerializationError(msg) from e

    msg = f'Unknown encoding: {encoding!r}'
    raise SerializationError(msg)


def serialize_entry(entry: CacheEntry) -> dict[str, Any]:
    """
    Serializa CacheEntry a dict ready para DynamoDB put_item.

    Solo limpia keys opcionales None.
    """
    return {k: v for k, v in entry.items() if v is not None}
