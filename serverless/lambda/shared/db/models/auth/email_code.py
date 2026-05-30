"""@module auth.email_code — tabla `auth_email_codes` (codes de 8 chars)."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
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
from .enums import AuthCodeKind


class AuthEmailCode(Base):
    """Code de 8 chars enviado por email para verificar un flujo.

    `code_hash` es SHA-256 (32 bytes) del code generado — el code en
    plain text NO se guarda en la DB (defensa contra read access).

    `attempts` se incrementa en cada `verify.code` que NO coincide.
    Tras 5 fallos, el service `lock_user` cambia `auth_users.status` a
    `locked` (AC-11).

    `expires_at` es `now + 15 min` al insertar. La query de verify
    descarta expirados (`expires_at < now`).

    `consumed_at` se setea cuando el code se usa exitosamente. Despues
    del consumo el row NO se borra — sirve para auditoria.

    Indice compuesto `(user_id, kind, consumed_at)`: la query mas
    comun es "el ultimo code activo del user para este flujo" — esta
    forma cubre el filtro + sort.
    """

    __tablename__ = 'auth_email_codes'

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

    code_hash: Mapped[bytes] = mapped_column(BYTEA(), nullable=False)

    kind: Mapped[AuthCodeKind] = mapped_column(
        SAEnum(
            AuthCodeKind,
            name='auth_code_kind',
            create_type=False,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('0'),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            'ix_auth_email_codes_user_kind',
            'user_id',
            'kind',
            'consumed_at',
        ),
    )
