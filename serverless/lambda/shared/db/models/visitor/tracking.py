"""@module visitor.tracking — tabla `tracking_events` (eventos del visitante)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class TrackingEvent(Base):
    """Un evento de tracking (replica de DynamoDB, particionada por mes)."""

    __tablename__ = 'tracking_events'

    session_id: Mapped[str] = mapped_column(
        Text, ForeignKey('sessions.session_id'), nullable=False
    )
    visit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('session_visits.visit_id'),
        nullable=False,
    )
    page_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    page_path: Mapped[str | None] = mapped_column(Text)

    viewport_width: Mapped[int | None] = mapped_column(Integer)
    viewport_height: Mapped[int | None] = mapped_column(Integer)

    niche: Mapped[str | None] = mapped_column(Text)

    event_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))
    event_type_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey('event_types.id')
    )
    event_props: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        Index('idx_tracking_session_created', 'session_id', 'created_at'),
        Index(
            'idx_tracking_created_brin',
            'created_at',
            postgresql_using='brin',
        ),
        Index('idx_tracking_page_path', 'page_path'),
        Index(
            'idx_tracking_niche_created',
            'niche',
            text('created_at DESC'),
            postgresql_where=text('niche IS NOT NULL'),
        ),
        Index('idx_tracking_event_type', 'event_type_id'),
        Index('idx_tracking_visit_id', 'visit_id'),
        {'postgresql_partition_by': 'RANGE (created_at)'},
    )

    __mapper_args__ = {  # noqa: RUF012
        'primary_key': [session_id, page_id, created_at],
    }
