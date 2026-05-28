"""@module auth.magic_link — tabla `auth_magic_links` (URLs single-use)."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import BYTEA, INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base
from .enums import AuthLinkKind


class AuthMagicLink(Base):
    """Token opaco de magic-link (NO JWT).

    El token (32 bytes b64url) se envia en el email; en la DB se guarda
    SOLO el hash SHA-256 (`token_hash`, BYTEA UNIQUE) — el lookup es
    O(log n) por el indice unique.

    Single-use: tras consumir, `consumed_at = now()`. Re-clicks devuelven
    400 LINK_CONSUMED.

    `ip` + `user_agent` se guardan SOLO si el GET del magic-link los
    trae — sirven para auditoria (detectar uso fuera del rango esperado
    del user).
    """

    __tablename__ = 'auth_magic_links'

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

    token_hash: Mapped[bytes] = mapped_column(
        BYTEA(), nullable=False, unique=True,
    )

    kind: Mapped[AuthLinkKind] = mapped_column(
        SAEnum(
            AuthLinkKind,
            name='auth_link_kind',
            create_type=False,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    ip: Mapped[str | None] = mapped_column(INET(), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
