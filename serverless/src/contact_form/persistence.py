"""Persistence de contacts en DynamoDB."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import boto3

from _shared.ulid import new_uuidv7


def save_contact(payload: dict[str, Any]) -> dict[str, str]:
    """
    Persiste un contact submission en DynamoDB.

    Args:
        payload: dict con campos validados del form.

    Returns:
        Dict con `contact_id` y `created_at` ISO 8601.
    """
    contact_id = new_uuidv7()
    created_at = datetime.now(UTC).isoformat()

    region = os.environ.get('AWS_REGION', 'us-east-1')
    table_name = os.environ.get('CONTACTS_TABLE_NAME', 'portfolio-contacts-dev')
    table = boto3.resource('dynamodb', region_name=region).Table(table_name)

    item: dict[str, Any] = {
        'id': contact_id,
        'created_at': created_at,
        'name': payload['name'],
        'email': payload['email'],
        'message': payload['message'],
    }
    # Campos opcionales: solo agregar si tienen valor (DynamoDB no permite
    # empty strings). session_id enlaza el contacto con tracking_events; el
    # origen (ip/country/user_agent) ya no se duplica aqui - se consulta en
    # tracking via JOIN por session_id.
    for optional_field in (
        'company', 'role', 'service_type', 'budget', 'timeline', 'niche',
        'session_id',
    ):
        value = payload.get(optional_field)
        if value:
            item[optional_field] = value

    table.put_item(Item=item)

    return {'contact_id': contact_id, 'created_at': created_at}
