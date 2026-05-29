"""@module auth.webauthn_credential — tabla `auth_webauthn_credentials`."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base


class AuthWebauthnCredential(Base):
    """Credential WebAuthn / Passkey registrado por un usuario.

    `credential_id` (UNIQUE) y `public_key` (CBOR bytes) los emite el
    authenticator durante el register ceremony. `sign_count` se valida
    monotonicamente creciente en cada login: si llega `<= stored`, es
    clone detection -> se rechaza y se marca `disabled_at=now()`
    (decision 14 / AC-15).

    `transports` (JSONB) = lista de transports reportados por el browser
    (`['internal']`, `['usb', 'nfc']`, ...). `aaguid` identifica el
    modelo del authenticator. `disabled_at IS NOT NULL` = deshabilitado
    (borrado logico o clone detection).
    """

    __tablename__ = 'auth_webauthn_credentials'

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

    credential_id: Mapped[bytes] = mapped_column(
        BYTEA(), nullable=False, unique=True,
    )
    public_key: Mapped[bytes] = mapped_column(BYTEA(), nullable=False)

    sign_count: Mapped[int] = mapped_column(
        Integer(), nullable=False, server_default=text('0'),
    )

    transports: Mapped[Any | None] = mapped_column(JSONB(), nullable=True)
    attestation_format: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
    )
    aaguid: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), nullable=True,
    )
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    disabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            'credential_id',
            name='uq_auth_webauthn_credentials_credential_id',
        ),
        Index(
            'ix_webauthn_credentials_user', 'user_id', 'disabled_at',
        ),
    )
