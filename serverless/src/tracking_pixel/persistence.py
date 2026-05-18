"""Persistence del tracking event en DynamoDB con TTL 60d."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from typing import Any

import boto3

from common.ulid import new_uuidv7

# 60 dias en segundos
TTL_SECONDS = 60 * 24 * 60 * 60


def save_tracking_event(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Persiste un evento de tracking en DynamoDB con TTL +60d.

    PK: session_id, SK: page_id (UUIDv7).
    El TTL service de AWS borrara el item ~48h despues de expires_at
    sin consumir WCU.

    Args:
        payload: dict con campos validados + enrichment.

    Returns:
        Dict con `session_id` y `page_id` (ambos identifiers del item).
    """
    page_id = new_uuidv7()
    created_at = datetime.now(UTC).isoformat()
    expires_at = int(time.time()) + TTL_SECONDS

    region = os.environ.get('AWS_REGION', 'us-east-1')
    table_name = os.environ.get('TRACKING_TABLE_NAME', 'portfolio-tracking-dev')
    table = boto3.resource('dynamodb', region_name=region).Table(table_name)

    item: dict[str, Any] = {
        'session_id': payload['session_id'],
        'page_id': page_id,
        'created_at': created_at,
        'expires_at': expires_at,
        'page_url': payload['page_url'],
        # Identificadores del evento (SPEC-102): event_id da idempotencia,
        # event_type_id es el tipo del catalogo event_types.
        'event_id': payload['event_id'],
        'event_type_id': payload['event_type_id'],
    }

    # Campos opcionales (solo si tienen valor)
    for optional_field in (
        'page_title',
        'page_path',
        'referrer',
        'utm_source',
        'utm_medium',
        'utm_campaign',
        'utm_content',
        'utm_term',
        'niche',
    ):
        value = payload.get(optional_field)
        if value:
            item[optional_field] = value

    # Viewport (int, no string)
    for vp_field in ('viewport_width', 'viewport_height'):
        value = payload.get(vp_field)
        if value is not None:
            item[vp_field] = value

    # Metadata enrichment
    for meta_field in (
        'ip',
        'country',
        'user_agent',
        'browser',
        'browser_version',
        'os',
        'device_type',
    ):
        if payload.get(meta_field):
            item[meta_field] = payload[meta_field]

    # event_props (SPEC-200): datos especificos por tipo de evento. Se guarda
    # como atributo Map de DynamoDB. Nullable: solo si el cliente lo envio.
    event_props = payload.get('event_props')
    if event_props:
        item['event_props'] = event_props

    table.put_item(Item=item)

    return {
        'session_id': payload['session_id'],
        'page_id': page_id,
        'expires_at': expires_at,
    }
