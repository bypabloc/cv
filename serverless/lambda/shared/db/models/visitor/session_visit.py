"""@module visitor.session_visit — tabla `session_visits` (visits multi-touch)."""

from datetime import datetime

from sqlalchemy import (
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class SessionVisit(Base):
    """Una visita logica del visitante (cambio de network/utm)."""

    __tablename__ = 'session_visits'

    visit_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=func.uuidv7(),
    )
    session_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('sessions.session_id'),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    event_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text('0')
    )

    ip: Mapped[str | None] = mapped_column(INET)
    country: Mapped[str | None] = mapped_column(CHAR(2))

    utm_source: Mapped[str | None] = mapped_column(Text)
    utm_medium: Mapped[str | None] = mapped_column(Text)
    utm_campaign: Mapped[str | None] = mapped_column(Text)
    utm_content: Mapped[str | None] = mapped_column(Text)
    utm_term: Mapped[str | None] = mapped_column(Text)

    referrer: Mapped[str | None] = mapped_column(Text)
    landing_page_path: Mapped[str | None] = mapped_column(Text)
    niche: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index(
            'idx_visits_session_started',
            'session_id',
            text('started_at DESC'),
        ),
        Index(
            'idx_visits_started_brin',
            'started_at',
            postgresql_using='brin',
        ),
        Index(
            'idx_visits_country',
            'country',
            postgresql_where=text('country IS NOT NULL'),
        ),
        Index(
            'idx_visits_niche',
            'niche',
            postgresql_where=text('niche IS NOT NULL'),
        ),
        Index(
            'idx_visits_utm_source',
            'utm_source',
            postgresql_where=text('utm_source IS NOT NULL'),
        ),
    )
