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
from .session import db_session, get_engine

__all__ = [
    'Base',
    'TimestampMixin',
    'UUIDPKMixin',
    'db_session',
    'get_engine',
]
