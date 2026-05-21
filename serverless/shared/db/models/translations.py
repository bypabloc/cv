"""@module translations — tablas polimorficas: traducciones + priority.

Dos tablas genericas que aplican a cualquier entidad del CV via el par
(`entity_type`, `entity_id`):

- `translations`     — todos los textos bilingues del CV. 1 fila por
                       (entidad, campo, idioma). Reemplaza las columnas
                       `*_es`/`*_en`: escala a N idiomas sin ALTER TABLE.
- `niche_priorities` — el `priority` por (entidad, niche). Separado de las
                       uniones `<entidad>_niches` (decision del usuario).

Integridad polimorfica: `entity_id` NO tiene FK real (apunta a tablas
distintas segun `entity_type`). Se valida con un trigger creado en una
migracion Alembic posterior (`assert_entity_exists`). Esto es el trade-off
conocido del patron polimorfico — documentado en el plan, Decision 1.
"""

from sqlalchemy import ForeignKey, Integer, PrimaryKeyConstraint, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin
from ..enums import entity_type_enum, locale_enum


class Translation(TimestampMixin, Base):
    """Un texto bilingue de una entidad, en un idioma.

    Ejemplo: el `role` de una experiencia genera 2 filas — una `locale='es'`
    y otra `locale='en'`. PK compuesta `(entity_type, entity_id, field,
    locale)`: garantiza una sola traduccion por campo+idioma.

    `field` es el nombre logico del campo traducido (`role`, `summary`,
    `title`, `motivation`, `text`, `problem`, `process`, `result`, ...).
    """

    __tablename__ = 'translations'

    entity_type: Mapped[str] = mapped_column(entity_type_enum, nullable=False)
    entity_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    field: Mapped[str] = mapped_column(String(64), nullable=False)
    locale: Mapped[str] = mapped_column(locale_enum, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('entity_type', 'entity_id', 'field', 'locale'),
        {
            'comment': (
                'Textos bilingues del CV. entity_id es polimorfico — su '
                'integridad la valida el trigger assert_entity_exists.'
            )
        },
    )


class NichePriority(TimestampMixin, Base):
    """Priority de una entidad en un niche concreto.

    El priority del CV depende del par (entidad, niche): una experiencia
    puede tener priority 100 en fintech y 50 en generic. PK compuesta
    `(entity_type, entity_id, niche_id)`. `niche_id` SI tiene FK real (apunta
    siempre a `niches`); `entity_id` es polimorfico (mismo trigger que
    `translations`).

    Solo `experience` y `project` declaran priority en la data actual; la
    tabla lo soporta para cualquier entidad.
    """

    __tablename__ = 'niche_priorities'

    entity_type: Mapped[str] = mapped_column(entity_type_enum, nullable=False)
    entity_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    niche_id: Mapped[str] = mapped_column(
        ForeignKey('niches.id', ondelete='CASCADE'), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        PrimaryKeyConstraint('entity_type', 'entity_id', 'niche_id'),
        {
            'comment': (
                'Priority por (entidad, niche). entity_id es polimorfico — '
                'integridad via trigger assert_entity_exists.'
            )
        },
    )
