"""@module base — DeclarativeBase + mixins comunes del schema del CV.

Todos los modelos del CV heredan de `Base`. `Base.metadata` es el target
unico del autogenerate de Alembic (`alembic/env.py`).

Convenciones:
- PK `uuid` con default server-side `uuidv7()` (PostgreSQL 18 nativo:
  ordenable temporalmente, mejor localidad de indice que uuid v4).
- `TimestampMixin` agrega `created_at` / `updated_at` (`timestamptz`),
  ambos con default `now()` server-side.
- Naming convention explicita de constraints para que Alembic genere
  nombres deterministas (necesario para `downgrade` reproducible).
"""

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import MetaData
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


# Naming convention: Alembic genera nombres de constraint deterministas.
# Sin esto, los nombres autogenerados varian y `downgrade` puede fallar.
NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class Base(DeclarativeBase):
    """Base declarativa de todos los modelos del CV."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPKMixin:
    """Mixin: PK `id uuid` con default server-side `uuidv7()` (PG18)."""

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text('uuidv7()'),
    )


class TimestampMixin:
    """Mixin: columnas de auditoria `created_at` / `updated_at`."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
