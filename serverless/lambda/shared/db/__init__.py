"""@module shared.db — schema relacional unificado del portfolio.

Una sola base de datos PostgreSQL (Neon) con las 35 tablas: datos del
visitante (contacts, tracking_events, event_types, processed_stream_events)
+ contenido del CV (experiences, projects, translations, ...).

Una sola fuente de verdad: los modelos SQLAlchemy de `models/`. El schema se
versiona con Alembic (`alembic/`). Las Lambdas consumen el ORM via
`db_session()`.

Tambien actua como portador unico de SQLAlchemy: re-exporta el subset que
los services usan hoy (`select`, `func`, `pg_insert`, `Session`) para que
los `core/` de los services NO importen `from sqlalchemy` directo
(ver `.claude/rules/lambda-shared-imports.md`).

    from shared.db import Base, db_session, select, pg_insert, Session
    from shared.db.models import Contact, Experience
"""

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .base import Base, TimestampMixin, UUIDPKMixin
from .migrations import (
    build_config,
    current_revision,
    run_current,
    run_downgrade,
    run_migrate,
    run_show_migrations,
    run_stamp,
)
from .repository import (
    RepositoryError,
    ensure_session_and_visit,
    insert_contact,
    insert_tracking,
    list_tables,
)
from .session import db_session, get_engine

__all__ = [
    'Base',
    'RepositoryError',
    'Session',
    'TimestampMixin',
    'UUIDPKMixin',
    'build_config',
    'current_revision',
    'db_session',
    'delete',
    'ensure_session_and_visit',
    'func',
    'get_engine',
    'insert_contact',
    'insert_tracking',
    'list_tables',
    'pg_insert',
    'run_current',
    'run_downgrade',
    'run_migrate',
    'run_show_migrations',
    'run_stamp',
    'select',
]
