"""@module contact — tabla `contacts` (envios del formulario de contacto).

Replica en Neon de la tabla DynamoDB `ContactsTable`. El `stream_processor`
inserta una fila por cada envio del formulario que llega via DynamoDB Stream.

Fiel al schema actual (migraciones 001 + 010):
- PK `id` UUID generado por la Lambda (NO server-side `uuidv7()`): debe
  coincidir con el item de DynamoDB.
- `email` es `CITEXT` (case-insensitive, para matching de CRM) — requiere
  la extension `citext`.
- `service_type` / `status` se validan con CHECK inline (NO ENUM nativo):
  se conserva tal cual el schema de prod para parity.
"""

from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import CITEXT, INET, UUID
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

    # Metadata de request (legacy: los contactos nuevos la dejan en NULL).
    # CHAR(2): codigo ISO de pais, ancho fijo (parity con el schema de prod).
    ip: Mapped[str | None] = mapped_column(INET)
    country: Mapped[str | None] = mapped_column(CHAR(2))
    user_agent: Mapped[str | None] = mapped_column(Text)

    # Lifecycle / CRM (poblado manualmente por el owner).
    status: Mapped[str | None] = mapped_column(Text, server_default='new')
    notes: Mapped[str | None] = mapped_column(Text)

    # Correlacion con el journey de tracking (cf_session). NO es FK:
    # tracking_events tiene TTL de 60 dias y un contacto puede sobrevivirlo.
    # El orden (ultima columna) replica el schema de prod (migracion 010
    # agrego session_id al final con ALTER TABLE).
    session_id: Mapped[str | None] = mapped_column(Text)

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
        # Correlacion con tracking_events via session_id (migracion 010).
        Index(
            'idx_contacts_session_id',
            'session_id',
            postgresql_where=text('session_id IS NOT NULL'),
        ),
    )
