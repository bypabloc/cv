"""Builders de eventos DynamoDB Stream para los tests de integracion.

Prefijo `_` en la carpeta para que pytest NO recolecte estos archivos
como tests. Extiende los builders de `tests/unit/_helpers.py` con los
escenarios que la suite de integracion necesita: MODIFY/REMOVE,
records sin `eventID`, tabla desconocida, payload que falla al insertar
y `event_props` como dict libre (JSONB).
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

_CONTACTS_ARN = (
    'arn:aws:dynamodb:us-east-1:123:table/portfolio-contacts-dev/stream/x'
)
_TRACKING_ARN = (
    'arn:aws:dynamodb:us-east-1:123:table/portfolio-tracking-dev/stream/x'
)
_UNKNOWN_ARN = 'arn:aws:dynamodb:us-east-1:123:table/other-table/stream/x'

# UUID v7 fijo para `page_id` (columna UUID del modelo TrackingEvent).
_PAGE_ID = '019e372b-e0a7-7154-8279-8829bcf6a08c'

# Namespace para derivar UUIDs deterministas a partir de un event_id.
_UUID_NS = uuid.UUID('00000000-0000-0000-0000-000000000000')


def contact_id(event_id: str) -> str:
    """Deriva el `Contact.id` (UUID) determinista de un `event_id`.

    La columna `contacts.id` es de tipo `UUID`: el item de DynamoDB lleva
    un UUID v7 real. El builder genera uno determinista por `event_id`
    para que el test pueda recomputar el mismo valor en el assert.
    """
    return str(uuid.uuid5(_UUID_NS, event_id))


def lambda_context() -> MagicMock:
    """Devuelve un Lambda context falso valido para Powertools.

    `logger.inject_lambda_context` lee `function_name`,
    `memory_limit_in_mb`, `invoked_function_arn` y `aws_request_id`.
    """
    ctx = MagicMock()
    ctx.function_name = 'portfolio-stream-processor-test'
    ctx.memory_limit_in_mb = 512
    ctx.invoked_function_arn = (
        'arn:aws:lambda:us-east-1:000000000000:function:'
        'portfolio-stream-processor-test'
    )
    ctx.aws_request_id = 'test-request-id'
    return ctx


def contact_record(event_id: str) -> dict[str, Any]:
    """Construye un Stream record INSERT de la tabla `contacts`."""
    return {
        'eventID': event_id,
        'eventName': 'INSERT',
        'eventSourceARN': _CONTACTS_ARN,
        'dynamodb': {
            'NewImage': {
                'id': {'S': contact_id(event_id)},
                'name': {'S': 'Pablo'},
                'email': {'S': 'p@example.com'},
                'message': {'S': 'hola'},
                'company': {'S': 'Acme'},
                'created_at': {'S': '2026-05-17T00:00:00Z'},
                'session_id': {'S': f'sess-{event_id}'},
            },
        },
    }


def tracking_record(
    event_id: str,
    *,
    event_props: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construye un Stream record INSERT de la tabla `tracking`.

    Si se pasa `event_props`, se serializa al formato type-tagged de
    DynamoDB (`M` para mapa, `N` para numero, `S` para string) para
    ejercitar la columna JSONB.
    """
    new_image: dict[str, Any] = {
        'session_id': {'S': f'sess-{event_id}'},
        'page_id': {'S': _PAGE_ID},
        'page_url': {'S': 'https://the-full-stack.com/'},
        'page_title': {'S': 'Home'},
        'created_at': {'S': '2026-05-17T00:00:00Z'},
        'expires_at': {'N': '1755388800'},
        'niche': {'S': 'generic'},
        'viewport_width': {'N': '1920'},
    }
    if event_props is not None:
        new_image['event_props'] = _to_dynamodb_value(event_props)
    return {
        'eventID': event_id,
        'eventName': 'INSERT',
        'eventSourceARN': _TRACKING_ARN,
        'dynamodb': {'NewImage': new_image},
    }


def contact_record_without_event_id() -> dict[str, Any]:
    """Construye un record de `contacts` sin `eventID` (debe saltearse)."""
    record = contact_record('placeholder')
    del record['eventID']
    return record


def modify_record(event_id: str) -> dict[str, Any]:
    """Construye un record MODIFY de `contacts` (no se replica)."""
    record = contact_record(event_id)
    record['eventName'] = 'MODIFY'
    return record


def remove_record(event_id: str) -> dict[str, Any]:
    """Construye un record REMOVE de `tracking` (TTL; no se replica)."""
    record = tracking_record(event_id)
    record['eventName'] = 'REMOVE'
    return record


def unknown_table_record(event_id: str) -> dict[str, Any]:
    """Construye un record cuyo ARN no es contacts ni tracking."""
    record = contact_record(event_id)
    record['eventSourceARN'] = _UNKNOWN_ARN
    return record


def invalid_contact_record(event_id: str) -> dict[str, Any]:
    """Construye un record de `contacts` con `created_at` malformado.

    El parser `_parse_iso` invoca `datetime.fromisoformat`: un string que
    no es ISO 8601 lanza `ValueError`, lo que hace fallar `process_record`
    y dispara el reporte en `batchItemFailures`.
    """
    record = contact_record(event_id)
    record['dynamodb']['NewImage']['created_at'] = {'S': 'no-es-una-fecha'}
    return record


def stream_event(*records: dict[str, Any]) -> dict[str, Any]:
    """Construye el evento DynamoDB Stream `{Records: [...]}`."""
    return {'Records': list(records)}


def _to_dynamodb_value(value: Any) -> dict[str, Any]:
    """Serializa un valor Python al formato type-tagged de DynamoDB."""
    if isinstance(value, bool):
        return {'BOOL': value}
    if isinstance(value, (int, float)):
        return {'N': str(value)}
    if isinstance(value, str):
        return {'S': value}
    if isinstance(value, dict):
        return {'M': {k: _to_dynamodb_value(v) for k, v in value.items()}}
    if isinstance(value, list):
        return {'L': [_to_dynamodb_value(v) for v in value]}
    raise TypeError(f'tipo no soportado en el builder: {type(value)}')
