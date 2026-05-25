"""@module taxonomy.priority — tabla polimorfica `niche_priorities`."""

from sqlalchemy import (
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base, TimestampMixin
from ...enums import entity_type_enum


class NichePriority(TimestampMixin, Base):
    """Priority de una entidad en un niche concreto.

    PK compuesta `(entity_type, entity_id, niche_id)`. `niche_id` SI tiene
    FK real; `entity_id` es polimorfico (validado por trigger
    `assert_entity_exists`).
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
