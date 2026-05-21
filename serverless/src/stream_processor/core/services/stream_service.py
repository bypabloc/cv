"""Service de la operacion `stream`: replica DynamoDB Streams a Neon.

Concentra la logica de negocio del Lambda `stream_processor`:

- transformacion de un Stream Record (imagen type-tagged de DynamoDB) a
  los kwargs del modelo ORM correspondiente (`Contact` / `TrackingEvent`);
- escritura ORM en Neon mas la fila de idempotencia
  (`processed_stream_events`), en una unica transaccion por record.

Regla de separacion:
  - controllers/stream/process.py : orquesta (valida -> service -> normaliza).
  - services/stream_service.py     : logica de negocio (este archivo).
  - utils/                         : infraestructura generica.

El service NO conoce el evento Lambda ni la respuesta del handler:
recibe un Record (dict) y devuelve el resultado del procesamiento.

Idempotencia: cada Stream record trae un `eventID` unico. Antes de
insertar se verifica en `processed_stream_events`; el INSERT del dato +
su fila de idempotencia confirman en la MISMA transaccion (via
`db_session`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from boto3.dynamodb.types import TypeDeserializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from settings.config import logger
from shared.db.models import Contact, ProcessedStreamEvent, TrackingEvent
from shared.db.session import db_session

_deserializer = TypeDeserializer()


# --------------------------------------------------------------------------
# Transformacion: Stream Record -> kwargs del modelo ORM
# --------------------------------------------------------------------------


def _json_safe(value: Any) -> Any:
    """Convierte un valor a uno JSON-serializable, recursivamente.

    DynamoDB serializa TODO numero como `N`; el `TypeDeserializer` de
    boto3 los devuelve como `Decimal`. `json.dumps` (lo que usa
    SQLAlchemy para la columna JSONB) no serializa `Decimal` — hay que
    bajarlos a `int`/`float`.
    """
    if isinstance(value, Decimal):
        # Entero exacto -> int; con parte fraccionaria -> float.
        return (
            int(value)
            if value == value.to_integral_value()
            else float(value)
        )
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def deserialize_image(image: dict[str, Any]) -> dict[str, Any]:
    """Aplana un Image type-tagged de DynamoDB a un dict Python plano.

    Parameters
    ----------
    image : dict[str, Any]
        Dict tipo `{"name": {"S": "Pablo"}, "count": {"N": "5"}}`.

    Returns
    -------
    dict[str, Any]
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


def parse_contact_record(
    record: dict[str, Any],
) -> dict[str, Any] | None:
    """Mapea un Stream record de `contacts` a kwargs de `Contact`.

    Parameters
    ----------
    record : dict[str, Any]
        Stream record de DynamoDB.

    Returns
    -------
    dict[str, Any] | None
        Dict de kwargs para `Contact(**payload)`, o `None` si el record
        no es un INSERT (solo se replican los INSERT).
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
        # ip/country/user_agent: columnas legacy — los contactos nuevos
        # las reciben NULL (el contact_form dejo de escribirlas en
        # DynamoDB).
        'ip': None,
        'country': None,
        'user_agent': None,
    }


def parse_tracking_record(
    record: dict[str, Any],
) -> dict[str, Any] | None:
    """Mapea un Stream record de `tracking` a kwargs de `TrackingEvent`.

    Parameters
    ----------
    record : dict[str, Any]
        Stream record de DynamoDB.

    Returns
    -------
    dict[str, Any] | None
        Dict de kwargs para `TrackingEvent(**payload)`, o `None` si el
        record no es un INSERT (REMOVE por TTL no se replica).
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
        # `_json_safe` baja los Decimal de DynamoDB a int/float
        # (json.dumps no serializa Decimal).
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

    Parameters
    ----------
    record : dict[str, Any]
        Stream record de DynamoDB.

    Returns
    -------
    str
        `'contacts'` | `'tracking'` | `'unknown'`.
    """
    arn = record.get('eventSourceARN', '')
    if 'portfolio-contacts-' in arn:
        return 'contacts'
    if 'portfolio-tracking-' in arn:
        return 'tracking'
    return 'unknown'


# --------------------------------------------------------------------------
# Escritura ORM en Neon
# --------------------------------------------------------------------------


def is_event_processed(session: Session, event_id: str) -> bool:
    """`True` si el `event_id` ya esta en `processed_stream_events`."""
    stmt = select(ProcessedStreamEvent.event_id).where(
        ProcessedStreamEvent.event_id == event_id,
    )
    return session.execute(stmt).first() is not None


def mark_event_processed(
    session: Session,
    event_id: str,
    *,
    event_type: str,
    table_name: str,
) -> None:
    """Registra el `event_id` como procesado (fila de idempotencia).

    Se llama dentro de la misma Session/transaccion que el INSERT del
    contacto/evento — ambos confirman juntos o ninguno.
    """
    session.add(
        ProcessedStreamEvent(
            event_id=event_id,
            event_type=event_type,
            table_name=table_name,
        ),
    )


def insert_contact(session: Session, payload: dict[str, Any]) -> None:
    """Inserta una fila en `contacts` desde el payload del transformer.

    `session_id` enlaza el contacto con `tracking_events` (correlacion
    via JOIN). `ip`/`country`/`user_agent` son columnas legacy: los
    contactos nuevos las reciben en NULL.
    """
    session.add(Contact(**payload))


def insert_tracking(session: Session, payload: dict[str, Any]) -> None:
    """Inserta una fila en `tracking_events` desde el payload.

    `event_props` es un dict plano: SQLAlchemy lo adapta a JSONB sin
    envoltura manual.
    """
    session.add(TrackingEvent(**payload))


# --------------------------------------------------------------------------
# Procesamiento de un record (logica de negocio principal)
# --------------------------------------------------------------------------


def process_record(record: dict[str, Any], event_id: str) -> str:
    """Procesa un record del Stream dentro de su propia transaccion.

    Parameters
    ----------
    record : dict[str, Any]
        Stream record de DynamoDB.
    event_id : str
        `eventID` del record (idempotencia).

    Returns
    -------
    str
        `'processed'` si se replico una fila, `'skipped'` si el record
        no aplica (ya procesado, no-INSERT, imagen incompleta o tabla
        desconocida).

    Raises
    ------
    Exception
        Cualquier fallo de DB; el caller lo cuenta como fallido y
        `db_session()` hace rollback.
    """
    with db_session() as session:
        if is_event_processed(session, event_id):
            logger.debug(
                'event already processed',
                extra={'event_id': event_id},
            )
            return 'skipped'

        table = detect_table(record)
        if table == 'contacts':
            payload = parse_contact_record(record)
            if payload is None:
                return 'skipped'
            insert_contact(session, payload)
        elif table == 'tracking':
            payload = parse_tracking_record(record)
            if payload is None:
                return 'skipped'
            insert_tracking(session, payload)
        else:
            logger.warning(
                'unknown table in stream record',
                extra={
                    'event_source_arn': record.get('eventSourceARN', ''),
                },
            )
            return 'skipped'

        mark_event_processed(
            session,
            event_id,
            event_type=record.get('eventName', ''),
            table_name=table,
        )
        return 'processed'
