"""@module auth.admin_action — tabla `auth_user_admin_actions` (audit admin)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
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

from ...base import Base


class AuthUserAdminAction(Base):
    """Audit inmutable de una accion administrativa sobre un user.

    Cada `admin.*` operation del Lambda `users` (disable, enable,
    force-logout, delete) inserta un row ANTES de la accion destructiva
    (audit pre-hoc). Tambien registra los intentos de acceso admin
    fallidos (`require_admin_user` con `success=false`).

    `admin_user_id` y `target_user_id` usan `ON DELETE SET NULL`: si el
    user borrado fue admin o target de una accion, el audit se conserva
    con la referencia en NULL (compliance, sin PII personal).

    `meta_data` (columna `metadata` en PG) lleva `{reason, ...}`. El attr
    Python es `meta_data` porque SQLAlchemy reserva `metadata` en la Base.
    """

    __tablename__ = 'auth_user_admin_actions'

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text('uuidv7()'),
    )

    admin_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('auth_users.id', ondelete='SET NULL'),
        nullable=True,
    )
    target_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('auth_users.id', ondelete='SET NULL'),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(String(64), nullable=False)

    meta_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(), name='metadata', nullable=True,
    )

    ip: Mapped[str | None] = mapped_column(INET(), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        Index(
            'ix_auth_admin_actions_target_ts',
            'target_user_id',
            'created_at',
        ),
    )
