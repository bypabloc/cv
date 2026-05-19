"""@module pg_writer — escritura ORM de la replica Neon (DynamoDB Streams).

El `stream_processor` consume DynamoDB Streams y replica cada record en Neon.
Antes este modulo emitia SQL crudo via psycopg; ahora usa los modelos ORM de
`_shared/db/` — los modelos son la unica fuente de verdad del schema.

Patron de transaccion: el handler abre UNA `Session` por record (via
`db_session()`), inserta el contacto/evento + su fila de idempotencia, y el
context manager hace commit al salir limpio o rollback ante excepcion. Una
Session por record preserva el comportamiento del pipeline previo: un record
fallido no arrastra a los demas de la batch.

`Contact.id` viene del item de DynamoDB (lo genero la Lambda `contact_form`),
NO server-side — coincide con el item origen. `tracking_events` no tiene PK
fisica; la idempotencia la garantiza `processed_stream_events`.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from _shared.db.models import Contact, ProcessedStreamEvent, TrackingEvent


def is_event_processed(session: Session, event_id: str) -> bool:
    """`True` si el `event_id` ya esta en `processed_stream_events`."""
    stmt = select(ProcessedStreamEvent.event_id).where(
        ProcessedStreamEvent.event_id == event_id
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
        )
    )


def insert_contact(session: Session, payload: dict[str, Any]) -> None:
    """Inserta una fila en `contacts` desde el payload del transformer.

    `session_id` enlaza el contacto con `tracking_events` (correlacion via
    JOIN). `ip`/`country`/`user_agent` son columnas legacy: los contactos
    nuevos las reciben en NULL (el `contact_form` dejo de duplicarlas).
    """
    session.add(Contact(**payload))


def insert_tracking(session: Session, payload: dict[str, Any]) -> None:
    """Inserta una fila en `tracking_events` desde el payload del transformer.

    `event_props` es un dict plano: SQLAlchemy lo adapta a JSONB sin envoltura
    manual (a diferencia de psycopg crudo, que exigia `Jsonb(...)`).
    """
    session.add(TrackingEvent(**payload))
