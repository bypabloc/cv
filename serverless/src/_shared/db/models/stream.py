"""@module stream — tabla `processed_stream_events` (idempotency log).

Cada record de DynamoDB Stream tiene un `eventID` unico. El
`stream_processor` verifica este `eventID` aqui ANTES de insertar en
`contacts` / `tracking_events` — es el mecanismo de idempotencia del
pipeline (sustituye al UNIQUE que `tracking_events`, al estar particionada,
no puede tener).

Fiel al schema actual (migracion 001). Sin TTL automatico: la tabla crece
con cada evento procesado; volumen bajo, cleanup manual si crece.
"""

from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ProcessedStreamEvent(Base):
    """Registro de un DynamoDB Stream event ya procesado (idempotencia)."""

    __tablename__ = 'processed_stream_events'

    event_id: Mapped[str] = mapped_column(Text, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # 'INSERT' | 'MODIFY' | 'REMOVE'
    event_type: Mapped[str | None] = mapped_column(Text)
    # 'contacts' | 'tracking'
    table_name: Mapped[str | None] = mapped_column(Text)
