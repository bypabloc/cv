"""@module contact — tabla `contacts` (envios del formulario de contacto).

Replica en Neon de la tabla DynamoDB `ContactsTable`. El `stream_processor`
inserta una fila por cada envio del formulario que llega via DynamoDB Stream.

Fiel al schema actual (migraciones 001 + 010 + d4e5f6a7b8c9):
- PK `id` UUID generado por la Lambda (NO server-side `uuidv7()`): debe
  coincidir con el item de DynamoDB.
- `email` es `CITEXT` (case-insensitive, para matching de CRM) — requiere
  la extension `citext`.
- `service_type` / `status` se validan con CHECK inline (NO ENUM nativo):
  se conserva tal cual el schema de prod para parity.
- `session_id` FK a `sessions(session_id)` NOT NULL (spec
  sessions-normalize). Si llega un /contact sin session previa, el
  Lambda crea la session on-the-fly.
- Spec sessions-normalize dropeo `ip`, `country`, `user_agent` (todos
  movidos a sessions/session_visits via FK).
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base

_SERVICE_TYPES = ('consulting', 'fulltime', 'contract', 'other')
_STATUSES = ('new', 'contacted', 'qualified', 'converted', 'rejected')


class Contact(Base):
    """Un envio del formulario de contacto (replica de DynamoDB)."""

    __tablename__ = 'contacts'

    # UUIDv7 generado por la Lambda al insert.
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Campos del formulario.
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # CITEXT: matching de email case-insensitive para CRM.
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(Text)
    service_type: Mapped[str | None] = mapped_column(Text)
    budget: Mapped[str | None] = mapped_column(Text)
    timeline: Mapped[str | None] = mapped_column(Text)
    niche: Mapped[str | None] = mapped_column(Text)

    # Lifecycle / CRM (poblado manualmente por el owner).
    status: Mapped[str | None] = mapped_column(Text, server_default='new')
    notes: Mapped[str | None] = mapped_column(Text)

    # FK a sessions (spec sessions-normalize). Si el form se envia sin
    # /track previo, el Lambda crea la session on-the-fly antes del
    # INSERT del contact (decision 2). NOT NULL post-migration
    # d4e5f6a7b8c9 (los rows previos fueron TRUNCATEados).
    session_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('sessions.session_id'),
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
        # Indices de la migracion 002. Nombres explicitos (idx_*) para
        # parity exacto con el schema de prod.
        Index('idx_contacts_email', 'email'),
        Index('idx_contacts_created_at', text('created_at DESC')),
        Index(
            'idx_contacts_niche_created', 'niche', text('created_at DESC')
        ),
        # Partial index: solo los contactos en estados accionables del CRM.
        Index(
            'idx_contacts_status',
            'status',
            postgresql_where=text("status IN ('new', 'contacted')"),
        ),
        # Full-text search en el mensaje (diccionario espanol).
        Index(
            'idx_contacts_message_fts',
            text("to_tsvector('spanish', message)"),
            postgresql_using='gin',
        ),
        # Correlacion con sessions via session_id (spec sessions-normalize).
        # Ya no es partial WHERE NOT NULL — la columna es NOT NULL.
        Index('idx_contacts_session_id', 'session_id'),
    )
