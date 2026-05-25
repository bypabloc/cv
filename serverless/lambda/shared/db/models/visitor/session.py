"""@module visitor.session — tabla `sessions` (identidad estable del visitante)."""

from datetime import datetime

from sqlalchemy import DateTime, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class Session(Base):
    """Un visitante (1 row por session_id de localStorage)."""

    __tablename__ = 'sessions'

    session_id: Mapped[str] = mapped_column(Text, primary_key=True)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user_agent: Mapped[str | None] = mapped_column(Text)
    browser: Mapped[str | None] = mapped_column(Text)
    browser_version: Mapped[str | None] = mapped_column(Text)
    os: Mapped[str | None] = mapped_column(Text)
    device_type: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index(
            'idx_sessions_first_seen_brin',
            'first_seen_at',
            postgresql_using='brin',
        ),
        Index('idx_sessions_last_seen', text('last_seen_at DESC')),
    )
