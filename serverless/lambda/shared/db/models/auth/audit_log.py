"""@module auth.audit_log — tabla `auth_audit_log` (eventos de auditoria)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

import shared.db.models.auth.user  # noqa: F401 -- FK target (user)

from ...base import Base


class AuthAuditLog(Base):
    """Bitacora insert-only de eventos del dominio auth.

    Cada accion del Lambda `auth` (login.start, register.verify-code,
    session.refresh, ...) inserta un row aqui — exitoso (success=true)
    o fallido (success=false + error_code).

    `user_id` puede ser NULL: en `login.start` con email inexistente o
    en `register.start` antes de crear el row, no hay user todavia.

    `metadata` es JSONB libre para detalles no estructurados (ej.
    `{'jti': '...', 'family_id': '...'}` en session.refresh.reuse_detected).

    Indice `(user_id, event, created_at)` cubre las queries comunes:
    "lista de events de un user" y "ultimos eventos de un type".

    Retencion: insert-only. La estrategia de retencion / particionado
    se evaluara cuando el volumen lo justifique (no en este plan).
    """

    __tablename__ = 'auth_audit_log'

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text('uuidv7()'),
    )

    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('auth_users.id', ondelete='SET NULL'),
        nullable=True,
    )

    event: Mapped[str] = mapped_column(String(64), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    ip: Mapped[str | None] = mapped_column(INET(), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    niche: Mapped[str | None] = mapped_column(String(32), nullable=True)

    meta_data: Mapped[dict[str, Any] | None] = mapped_column(
        # En la DB la columna se llama `metadata` (no `meta_data`); SQLAlchemy
        # reserva `metadata` en la clase Base, asi que mapeamos al nombre
        # `meta_data` en Python pero la DDL la mantiene como `metadata`.
        JSONB(),
        name='metadata',
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            'ix_auth_audit_log_user_event_ts',
            'user_id',
            'event',
            'created_at',
        ),
    )
