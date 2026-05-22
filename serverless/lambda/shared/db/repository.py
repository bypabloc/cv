"""@module shared.db.repository — acceso a datos del schema PostgreSQL.

Concentra las operaciones de lectura/escritura ORM del portfolio que
antes vivian dispersas en el `core/` de los Lambdas:

- `list_tables`           — listado de tablas con estimado de filas.
- `is_event_processed`    — chequeo de idempotencia del stream.
- `mark_event_processed`  — registro de idempotencia del stream.
- `insert_contact` / `insert_tracking` — escritura ORM de los datos
  replicados desde DynamoDB Streams.

Esta logica vivia en `db/core/services/db_service.py` y
`stream_processor/core/services/stream_service.py`. Se movio aca porque
SQLAlchemy es responsabilidad de dominio de `shared.db`: el `core/` de
un Lambda NO importa `sqlalchemy` directo, solo consume estas funciones
(`from shared.db.repository import ...`).

Las funciones de transformacion de un Stream Record a kwargs del modelo
(parseo de la imagen type-tagged de DynamoDB) NO viven aca: NO usan
SQLAlchemy, son logica de negocio del `stream_processor` y se quedan en
su `core/services/`.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import Contact, ProcessedStreamEvent, TrackingEvent
from .session import get_engine


class RepositoryError(Exception):
    """Error de acceso a datos del schema PostgreSQL.

    El caller (un service del Lambda) lo captura y lo traduce a la
    respuesta normalizada del estandar lambda-controller.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int = 5000,
        error_code: str = 'DB_QUERY_FAILED',
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.error_code = error_code


# La query de listado de tablas: estimado de filas via las estadisticas
# del planner (`pg_stat_user_tables`), sin contar fila por fila.
_TABLES_QUERY = (
    "SELECT schemaname || '.' || relname AS table_name, "
    'n_live_tup AS estimated_rows '
    'FROM pg_stat_user_tables '
    'ORDER BY n_live_tup DESC'
)


def list_tables() -> dict[str, Any]:
    """Lista las tablas de la DB con un estimado de filas por tabla.

    Consulta `pg_stat_user_tables` (estadisticas del planner):
    `n_live_tup` es un estimado, NO un `COUNT(*)` exacto — barato y
    suficiente para una vista operativa.

    Returns
    -------
    dict[str, Any]
        `{'tables': [{'name': str, 'rows': int}, ...]}`, ordenado por
        `rows` descendente. Lista vacia si la DB no tiene tablas de
        usuario.

    Raises
    ------
    RepositoryError
        Si la query falla (DB inaccesible, schema sin migrar, etc.) con
        `code=5000` y `error_code='DB_QUERY_FAILED'`.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text(_TABLES_QUERY)).all()
    except Exception as exc:
        raise RepositoryError(
            f'No se pudo listar las tablas: {exc}',
        ) from exc

    tables = [
        {'name': row.table_name, 'rows': int(row.estimated_rows)}
        for row in rows
    ]
    return {'tables': tables}


def is_event_processed(session: Session, event_id: str) -> bool:
    """`True` si el `event_id` ya esta en `processed_stream_events`."""
    from sqlalchemy import select

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

    Se llama dentro de la misma `Session`/transaccion que el INSERT del
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
