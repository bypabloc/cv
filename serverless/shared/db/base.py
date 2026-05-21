"""@module base — DeclarativeBase + mixins del schema unificado.

Todos los modelos del portfolio (las 37 tablas: datos del visitante +
contenido del CV) heredan de `Base`. `Base.metadata` es el target unico del
autogenerate de Alembic.

Convenciones:
- Naming convention explicita de constraints — Alembic genera nombres
  deterministas (necesario para `downgrade` reproducible).
- `UUIDPKMixin`: PK `uuid` con default server-side `uuidv7()` (PG18). Lo usan
  las tablas del CV. Las tablas del visitante (`contacts`, `tracking_events`)
  generan el UUID en la Lambda — declaran su PK sin server_default.
- `TimestampMixin`: `created_at` / `updated_at` con default `now()`.
"""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class Base(DeclarativeBase):
    """Base declarativa de las 37 tablas del portfolio."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPKMixin:
    """Mixin: PK `id uuid` con default server-side `uuidv7()` (PG18).

    Lo usan las tablas del CV. Las tablas del visitante NO lo usan: su `id`
    lo genera la Lambda (debe coincidir con el item de DynamoDB).
    """

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
