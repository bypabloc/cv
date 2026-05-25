"""@module taxonomy.event_type — catalogo de tipos de eventos de tracking."""

from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class EventType(Base):
    """Catalogo de tipos de evento de tracking.

    Seed: 16 tipos. El frontend los replica como constantes TS en
    build-time. Por eso el `id` es un UUIDv7 literal fijo (sembrado).
    """

    __tablename__ = 'event_types'

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    code_name: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
