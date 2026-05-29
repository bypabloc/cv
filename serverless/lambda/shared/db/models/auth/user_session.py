"""@module auth.user_session — tabla `auth_user_sessions` (sesiones activas)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class AuthUserSession(Base):
    """Sesion activa de un user, indexada por `family_id` del refresh JWT.

    El Lambda `auth` inserta un row por cada login (register/login verify)
    con el `family_id` (uuidv7) nuevo de la familia de refresh. Cada
    `session.refresh` actualiza `last_active_at` (la familia se mantiene en
    la rotation del refresh). El `session.logout` borra el row.

    `device_info` es un dict derivado del `user_agent` (browser/os/
    device_type). `family_id` es UNIQUE: 1 row por familia de refresh.

    Permite al user listar sus sesiones activas (`status.list-sessions`) y
    cerrar una individual (`status.revoke-session`), y al admin forzar el
    logout de todas las sesiones de un user (`admin.force-logout`).
    """

    __tablename__ = 'auth_user_sessions'

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text('uuidv7()'),
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('auth_users.id', ondelete='CASCADE'),
        nullable=False,
    )

    # 1 row por familia de refresh (uuidv7 generado en cada login).
    family_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False, unique=True,
    )

    device_info: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(), nullable=True,
    )
    ip: Mapped[str | None] = mapped_column(INET(), nullable=True)
    country: Mapped[str | None] = mapped_column(CHAR(2), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        Index(
            'ix_auth_user_sessions_user_active',
            'user_id',
            'last_active_at',
        ),
    )
