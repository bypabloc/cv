"""@module shared.db — schema relacional unificado del portfolio.

Una sola base de datos PostgreSQL (Neon) con las 35 tablas: datos del
visitante (contacts, tracking_events, event_types, processed_stream_events)
+ contenido del CV (experiences, projects, translations, ...).

Una sola fuente de verdad: los modelos SQLAlchemy de `models/`. El schema se
versiona con Alembic (`alembic/`). Las Lambdas consumen el ORM via
`db_session()`.

    from shared.db import Base, db_session
    from shared.db.models import Contact, Experience
"""

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
    insert_contact,
    insert_tracking,
    is_event_processed,
    list_tables,
    mark_event_processed,
)
from .session import db_session, get_engine

__all__ = [
    'Base',
    'RepositoryError',
    'TimestampMixin',
    'UUIDPKMixin',
    'build_config',
    'current_revision',
    'db_session',
    'get_engine',
    'insert_contact',
    'insert_tracking',
    'is_event_processed',
    'list_tables',
    'mark_event_processed',
    'run_current',
    'run_downgrade',
    'run_migrate',
    'run_show_migrations',
    'run_stamp',
]
