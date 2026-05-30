"""@module visitor.tracking — tabla `vis_tracking_events` con PK fisica."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

import shared.db.models.taxonomy.event_type
import shared.db.models.visitor.session
import shared.db.models.visitor.session_visit  # noqa: F401 -- FK target (session_visit)

from ...base import Base


class TrackingEvent(Base):
    """Un evento de tracking (particionada por mes RANGE(created_at)).

    PK fisica `(created_at, visit_id, page_id)` post-rename — antes era
    ORM-only. PG18 soporta PK fisica que incluye la column de particion.
    """

    __tablename__ = 'vis_tracking_events'

    session_id: Mapped[str] = mapped_column(
        Text, ForeignKey('vis_sessions.session_id'), nullable=False
    )
    visit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('vis_session_visits.visit_id'),
        nullable=False,
    )
    page_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)

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
        UUID(as_uuid=False), ForeignKey('tax_event_types.id')
    )
    event_props: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        # PK fisica (created_at, visit_id, page_id). created_at incluido
        # por requerimiento de particionado RANGE.
        PrimaryKeyConstraint(
            'created_at',
            'visit_id',
            'page_id',
            name='pk_vis_tracking_events',
        ),
        Index('idx_vis_tracking_session_created', 'session_id', 'created_at'),
        Index(
            'idx_vis_tracking_created_brin',
            'created_at',
            postgresql_using='brin',
        ),
        Index('idx_vis_tracking_page_path', 'page_path'),
        Index(
            'idx_vis_tracking_niche_created',
            'niche',
            text('created_at DESC'),
            postgresql_where=text('niche IS NOT NULL'),
        ),
        Index('idx_vis_tracking_event_type', 'event_type_id'),
        Index('idx_vis_tracking_visit_id', 'visit_id'),
        {'postgresql_partition_by': 'RANGE (created_at)'},
    )
