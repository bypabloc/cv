"""@module i18n.translation — tabla polimorfica `translations`."""

from sqlalchemy import PrimaryKeyConstraint, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin
from ...enums import entity_type_enum, locale_enum


class Translation(TimestampMixin, Base):
    """Un texto bilingue de una entidad, en un idioma.

    PK compuesta `(entity_type, entity_id, field, locale)`. `entity_id` es
    polimorfico (validado por trigger `assert_entity_exists`).
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
