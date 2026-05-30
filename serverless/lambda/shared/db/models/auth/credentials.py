"""@module auth.credentials — tabla `auth_credentials` (password hashes)."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

import shared.db.models.auth.user  # noqa: F401 -- FK target (user)

from ...base import Base


class AuthCredentials(Base):
    """Credenciales (password hash) de un usuario.

    Relacion 1-to-0..1 con `auth_users` (PK = user_id, FK). Esta tabla
    NO existe para users que solo se autentican via magic-link o code
    — solo se popula cuando el user llama `verify.set-password`.

    `algo` es `'argon2id'` siempre por ahora. Existe la columna para
    futuras migraciones (ej. cambio a Argon2.next o derivacion).

    `password_hash` contiene el hash en formato argon2 completo
    (`$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>`) — incluye salt y
    parametros, asi que NO hace falta tabla aparte.
    """

    __tablename__ = 'auth_credentials'

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey('auth_users.id', ondelete='CASCADE'),
        primary_key=True,
    )

    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    algo: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'argon2id'"),
    )

    password_set_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_change_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
