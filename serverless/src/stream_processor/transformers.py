"""@module transformers — DynamoDB Stream Records -> kwargs de los modelos ORM.

DynamoDB Stream entrega cada record con la imagen type-tagged
(`{"S": "x", "N": "1"}`). `deserialize_image` la aplana con el
`TypeDeserializer` de boto3; las funciones `parse_*` mapean ese dict plano a
los kwargs del constructor del modelo ORM correspondiente.

Conversiones de tipo (antes las hacia el SQL: `%(x)s::inet`, `to_timestamp`):
- `created_at` / `expires_at` -> `datetime` aware. `created_at` llega como
  string ISO; `expires_at` como epoch (segundos). El ORM exige objetos
  `datetime`, no strings ni ints — se convierten aqui.
- numericos (`viewport_*`) -> `int` (DynamoDB los entrega como `Decimal`).
- `ip` / `country` / `event_props` los adapta SQLAlchemy sola (INET/CHAR/JSONB).
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from boto3.dynamodb.types import TypeDeserializer

_deserializer = TypeDeserializer()


def _json_safe(value: Any) -> Any:
    """Convierte un valor a uno JSON-serializable, recursivamente.

    DynamoDB serializa TODO numero como `N`; el `TypeDeserializer` de boto3
    los devuelve como `Decimal`. `json.dumps` (lo que usa SQLAlchemy para la
    columna JSONB) no serializa `Decimal` — hay que bajarlos a `int`/`float`.
    """
    if isinstance(value, Decimal):
        # Entero exacto -> int; con parte fraccionaria -> float.
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def deserialize_image(image: dict[str, Any]) -> dict[str, Any]:
    """Aplana un Image type-tagged de DynamoDB a un dict Python plano.

    Args:
        image: dict tipo `{"name": {"S": "Pablo"}, "count": {"N": "5"}}`.

    Returns:
        Dict plano `{"name": "Pablo", "count": Decimal("5")}`.
    """
    if not image:
        return {}
    return {k: _deserializer.deserialize(v) for k, v in image.items()}


def _to_int(value: Any) -> int | None:
    """Convierte un valor (tipicamente `Decimal` de DynamoDB) a `int`."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_iso(value: Any) -> datetime | None:
    """Parsea un timestamp ISO 8601 a `datetime` aware (None si vacio)."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    # `fromisoformat` acepta el sufijo 'Z' desde Python 3.11.
    return datetime.fromisoformat(str(value))


def _epoch_to_datetime(value: Any) -> datetime | None:
    """Convierte un epoch en segundos a `datetime` aware UTC."""
    seconds = _to_int(value)
    if seconds is None:
        return None
    return datetime.fromtimestamp(seconds, tz=UTC)


def parse_contact_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """Mapea un Stream record de `contacts` a kwargs de `Contact`.

    Returns:
        Dict de kwargs para `Contact(**payload)`, o `None` si el record no
        es un INSERT (solo se replican los INSERT).
    """
    if record.get('eventName', '') != 'INSERT':
        return None

    image = deserialize_image(record['dynamodb'].get('NewImage', {}))
    if not image.get('id'):
        return None

    return {
        'id': str(image['id']),
        'stream_event_id': record.get('eventID', ''),
        'created_at': _parse_iso(image.get('created_at')),
        'name': image.get('name', ''),
        'email': image.get('email', ''),
        'message': image.get('message', ''),
        'company': image.get('company'),
        'role': image.get('role'),
        'service_type': image.get('service_type'),
        'budget': image.get('budget'),
        'timeline': image.get('timeline'),
        'niche': image.get('niche'),
        # session_id: clave de correlacion con tracking_events (SPEC-202).
        'session_id': image.get('session_id'),
        # ip/country/user_agent: columnas legacy — los contactos nuevos las
        # reciben NULL (el contact_form dejo de escribirlas en DynamoDB).
        'ip': None,
        'country': None,
        'user_agent': None,
    }


def parse_tracking_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """Mapea un Stream record de `tracking` a kwargs de `TrackingEvent`.

    Returns:
        Dict de kwargs para `TrackingEvent(**payload)`, o `None` si el record
        no es un INSERT (REMOVE por TTL no se replica).
    """
    if record.get('eventName', '') != 'INSERT':
        return None

    image = deserialize_image(record['dynamodb'].get('NewImage', {}))
    if not image.get('session_id') or not image.get('page_id'):
        return None

    return {
        'session_id': str(image['session_id']),
        'page_id': str(image['page_id']),
        'stream_event_id': record.get('eventID', ''),
        'created_at': _parse_iso(image.get('created_at')),
        'expires_at': _epoch_to_datetime(image.get('expires_at')),
        'page_url': image.get('page_url', ''),
        'page_title': image.get('page_title'),
        'page_path': image.get('page_path'),
        'referrer': image.get('referrer'),
        'utm_source': image.get('utm_source'),
        'utm_medium': image.get('utm_medium'),
        'utm_campaign': image.get('utm_campaign'),
        'utm_content': image.get('utm_content'),
        'utm_term': image.get('utm_term'),
        'viewport_width': _to_int(image.get('viewport_width')),
        'viewport_height': _to_int(image.get('viewport_height')),
        'niche': image.get('niche'),
        # Identificadores del evento (SPEC-102).
        'event_id': image.get('event_id'),
        'event_type_id': image.get('event_type_id'),
        # Datos especificos por tipo de evento (SPEC-200): el cliente lo
        # envia como dict; SQLAlchemy lo adapta a la columna JSONB.
        # `_json_safe` baja los Decimal de DynamoDB a int/float (json.dumps
        # no serializa Decimal).
        'event_props': _json_safe(image.get('event_props')),
        'ip': image.get('ip'),
        'country': image.get('country'),
        'user_agent': image.get('user_agent'),
        'browser': image.get('browser'),
        'browser_version': image.get('browser_version'),
        'os': image.get('os'),
        'device_type': image.get('device_type'),
    }


def detect_table(record: dict[str, Any]) -> str:
    """Detecta la tabla origen del record por su `eventSourceARN`.

    Returns:
        `'contacts'` | `'tracking'` | `'unknown'`.
    """
    arn = record.get('eventSourceARN', '')
    if 'portfolio-contacts-' in arn:
        return 'contacts'
    if 'portfolio-tracking-' in arn:
        return 'tracking'
    return 'unknown'
