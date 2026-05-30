"""@module auth.mfa_method — tabla `auth_mfa_methods` (TOTP + email_code MFA)."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import BYTEA, UUID
from sqlalchemy.orm import Mapped, mapped_column

import shared.db.models.auth.user  # noqa: F401 -- FK target (user)

from ...base import Base
from .enums import AuthMfaKind


class AuthMfaMethod(Base):
    """Metodo MFA activable por un usuario: `totp` o `email_code`.

    Un row por `(user_id, kind)` (UNIQUE). `confirmed_at IS NULL` =
    metodo pendiente de confirmar (TOTP recien generado, sin verificar
    el primer code). `disabled_at IS NOT NULL` = deshabilitado.

    Campos `totp_*` solo aplican a `kind=totp`; son NULL para
    `email_code`. `totp_secret_ciphertext` es la salida de `kms:Encrypt`
    con la CMK `alias/portfolio-lambdas` + `EncryptionContext={user_id,
    purpose:totp}` (CMK directa, SIN envelope encryption — decision 1 del
    plan 02). El secret en plain text NUNCA se persiste, NUNCA se loggea.

    `preferred` marca el metodo por defecto que el login propone primero.
    """

    __tablename__ = 'auth_mfa_methods'

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

    kind: Mapped[AuthMfaKind] = mapped_column(
        SAEnum(
            AuthMfaKind,
            name='auth_mfa_kind',
            create_type=False,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    preferred: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
        server_default=text('false'),
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    disabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --- TOTP-only (NULL para email_code) ---
    totp_secret_ciphertext: Mapped[bytes | None] = mapped_column(
        BYTEA(),
        nullable=True,
    )
    totp_algorithm: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        server_default=text("'SHA1'"),
    )
    totp_digits: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
        server_default=text('6'),
    )
    totp_period: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
        server_default=text('30'),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'kind', name='uq_auth_mfa_user_kind'),
        Index('ix_auth_mfa_methods_user', 'user_id'),
    )
