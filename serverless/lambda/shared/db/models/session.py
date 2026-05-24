"""@module session — tabla `sessions` (identidad estable del visitante).

Una row por `session_id` (texto generado por el cliente en
localStorage). Datos del visitante que varian poco dentro del mismo
session: `user_agent`, `browser`, `browser_version`, `os`,
`device_type`. Son snapshot del PRIMER evento de la session (decision
1 del plan sessions-normalize) — solo `last_seen_at` se UPDATEa.

Fiel a la migration `d4e5f6a7b8c9`:
- PK natural `session_id` (TEXT).
- Sin particionado: cardinalidad << tracking_events.
- `tracking_events.session_id` y `contacts.session_id` la referencian
  por FK (NOT NULL en ambos, sin cascade).
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


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

    # Identidad relativamente estable del visitante (snapshot del primer
    # evento; decision 1: no se sobrescribe aunque cambie en eventos
    # subsiguientes).
    user_agent: Mapped[str | None] = mapped_column(Text)
    browser: Mapped[str | None] = mapped_column(Text)
    browser_version: Mapped[str | None] = mapped_column(Text)
    os: Mapped[str | None] = mapped_column(Text)
    device_type: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        # BRIN para first_seen_at: time-series, escritura ordenada.
        Index(
            'idx_sessions_first_seen_brin',
            'first_seen_at',
            postgresql_using='brin',
        ),
        # BTree DESC en last_seen_at para queries "visitantes activos".
        Index('idx_sessions_last_seen', text('last_seen_at DESC')),
    )
