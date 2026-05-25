"""@module visitor.contact — tabla `vis_contacts` (envios del formulario)."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base

_SERVICE_TYPES = ('consulting', 'fulltime', 'contract', 'other')
_STATUSES = ('new', 'contacted', 'qualified', 'converted', 'rejected')


class Contact(Base):
    """Un envio del formulario de contacto (replica de DynamoDB)."""

    __tablename__ = 'vis_contacts'

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(Text)
    service_type: Mapped[str | None] = mapped_column(Text)
    budget: Mapped[str | None] = mapped_column(Text)
    timeline: Mapped[str | None] = mapped_column(Text)
    niche: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str | None] = mapped_column(Text, server_default='new')
    notes: Mapped[str | None] = mapped_column(Text)

    session_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('vis_sessions.session_id'),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "service_type IS NULL OR service_type IN "
            f"({', '.join(repr(v) for v in _SERVICE_TYPES)})",
            name='service_type_valid',
        ),
        CheckConstraint(
            "status IN "
            f"({', '.join(repr(v) for v in _STATUSES)})",
            name='status_valid',
        ),
        Index('idx_vis_contacts_email', 'email'),
        Index('idx_vis_contacts_created_at', text('created_at DESC')),
        Index(
            'idx_vis_contacts_niche_created', 'niche', text('created_at DESC')
        ),
        Index(
            'idx_vis_contacts_status',
            'status',
            postgresql_where=text("status IN ('new', 'contacted')"),
        ),
        Index(
            'idx_vis_contacts_message_fts',
            text("to_tsvector('spanish', message)"),
            postgresql_using='gin',
        ),
        Index('idx_vis_contacts_session_id', 'session_id'),
    )
