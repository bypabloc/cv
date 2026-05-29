"""@module auth.recovery_code — tabla `auth_mfa_recovery_codes`."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import BYTEA, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class AuthMfaRecoveryCode(Base):
    """Recovery code de MFA (bypass cuando se pierde TOTP/WebAuthn).

    10 codes por user, generados al setear MFA. `code_hash` es SHA-256
    del code (10 chars Crockford-like); el code en plain text se muestra
    UNA vez al user y NUNCA se persiste. `consumed_at IS NULL` = code
    activo. Tabla aparte (no JSONB en `auth_mfa_methods`) para auditar
    el consumo individual de cada code.
    """

    __tablename__ = 'auth_mfa_recovery_codes'

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

    code_hash: Mapped[bytes] = mapped_column(
        BYTEA(), nullable=False, unique=True,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            'code_hash', name='uq_auth_mfa_recovery_codes_code_hash',
        ),
        Index(
            'ix_auth_mfa_recovery_user_active', 'user_id', 'consumed_at',
        ),
    )
