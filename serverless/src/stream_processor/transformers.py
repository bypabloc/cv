"""
Transforma DynamoDB Stream Records al shape de Neon PostgreSQL.

DynamoDB Stream entrega records como:
    {
      "eventID": "abc123...",
      "eventName": "INSERT" | "MODIFY" | "REMOVE",
      "dynamodb": {
        "Keys": {...},
        "NewImage": {...},   // type-tagged values: {"S": "x", "N": "1"}
        "OldImage": {...}
      }
    }

Convertimos NewImage a un dict Python plano usando boto3 TypeDeserializer.
"""

from __future__ import annotations

from typing import Any

from boto3.dynamodb.types import TypeDeserializer

_deserializer = TypeDeserializer()


def deserialize_image(image: dict[str, Any]) -> dict[str, Any]:
    """
    Convierte un Image type-tagged a dict Python plano.

    Args:
        image: dict tipo {"name": {"S": "Pablo"}, "count": {"N": "5"}}.

    Returns:
        Dict plano {"name": "Pablo", "count": Decimal("5")}.
    """
    if not image:
        return {}
    return {k: _deserializer.deserialize(v) for k, v in image.items()}


def parse_contact_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse Stream record de la tabla contacts.

    Args:
        record: Stream record dict.

    Returns:
        Dict listo para INSERT en Neon.contacts, o None si MODIFY/REMOVE.
    """
    event_name = record.get('eventName', '')
    if event_name != 'INSERT':
        # Solo procesamos INSERT (MODIFY raramente ocurre en este patron;
        # REMOVE no aplica para contacts - no tienen TTL)
        return None

    image = deserialize_image(record['dynamodb'].get('NewImage', {}))
    if not image.get('id'):
        return None

    return {
        'id': str(image['id']),
        'stream_event_id': record.get('eventID', ''),
        'created_at': image.get('created_at'),
        'name': image.get('name', ''),
        'email': image.get('email', ''),
        'message': image.get('message', ''),
        'company': image.get('company'),
        'role': image.get('role'),
        'service_type': image.get('service_type'),
        'budget': image.get('budget'),
        'timeline': image.get('timeline'),
        'niche': image.get('niche'),
        'ip': image.get('ip'),
        'country': image.get('country'),
        'user_agent': image.get('user_agent'),
    }


def parse_tracking_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse Stream record de la tabla tracking.

    REMOVE (TTL fired) -> None (no procesamos, la particion mensual se drop).
    """
    event_name = record.get('eventName', '')
    if event_name != 'INSERT':
        return None

    image = deserialize_image(record['dynamodb'].get('NewImage', {}))
    if not image.get('session_id') or not image.get('page_id'):
        return None

    # Convertir Decimal a int para campos numericos
    def _to_int(v: Any) -> int | None:
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    return {
        'session_id': str(image['session_id']),
        'page_id': str(image['page_id']),
        'stream_event_id': record.get('eventID', ''),
        'created_at': image.get('created_at'),
        'expires_at': _to_int(image.get('expires_at')),
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
        # Identificadores del evento (SPEC-102)
        'event_id': image.get('event_id'),
        'event_type_id': image.get('event_type_id'),
        'ip': image.get('ip'),
        'country': image.get('country'),
        'user_agent': image.get('user_agent'),
        'browser': image.get('browser'),
        'browser_version': image.get('browser_version'),
        'os': image.get('os'),
        'device_type': image.get('device_type'),
    }


def detect_table(record: dict[str, Any]) -> str:
    """
    Detecta si el record es de contacts o tracking basado en source ARN.

    El eventSourceARN contiene el nombre de la tabla.

    Returns:
        'contacts' | 'tracking' | 'unknown'
    """
    arn = record.get('eventSourceARN', '')
    if 'portfolio-contacts-' in arn:
        return 'contacts'
    if 'portfolio-tracking-' in arn:
        return 'tracking'
    return 'unknown'
