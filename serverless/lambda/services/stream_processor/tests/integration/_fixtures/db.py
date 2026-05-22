"""Backend SQLite in-memory para los tests de integracion del Lambda.

Prefijo `_` en la carpeta para que pytest NO recolecte estos archivos
como tests.

El `stream_processor` escribe a Neon PostgreSQL via el ORM SQLAlchemy de
`shared.db`. Para correr los tests de integracion en CI sin un Neon real,
este modulo monta una base SQLite en memoria con las MISMAS tablas del
ORM (`contacts`, `tracking_events`, `processed_stream_events`,
`event_types`) y expone un context manager `db_session` con la misma
semantica que `shared.db.session.db_session` (commit al salir limpio,
rollback ante excepcion). El test parchea `stream_service.db_session`
con este reemplazo: asi se ejercita el flujo real
handler -> controller -> service -> ORM -> DB, sin Neon.

Estrategia de fidelidad (documentada en el conftest de integracion):
- Las tablas se crean a partir de los modelos SQLAlchemy reales, asi que
  columnas, tipos logicos y `NOT NULL` se respetan.
- 3 tipos PostgreSQL especificos (`CITEXT`, `INET`, `JSONB`) se degradan
  a `TEXT` en el dialecto SQLite via `@compiles`. `JSONB` mapeado a la
  columna ORM `JSONB` igual hace el roundtrip dict<->JSON (SQLAlchemy lo
  serializa). El resto de tipos (`UUID`, `CHAR`, `Text`, `Integer`,
  `DateTime`) degradan de forma nativa.
- Los indices con expresiones PostgreSQL (`to_tsvector`, `gin`, `brin`)
  y los `server_default` con funciones PG (`uuidv7()`) NO existen en
  SQLite: se omiten al copiar las tablas. El `server_default` `now()` SI
  se conserva (SQLite lo compila a `CURRENT_TIMESTAMP`), de modo que
  `created_at` / `received_at` se rellenan igual que en PostgreSQL.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from shared.db.models import (
    Contact,
    EventType,
    ProcessedStreamEvent,
    TrackingEvent,
)
from sqlalchemy import Engine, MetaData, Table, create_engine
from sqlalchemy.dialects.postgresql import CITEXT, INET, JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker

# Tablas que el stream_processor toca, en orden de dependencia
# (event_types antes de tracking_events por la FK event_type_id).
_TABLES = (EventType, Contact, TrackingEvent, ProcessedStreamEvent)

# --- Degradacion de tipos PostgreSQL al dialecto SQLite -------------------
# Sin estos overrides, SQLite no sabe compilar CITEXT/INET/JSONB y el
# CREATE TABLE falla. Se registran una sola vez al importar el modulo.


@compiles(CITEXT, 'sqlite')
def _compile_citext_sqlite(
    _element: object, _compiler: object, **_kw: object
) -> str:
    """`CITEXT` (email case-insensitive de PG) -> `TEXT` en SQLite."""
    return 'TEXT'


@compiles(INET, 'sqlite')
def _compile_inet_sqlite(
    _element: object, _compiler: object, **_kw: object
) -> str:
    """`INET` (direccion IP de PG) -> `TEXT` en SQLite."""
    return 'TEXT'


@compiles(JSONB, 'sqlite')
def _compile_jsonb_sqlite(
    _element: object, _compiler: object, **_kw: object
) -> str:
    """`JSONB` (event_props de PG) -> `TEXT` en SQLite.

    El tipo ORM sigue siendo `JSONB`, asi que SQLAlchemy serializa el
    dict a JSON al escribir y lo deserializa al leer (roundtrip exacto).
    """
    return 'TEXT'


def _portable_metadata() -> MetaData:
    """Copia las 4 tablas a un MetaData compatible con SQLite.

    Omite los indices (varios usan expresiones PG inexistentes en SQLite)
    y limpia los `server_default` que invocan funciones PG (`uuidv7()`).
    Conserva el `server_default` `now()` para que las columnas de
    timestamp se rellenen igual que en PostgreSQL.
    """
    metadata = MetaData()
    for model in _TABLES:
        source = model.__table__
        columns = []
        for column in source.columns:
            copied = column._copy()
            server_default = copied.server_default
            if server_default is not None:
                expression = str(getattr(server_default, 'arg', ''))
                if 'uuidv7' in expression:
                    copied.server_default = None
            columns.append(copied)
        Table(source.name, metadata, *columns)
    return metadata


def create_sqlite_engine() -> Engine:
    """Crea un engine SQLite in-memory con las 4 tablas del ORM."""
    engine = create_engine('sqlite:///:memory:')
    _portable_metadata().create_all(engine)
    return engine


def seed_processed_event(
    engine: Engine,
    event_id: str,
    *,
    event_type: str = 'INSERT',
    table_name: str = 'contacts',
) -> None:
    """Pre-puebla `processed_stream_events` con un `event_id` dado.

    Sirve para los tests de idempotencia: simula que un Stream record ya
    fue procesado en una invocacion anterior.
    """
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        session.add(
            ProcessedStreamEvent(
                event_id=event_id,
                event_type=event_type,
                table_name=table_name,
            ),
        )
        session.commit()
    finally:
        session.close()


def make_db_session(engine: Engine):
    """Devuelve un context manager `db_session` ligado al engine SQLite.

    Replica la semantica de `shared.db.session.db_session`: commit al
    salir sin error, rollback ante excepcion, close siempre. Es el objeto
    con el que el test parchea `stream_service.db_session`.
    """
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def db_session() -> Iterator[Session]:
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return db_session
